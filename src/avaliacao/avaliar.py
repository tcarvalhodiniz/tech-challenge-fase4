"""
Avaliação da solução.

Roda seis medições com perguntas que não foram usadas nos passos anteriores e
compara o resultado com os critérios de config/settings.py.

    1. Precisão das evidências   as evidências recuperadas tratam do assunto da pergunta?
    2. Fidelidade                as conclusões estão apoiadas nas evidências citadas?
    3. Recusa                    perguntas sem resposta são recusadas? As respondíveis são respondidas?
    4. Elogios genéricos         a busca piora se os elogios genéricos voltarem para a base?
    5. Temas                     os temas de reclamação mais comuns aparecem nas respostas amplas?
    6. Tempo                     quanto demora cada etapa?

Com a variável MODELO_COMPARADO, mede também a precisão da busca com outro modelo
de embeddings.

Não há medida de recall por documento. Nesta base muitas avaliações dizem a mesma
coisa, então não existe uma única avaliação correta para cada pergunta.

Uso:  python -m src.avaliacao.avaliar
      MODELO_COMPARADO=<modelo> python -m src.avaliacao.avaliar
"""

import json
import os
import re
import time

import numpy as np

from config import settings
from src.avaliacao import juiz
from src.avaliacao.perguntas import (AMPLAS_SOBRE_PROBLEMAS, ELOGIOS, FORA_DO_ESCOPO, RESPONDIVEIS,
                                     SEM_EVIDENCIA)
from src.geracao.responder import RECUSADA, Respondedor, gerar
from src.indexacao.indice import gerar_embeddings
from src.preparacao.carga import carregar_avaliacoes
from src.preparacao.exploracao import TEMAS
from src.preparacao.texto import eh_generico, montar_texto, normalizar
from src.recuperacao.transformacao import gerar_frases

CAMINHO_RESUMO = os.path.join(settings.PATHS["reports"], "avaliacao.json")
MODELO_COMPARADO = os.getenv("MODELO_COMPARADO", "")


def taxa(parte: int, total: int) -> float:
    return round(parte / total, 3) if total else 0.0


# ---------------------------------------------------------------------------
# 1. Precisão das evidências
# ---------------------------------------------------------------------------

def medir_precisao(recuperador) -> tuple[dict, dict]:
    """Parcela das evidências julgadas relevantes, na busca simples e na configuração do projeto."""
    configuracoes = {"busca simples": {"transformar": False}, "configuração do projeto": {}}
    resultado = {nome: {"relevantes": 0, "evidencias": 0, "por_pergunta": []} for nome in configuracoes}
    relevancia_no_projeto = {}

    for pergunta in RESPONDIVEIS:
        for nome, opcoes in configuracoes.items():
            evidencias = recuperador.recuperar(pergunta, **opcoes).evidencias
            relevantes = juiz.julgar_relevancia(pergunta, [e.texto for e in evidencias])
            resultado[nome]["relevantes"] += sum(relevantes)
            resultado[nome]["evidencias"] += len(relevantes)
            resultado[nome]["por_pergunta"].append(
                {"pergunta": pergunta, "relevantes": sum(relevantes), "evidencias": len(relevantes)})
            if not opcoes:
                relevancia_no_projeto[pergunta] = relevantes

    for dados in resultado.values():
        dados["precisao"] = taxa(dados["relevantes"], dados["evidencias"])
    return resultado, relevancia_no_projeto


# ---------------------------------------------------------------------------
# 2. Fidelidade
# ---------------------------------------------------------------------------

