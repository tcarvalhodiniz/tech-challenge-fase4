"""
Recuperação das avaliações mais relevantes para uma pergunta.

Etapas:
1. Transformação: a pergunta vira frases de busca (transformacao.py).
2. Busca: a pergunta original e as frases são procuradas no índice de
   significado. As frases também são procuradas no índice de palavras.
3. Fusão: os rankings são combinados com RRF (Reciprocal Rank Fusion). Uma
   avaliação bem colocada em vários rankings sobe na lista final.
4. Seleção: ficam as avaliações mais bem colocadas. Textos que dizem a mesma
   coisa contam como uma evidência só. Cada evidência guarda quantas
   avaliações da base inteira dizem o mesmo que ela.

A busca por palavras não usa a pergunta original. As palavras de uma pergunta
("quais", "frequência", "clientes") não são as palavras de um comentário, e essa
busca trazia textos sem relação com o assunto, como "Compro com frequência".

O resultado guarda o que aconteceu em cada etapa, para ser possível mostrar
como cada evidência foi encontrada.

Uso:  python -m src.recuperacao.recuperador "Quais os problemas com a entrega?"
"""

from dataclasses import dataclass, field

from config import settings
from src.indexacao.indice import Indice
from src.recuperacao.transformacao import gerar_frases


@dataclass
class Evidencia:
    posicao: int              # linha do documento na base de conhecimento
    review_id: str
    texto: str
    pontuacao: float          # soma do RRF nos rankings em que apareceu
    similaridade: float       # maior similaridade de cosseno com a pergunta ou com as frases de busca
    review_ids: list[str]     # avaliações da base com exatamente esse texto
    rankings: list[str]       # em quais rankings ela apareceu
    parecidas: list[dict] = field(default_factory=list)   # candidatos da busca que dizem a mesma coisa
    posicoes_na_base: list[int] = field(default_factory=list)   # todos os documentos da base que dizem a mesma coisa

    @property
    def avaliacoes_na_base(self) -> int:
        """Quantas avaliações da base inteira dizem a mesma coisa que esta evidência."""
        return len(self.posicoes_na_base)


@dataclass
class Recuperacao:
    pergunta: str
    frases: list[str]                                              # etapa 1
    rankings: dict[str, list[int]] = field(default_factory=dict)   # etapa 2: posições por ranking
    evidencias: list[Evidencia] = field(default_factory=list)      # etapas 3 e 4


def rrf(rankings: dict[str, list[int]], k: int = settings.RRF_K) -> list[tuple[int, float]]:
    """Combina vários rankings. Cada posição soma 1 / (k + colocação) em cada ranking em que aparece."""
    pontos: dict[int, float] = {}
    for posicoes in rankings.values():
        for colocacao, posicao in enumerate(posicoes, start=1):
            pontos[posicao] = pontos.get(posicao, 0.0) + 1.0 / (k + colocacao)
    return sorted(pontos.items(), key=lambda item: -item[1])


class Recuperador:
    def __init__(self, indice: Indice | None = None):
        self.indice = indice or Indice()

    def recuperar(self, pergunta: str, n: int = settings.EVIDENCIAS, transformar: bool = True,
                  palavras_na_pergunta: bool = False, juntar_parecidas: bool = True) -> Recuperacao:
        """Os três últimos parâmetros existem para comparar configurações da busca.
        Os valores padrão são a configuração do projeto."""
        indice = self.indice

        # 1. Transformação da pergunta
        frases = gerar_frases(pergunta) if transformar else []
        consultas = [pergunta] + frases
        vetores = indice.embutir(consultas)

        # 2. Busca, já com um documento por texto
        resultado = Recuperacao(pergunta=pergunta, frases=frases)
        for consulta, vetor in zip(consultas, vetores):
            achados = indice.buscar_vetorial(vetor, settings.K_POR_BUSCA, distintos=True)
            resultado.rankings[f"significado | {consulta}"] = [p for p, _ in achados]
            if consulta != pergunta or palavras_na_pergunta:
                achados = indice.buscar_lexical(consulta, settings.K_POR_BUSCA, distintos=True)
                resultado.rankings[f"palavras | {consulta}"] = [p for p, _ in achados]

        # 3. Fusão
        fundido = rrf(resultado.rankings)

        # 4. Seleção. Um candidato quase igual a uma evidência já escolhida é
        #    guardado como "parecida" dela, em vez de ocupar outra vaga.
        vetores_escolhidos = []
        for posicao, pontuacao in fundido:
            vetor = indice.vetor(posicao)
            ids = [indice.review_id(int(p)) for p in indice.iguais[posicao]]
            if juntar_parecidas:
                parecida_com = next((e for e, v in zip(resultado.evidencias, vetores_escolhidos)
                                     if float(v @ vetor) >= settings.SIMILARIDADE_TEXTO_PARECIDO), None)
                if parecida_com is not None:
                    parecida_com.parecidas.append({"texto": indice.texto(posicao), "review_ids": ids})
                    continue
            if len(resultado.evidencias) < n:
                resultado.evidencias.append(Evidencia(
                    posicao=posicao,
                    review_id=indice.review_id(posicao),
                    texto=indice.texto(posicao),
                    pontuacao=round(pontuacao, 4),
                    similaridade=round(indice.similaridade(vetores, posicao), 3),
                    review_ids=ids,
                    rankings=[nome for nome, posicoes in resultado.rankings.items() if posicao in posicoes],
                    posicoes_na_base=indice.parecidas_na_base(posicao),
                ))
                vetores_escolhidos.append(vetor)
        return resultado


def mostrar(r: Recuperacao, indice: Indice, por_ranking: int = 3) -> None:
    """Imprime o que aconteceu em cada etapa."""
    print(f"PERGUNTA\n  {r.pergunta}")

    print("\n1. TRANSFORMAÇÃO: frases de busca")
    for frase in r.frases or ["(nenhuma: busca só com a pergunta original)"]:
        print(f"  - {frase}")

    print(f"\n2. BUSCA: {len(r.rankings)} rankings, até {settings.K_POR_BUSCA} resultados em cada")
    for nome, posicoes in r.rankings.items():
        print(f"  {nome}")
        for posicao in posicoes[:por_ranking]:
            print(f"      {indice.texto(posicao)[:90]}")

    print(f"\n3 e 4. FUSÃO E SELEÇÃO: {len(r.evidencias)} evidências")
    for i, e in enumerate(r.evidencias, start=1):
        total = f"  [{e.avaliacoes_na_base} avaliações da base dizem isso]" if e.avaliacoes_na_base > 1 else ""
        print(f"  [{i}] rrf={e.pontuacao:.4f} sim={e.similaridade:.2f} em {len(e.rankings)} rankings{total}")
        print(f"      {e.texto[:110]}")
        for p in e.parecidas[:2]:
            print(f"        parecida: {p['texto'][:90]}")
        print(f"      review_id {e.review_id}")


if __name__ == "__main__":
    import sys

    pergunta = " ".join(sys.argv[1:]) or "Quais os problemas com a entrega?"
    recuperador = Recuperador()
    mostrar(recuperador.recuperar(pergunta), recuperador.indice)
