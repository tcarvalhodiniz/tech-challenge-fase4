"""
Embeddings e índices de busca da base de conhecimento.

Para cada documento da base é gerado um vetor com um modelo de embeddings que
roda localmente. Os vetores ficam em um índice FAISS gravado em data/indice. O
índice da busca por palavras (BM25) é montado em memória na carga, a partir dos
mesmos documentos, porque leva menos de um segundo.

A posição de um documento nos dois índices é a mesma linha dele na base de
conhecimento. Por isso o manifesto guarda uma assinatura da base: se a base
mudar, o índice precisa ser gerado de novo.
"""

import hashlib
import json
import os
import time

import faiss
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from config import settings
from src.preparacao.base_conhecimento import carregar_base
from src.preparacao.texto import normalizar, sem_acentos, tokens

PASTA = settings.PATHS["indice"]
ARQ_VETORIAL = os.path.join(PASTA, "vetorial.faiss")
ARQ_MANIFESTO = os.path.join(PASTA, "manifesto.json")
CAMINHO_RESUMO = os.path.join(settings.PATHS["reports"], "indexacao.json")

# Muda quando a forma de gerar os vetores muda, para um índice antigo não ser reaproveitado.
VERSAO_DO_INDICE = 2

# Palavras muito frequentes, que não ajudam a diferenciar um comentário do outro
# na busca por palavras. Estão sem acento porque a comparação é feita sem acento.
# "nao" fica fora da lista: "não recebi" e "recebi" têm sentidos opostos.
PALAVRAS_VAZIAS = set(
    "a o e de do da dos das um uma em no na nos nas para por com que os as ao aos "
    "se foi ser eu me meu minha".split()
)

# Consultas usadas só para conferir se os índices respondem como esperado. Foram
# escritas com palavras diferentes das que os clientes costumam usar, para a
# busca por significado não acertar só por coincidência de palavras.
CONSULTAS_DE_TESTE = [
    "problemas com a entrega do pedido",
    "produto chegou com defeito",
    "cliente não recebeu o que comprou",
    "entrega mais rápida que o esperado",
    "vendedor não respondeu às mensagens",
]


def tokenizar(texto: str) -> list[str]:
    """Palavras em minúsculas e sem acento, para a busca por palavras.

    Os clientes escrevem a mesma palavra com e sem acento ("ótimo" e "otimo",
    "não" e "nao"). Sem tirar o acento, a busca trataria as duas como palavras
    diferentes.
    """
    return [t for t in tokens(sem_acentos(texto)) if t not in PALAVRAS_VAZIAS]


def carregar_modelo() -> SentenceTransformer:
    return SentenceTransformer(settings.MODELO_EMBEDDINGS)


def em_caixa_alta(texto: str) -> bool:
    letras = [c for c in texto if c.isalpha()]
    return len(letras) >= 10 and sum(c.isupper() for c in letras) >= 0.7 * len(letras)


def texto_para_vetor(texto: str) -> str:
    """Texto usado só para calcular o vetor. O texto mostrado ao usuário não muda.

    O modelo de embeddings diferencia maiúsculas de minúsculas, e um comentário
    todo em maiúsculas fica com um vetor distante do mesmo comentário em
    minúsculas (similaridade mediana de 0,49). Esses comentários quase não eram
    encontrados pela busca por significado, por isso são convertidos.
    """
    return texto.lower() if em_caixa_alta(texto) else texto


def gerar_embeddings(textos, modelo: SentenceTransformer) -> np.ndarray:
    """Um vetor por texto. Os vetores saem normalizados, então o produto interno
    entre dois deles é a similaridade de cosseno."""
    return modelo.encode(
        [texto_para_vetor(t) for t in textos], batch_size=128, normalize_embeddings=True,
        convert_to_numpy=True, show_progress_bar=False,
    ).astype("float32")