def medir_fidelidade(respondedor, relevancia_no_projeto: dict) -> tuple[dict, list]:
    """Conclusões sustentadas pelas evidências citadas, e uso das evidências relevantes."""
    respostas, detalhes = [], []
    conclusoes = sustentadas = relevantes = relevantes_citadas = fora_do_assunto = fora_do_assunto_citadas = 0

    for pergunta in RESPONDIVEIS:
        r = respondedor.responder(pergunta)
        respostas.append(r)
        if not r.pontos:
            continue
        pares = [(p.conclusao, [r.evidencias[n - 1].texto for n in p.evidencias]) for p in r.pontos]
        decisoes = juiz.julgar_sustentacao(pares)
        conclusoes += len(decisoes)
        sustentadas += sum(decisoes)
        for (conclusao, citadas), ok in zip(pares, decisoes):
            if not ok:
                detalhes.append({"pergunta": pergunta, "conclusao": conclusao, "citadas": citadas})
        marcadas = relevancia_no_projeto[pergunta]
        relevantes += sum(marcadas)
        relevantes_citadas += sum(1 for n, ok in enumerate(marcadas, start=1) if ok and n in r.citadas)
        fora_do_assunto += sum(1 for ok in marcadas if not ok)
        fora_do_assunto_citadas += sum(1 for n, ok in enumerate(marcadas, start=1) if not ok and n in r.citadas)

    resultado = {
        "conclusoes": conclusoes,
        "sustentadas": sustentadas,
        "fidelidade": taxa(sustentadas, conclusoes),
        "evidencias_relevantes": relevantes,
        "evidencias_relevantes_citadas": relevantes_citadas,
        "uso_das_evidencias_relevantes": taxa(relevantes_citadas, relevantes),
        "evidencias_fora_do_assunto": fora_do_assunto,
        "evidencias_fora_do_assunto_citadas": fora_do_assunto_citadas,
        "conclusoes_nao_sustentadas": detalhes,
    }
    return resultado, respostas


# ---------------------------------------------------------------------------
# 3. Recusa
# ---------------------------------------------------------------------------

def medir_recusa(respondedor, respostas_respondiveis: list) -> dict:
    grupos = {"fora do escopo": FORA_DO_ESCOPO, "sem evidência": SEM_EVIDENCIA}
    resultado = {"por_grupo": {}, "nao_recusadas": []}
    recusadas = total = sem_modelo = 0

    for grupo, perguntas in grupos.items():
        n = 0
        for pergunta in perguntas:
            r = respondedor.responder(pergunta)
            total += 1
            if r.situacao == RECUSADA:
                n += 1
                sem_modelo += r.similaridade_da_pergunta < settings.SIMILARIDADE_MINIMA_DA_PERGUNTA
            else:
                resultado["nao_recusadas"].append(
                    {"grupo": grupo, "pergunta": pergunta, "situacao": r.situacao,
                     "conclusoes": [p.conclusao for p in r.pontos], "avisos": r.avisos})
        recusadas += n
        resultado["por_grupo"][grupo] = {"perguntas": len(perguntas), "recusadas": n}

    indevidas = [r.pergunta for r in respostas_respondiveis if r.situacao == RECUSADA]
    situacoes = {}
    for r in respostas_respondiveis:
        situacoes[r.situacao] = situacoes.get(r.situacao, 0) + 1
    resultado.update({
        "perguntas_sem_resposta": total,
        "recusadas": recusadas,
        "recusa_correta": taxa(recusadas, total),
        "recusadas_sem_chamar_o_modelo": sem_modelo,
        "perguntas_respondiveis": len(respostas_respondiveis),
        "situacao_das_respondiveis": situacoes,
        "recusadas_por_engano": indevidas,
        "recusa_indevida": taxa(len(indevidas), len(respostas_respondiveis)),
    })
    return resultado


# ---------------------------------------------------------------------------
# Comparação de modelos de embeddings (opcional)
# ---------------------------------------------------------------------------

def medir_outro_modelo(indice) -> dict:
    """Precisão da busca por significado, com a pergunta original, no modelo do
    projeto e em outro modelo. Os vetores do outro modelo são calculados em
    memória, sem mexer no índice do projeto."""
    from sentence_transformers import SentenceTransformer

    outro = SentenceTransformer(MODELO_COMPARADO)
    inicio = time.perf_counter()
    vetores = gerar_embeddings(indice.documentos["texto"], outro)
    segundos = time.perf_counter() - inicio

    relevantes = {"modelo do projeto": 0, "outro modelo": 0}
    for pergunta in RESPONDIVEIS:
        do_projeto = [indice.texto(p) for p, _ in indice.buscar_vetorial(pergunta, 10, distintos=True)]

        pontos = vetores @ gerar_embeddings([pergunta], outro)[0]
        do_outro, vistos = [], set()
        for p in np.argsort(-pontos)[: settings.K_BRUTO]:
            primeiro = int(indice.representante[p])
            if primeiro not in vistos:
                vistos.add(primeiro)
                do_outro.append(indice.texto(primeiro))
            if len(do_outro) == 10:
                break

        relevantes["modelo do projeto"] += sum(juiz.julgar_relevancia(pergunta, do_projeto))
        relevantes["outro modelo"] += sum(juiz.julgar_relevancia(pergunta, do_outro))

    evidencias = 10 * len(RESPONDIVEIS)
    return {
        "modelo_do_projeto": settings.MODELO_EMBEDDINGS,
        "outro_modelo": MODELO_COMPARADO,
        "dimensao_do_outro_modelo": int(vetores.shape[1]),
        "segundos_para_gerar_embeddings_do_outro_modelo": round(segundos, 1),
        "evidencias": evidencias,
        "precisao_do_modelo_do_projeto": taxa(relevantes["modelo do projeto"], evidencias),
        "precisao_do_outro_modelo": taxa(relevantes["outro modelo"], evidencias),
    }