def assinatura(base: pd.DataFrame) -> str:
    """Resumo da base (ids e textos, na ordem). Muda se qualquer documento mudar."""
    h = hashlib.sha256()
    for review_id, texto in zip(base["review_id"], base["texto"]):
        h.update(review_id.encode())
        h.update(texto.encode())
    return h.hexdigest()


def construir() -> dict:
    """Gera os embeddings, grava o índice vetorial e devolve o manifesto."""
    base = carregar_base()
    modelo = carregar_modelo()

    inicio = time.perf_counter()
    vetores = gerar_embeddings(base["texto"], modelo)
    segundos = time.perf_counter() - inicio

    # Busca exata. Com dezenas de milhares de vetores ela leva milissegundos, e
    # um índice aproximado só traria risco de deixar de fora um documento relevante.
    indice = faiss.IndexFlatIP(vetores.shape[1])
    indice.add(vetores)

    os.makedirs(PASTA, exist_ok=True)
    faiss.write_index(indice, ARQ_VETORIAL)
    manifesto = {
        "versao": VERSAO_DO_INDICE,
        "modelo": settings.MODELO_EMBEDDINGS,
        "dispositivo": str(modelo.device),
        "documentos": int(indice.ntotal),
        "dimensao": int(vetores.shape[1]),
        "segundos_para_gerar_embeddings": round(segundos, 1),
        "tamanho_do_indice_mb": round(os.path.getsize(ARQ_VETORIAL) / 1e6, 1),
        "assinatura_da_base": assinatura(base),
    }
    with open(ARQ_MANIFESTO, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)
    return manifesto


class Indice:
    """Índices carregados em memória, com as duas buscas básicas.

    As duas buscas devolvem uma lista de (posição, pontuação), em que a posição
    é a linha do documento em `self.documentos`.
    """

    def __init__(self):
        if not os.path.exists(ARQ_MANIFESTO):
            construir()
        with open(ARQ_MANIFESTO, encoding="utf-8") as f:
            self.manifesto = json.load(f)

        self.documentos = carregar_base()
        if self.manifesto.get("versao") != VERSAO_DO_INDICE:
            raise SystemExit("O índice foi gerado por uma versão anterior do código. Rode: python -m src.indexacao.indice")
        if self.manifesto["modelo"] != settings.MODELO_EMBEDDINGS:
            raise SystemExit("O índice foi gerado com outro modelo. Rode: python -m src.indexacao.indice")
        if self.manifesto["assinatura_da_base"] != assinatura(self.documentos):
            raise SystemExit("A base mudou depois que o índice foi gerado. Rode: python -m src.indexacao.indice")

        self.vetorial = faiss.read_index(ARQ_VETORIAL)
        self.lexical = BM25Okapi([tokenizar(t) for t in self.documentos["texto"]])
        self.modelo = carregar_modelo()

        # Documentos com o mesmo texto (avaliações de clientes diferentes). Cada
        # grupo é representado pelo primeiro documento, e `iguais` guarda todos.
        chaves = self.documentos["texto"].map(normalizar)
        self.iguais = {int(p[0]): p for p in self.documentos.groupby(chaves.to_numpy(), sort=False).indices.values()}
        self.representante = np.empty(len(self.documentos), dtype=np.int64)
        for primeiro, posicoes in self.iguais.items():
            self.representante[posicoes] = primeiro

    def embutir(self, textos) -> np.ndarray:
        return gerar_embeddings(textos, self.modelo)

    def buscar_vetorial(self, consulta, k: int = 10, distintos: bool = False) -> list[tuple[int, float]]:
        """Documentos mais parecidos em significado. A pontuação é a similaridade de cosseno.

        `consulta` pode ser um texto ou um vetor já calculado.
        """
        vetor = consulta if isinstance(consulta, np.ndarray) else self.embutir([consulta])
        pontos, posicoes = self.vetorial.search(vetor.reshape(1, -1), settings.K_BRUTO if distintos else k)
        itens = [(int(p), float(s)) for p, s in zip(posicoes[0], pontos[0])]
        return self._distintos(itens, k) if distintos else itens

    def buscar_lexical(self, consulta: str, k: int = 10, distintos: bool = False) -> list[tuple[int, float]]:
        """Documentos que compartilham palavras com a consulta. A pontuação é a do BM25."""
        pontos = self.lexical.get_scores(tokenizar(consulta))
        melhores = np.argsort(-pontos)[: settings.K_BRUTO if distintos else k]
        itens = [(int(p), float(pontos[p])) for p in melhores if pontos[p] > 0]
        return self._distintos(itens, k) if distintos else itens

    def _distintos(self, itens: list[tuple[int, float]], k: int) -> list[tuple[int, float]]:
        """Mantém um documento por texto, na ordem em que aparecem, até completar k."""
        vistos, saida = set(), []
        for posicao, pontos in itens:
            primeiro = int(self.representante[posicao])
            if primeiro not in vistos:
                vistos.add(primeiro)
                saida.append((primeiro, pontos))
                if len(saida) == k:
                    break
        return saida

    def vetor(self, posicao: int) -> np.ndarray:
        return self.vetorial.reconstruct(posicao)

    def parecidas_na_base(self, posicao: int) -> list[int]:
        """Posições de todos os documentos da base que dizem o mesmo que o documento
        informado (similaridade a partir de SIMILARIDADE_TEXTO_PARECIDO). Inclui ele mesmo."""
        _, _, posicoes = self.vetorial.range_search(
            self.vetor(posicao).reshape(1, -1), settings.SIMILARIDADE_TEXTO_PARECIDO)
        return sorted(int(p) for p in posicoes)

    def similaridade(self, vetores: np.ndarray, posicao: int) -> float:
        """Maior similaridade de cosseno entre o documento e os vetores informados."""
        return float(np.max(vetores @ self.vetor(posicao)))

    def texto(self, posicao: int) -> str:
        return self.documentos["texto"].iat[posicao]

    def review_id(self, posicao: int) -> str:
        return self.documentos["review_id"].iat[posicao]


def conferir(indice: Indice, k: int = 3) -> dict:
    """Roda as consultas de teste nas duas buscas e mede o tempo de cada uma."""
    resultado = {"consultas": {}, "ms_por_busca": {}}
    tempos = {"vetorial": [], "lexical": []}
    for consulta in CONSULTAS_DE_TESTE:
        achados = {}
        for nome, buscar in (("vetorial", indice.buscar_vetorial), ("lexical", indice.buscar_lexical)):
            inicio = time.perf_counter()
            itens = buscar(consulta, k)
            tempos[nome].append((time.perf_counter() - inicio) * 1000)
            achados[nome] = [{"pontuacao": round(p, 3), "texto": indice.texto(pos)} for pos, p in itens]
        resultado["consultas"][consulta] = achados
    # A primeira busca vetorial inclui o aquecimento do modelo; a mediana ignora isso.
    resultado["ms_por_busca"] = {nome: round(float(np.median(t)), 1) for nome, t in tempos.items()}
    return resultado


def executar() -> dict:
    manifesto = construir()
    inicio = time.perf_counter()
    indice = Indice()
    carga = time.perf_counter() - inicio
    resumo = {"indice": manifesto, "segundos_para_carregar": round(carga, 1), **conferir(indice)}
    os.makedirs(settings.PATHS["reports"], exist_ok=True)
    with open(CAMINHO_RESUMO, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    return resumo


if __name__ == "__main__":
    r = executar()
    print(json.dumps({k: v for k, v in r.items() if k != "consultas"}, ensure_ascii=False, indent=2))
    for consulta, achados in r["consultas"].items():
        print(f"\n{consulta}")
        for nome, itens in achados.items():
            for item in itens:
                print(f"  {nome:8s} {item['pontuacao']:7.3f}  {item['texto'][:90]}")