# ---------------------------------------------------------------------------
# 4. Elogios genéricos
# ---------------------------------------------------------------------------

def medir_elogios_genericos(indice) -> dict:
    """Compara a busca simples na base do projeto e na base com os elogios genéricos de volta."""
    bruto = carregar_avaliacoes().drop_duplicates("review_id")
    textos = [montar_texto(t, c) for t, c in zip(bruto["review_comment_title"].fillna(""),
                                                 bruto["review_comment_message"].fillna(""))]
    genericos = [t for t in textos if t and eh_generico(t)]
    vetores_genericos = indice.embutir(genericos)

    resultado = {"elogios_genericos_devolvidos": len(genericos), "por_pergunta": []}
    total = {"base do projeto": 0, "com elogios genéricos": 0, "genericos_entre_as_10": 0}

    for pergunta in ELOGIOS:
        vetor = indice.embutir([pergunta])[0]
        do_projeto = [indice.texto(p) for p, _ in indice.buscar_vetorial(vetor, 10, distintos=True)]

        candidatos = [(pontos, False, indice.texto(p)) for p, pontos in indice.buscar_vetorial(vetor, settings.K_BRUTO)]
        candidatos += [(float(pontos), True, t) for pontos, t in zip(vetores_genericos @ vetor, genericos)]
        com_genericos, vistos = [], set()
        for pontos, generico, texto in sorted(candidatos, key=lambda c: -c[0]):
            if normalizar(texto) not in vistos:
                vistos.add(normalizar(texto))
                com_genericos.append((generico, texto))
            if len(com_genericos) == 10:
                break

        relevantes_projeto = sum(juiz.julgar_relevancia(pergunta, do_projeto))
        relevantes_com = sum(juiz.julgar_relevancia(pergunta, [t for _, t in com_genericos]))
        quantos_genericos = sum(1 for generico, _ in com_genericos if generico)
        total["base do projeto"] += relevantes_projeto
        total["com elogios genéricos"] += relevantes_com
        total["genericos_entre_as_10"] += quantos_genericos
        resultado["por_pergunta"].append({
            "pergunta": pergunta, "relevantes_na_base_do_projeto": relevantes_projeto,
            "relevantes_com_elogios_genericos": relevantes_com, "genericos_entre_as_10": quantos_genericos,
            "exemplos_de_genericos": [t for generico, t in com_genericos if generico][:3],
        })

    evidencias = 10 * len(ELOGIOS)
    resultado["precisao_na_base_do_projeto"] = taxa(total["base do projeto"], evidencias)
    resultado["precisao_com_elogios_genericos"] = taxa(total["com elogios genéricos"], evidencias)
    resultado["genericos_entre_as_evidencias"] = total["genericos_entre_as_10"]
    resultado["evidencias"] = evidencias
    return resultado


# ---------------------------------------------------------------------------
# 5. Temas
# ---------------------------------------------------------------------------

def medir_temas(respondedor) -> dict:
    """Confere se os temas medidos na análise exploratória aparecem nas respostas às perguntas amplas."""
    with open(os.path.join(settings.PATHS["reports"], "analise_exploratoria.json"), encoding="utf-8") as f:
        temas_da_base = json.load(f)["temas_por_palavra_chave"]

    citados = []
    for pergunta in AMPLAS_SOBRE_PROBLEMAS:
        r = respondedor.responder(pergunta)
        citados += [r.evidencias[n - 1].texto for n in r.citadas]

    resultado = []
    for tema, dados in temas_da_base.items():
        aparece = any(re.search(TEMAS[tema], t, flags=re.IGNORECASE) for t in citados)
        resultado.append({"tema": tema, "pct_dos_comentarios": dados["pct_dos_comentarios"],
                          "pct_com_nota_1_2": dados["pct_com_nota_1_2"], "aparece_nas_respostas": aparece})
    return {"perguntas": AMPLAS_SOBRE_PROBLEMAS, "evidencias_citadas": len(citados), "temas": resultado}


# ---------------------------------------------------------------------------
# 6. Tempo
# ---------------------------------------------------------------------------

def medir_tempo(recuperador) -> dict:
    """Tempo de cada etapa em três perguntas, com as chamadas ao modelo feitas de verdade (sem cache)."""
    tempos = {"transformação da pergunta": [], "busca, fusão e seleção": [], "geração da resposta": []}
    for pergunta in RESPONDIVEIS[:3]:
        inicio = time.perf_counter()
        gerar_frases(pergunta, usar_cache=False)
        tempos["transformação da pergunta"].append(time.perf_counter() - inicio)

        inicio = time.perf_counter()
        recuperacao = recuperador.recuperar(pergunta)   # as frases desta pergunta já estão em cache
        tempos["busca, fusão e seleção"].append(time.perf_counter() - inicio)

        inicio = time.perf_counter()
        gerar(pergunta, recuperacao, usar_cache=False)
        tempos["geração da resposta"].append(time.perf_counter() - inicio)

    medianas = {etapa: round(float(np.median(valores)), 2) for etapa, valores in tempos.items()}
    return {"segundos_por_etapa": medianas, "segundos_no_total": round(sum(medianas.values()), 2)}


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

def conferir_criterios(r: dict) -> dict:
    c = settings.CRITERIOS
    medidas = {
        "precisao_minima_das_evidencias": (r["precisao"]["configuração do projeto"]["precisao"], ">="),
        "fidelidade_minima": (r["fidelidade"]["fidelidade"], ">="),
        "recusa_correta_minima": (r["recusa"]["recusa_correta"], ">="),
        "recusa_indevida_maxima": (r["recusa"]["recusa_indevida"], "<="),
    }
    return {nome: {"medido": valor, "criterio": c[nome],
                   "atingido": valor >= c[nome] if sentido == ">=" else valor <= c[nome]}
            for nome, (valor, sentido) in medidas.items()}


def executar() -> dict:
    respondedor = Respondedor()
    recuperador = respondedor.recuperador

    r = {}
    r["precisao"], relevancia = medir_precisao(recuperador)
    r["fidelidade"], respostas = medir_fidelidade(respondedor, relevancia)
    r["recusa"] = medir_recusa(respondedor, respostas)
    r["elogios_genericos"] = medir_elogios_genericos(recuperador.indice)
    r["temas"] = medir_temas(respondedor)
    r["tempo"] = medir_tempo(recuperador)
    if MODELO_COMPARADO:
        r["modelos_de_embeddings"] = medir_outro_modelo(recuperador.indice)
    r["criterios"] = conferir_criterios(r)

    os.makedirs(settings.PATHS["reports"], exist_ok=True)
    with open(CAMINHO_RESUMO, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    r = executar()
    print("\nCRITÉRIOS")
    for nome, c in r["criterios"].items():
        print(f"  {'ok  ' if c['atingido'] else 'FALHOU'} {nome}: medido {c['medido']} | critério {c['criterio']}")
    print("\nPRECISÃO DAS EVIDÊNCIAS")
    for nome, dados in r["precisao"].items():
        print(f"  {nome}: {dados['relevantes']} de {dados['evidencias']} ({dados['precisao']})")
    f = r["fidelidade"]
    print(f"\nFIDELIDADE: {f['sustentadas']} de {f['conclusoes']} conclusões sustentadas")
    print(f"  evidências relevantes usadas: {f['evidencias_relevantes_citadas']} de {f['evidencias_relevantes']}")
    print(f"\nRECUSA: {r['recusa']['recusadas']} de {r['recusa']['perguntas_sem_resposta']} recusadas | "
          f"respondíveis recusadas por engano: {len(r['recusa']['recusadas_por_engano'])}")
    e = r["elogios_genericos"]
    print(f"\nELOGIOS GENÉRICOS: precisão {e['precisao_na_base_do_projeto']} na base do projeto e "
          f"{e['precisao_com_elogios_genericos']} com os genéricos de volta")
    print(f"\nTEMPO: {r['tempo']}")
    if "modelos_de_embeddings" in r:
        m = r["modelos_de_embeddings"]
        print(f"\nMODELOS: projeto {m['precisao_do_modelo_do_projeto']} | {m['outro_modelo']} {m['precisao_do_outro_modelo']}")
    if not all(c["atingido"] for c in r["criterios"].values()):
        raise SystemExit("\nA avaliação não atingiu todos os critérios.")
