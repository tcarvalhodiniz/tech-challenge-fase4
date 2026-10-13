"""
Comparação das configurações de busca.

Mostra o que cada etapa da recuperação muda no resultado. Cada pergunta é
buscada em quatro configurações, e para as 10 evidências de cada uma são
contadas duas coisas:

    baixa similaridade  evidências com similaridade abaixo de 0,40 com a
                        pergunta e com as frases de busca. São textos que
                        entraram sem ter relação com o assunto.
    repetidas           evidências que dizem o mesmo que outra mais bem colocada
                        (similaridade a partir de 0,80). Ocupam uma vaga sem trazer
                        informação nova.

As duas medidas saem dos próprios vetores, sem depender de avaliação manual. A
avaliação da relevância das evidências é feita na etapa de avaliação.

Uso:  python -m src.recuperacao.comparacao
"""

import json
import os

import numpy as np

from config import settings
from src.preparacao.carga import carregar_avaliacoes
from src.recuperacao.recuperador import Recuperador

CAMINHO_RESUMO = os.path.join(settings.PATHS["reports"], "recuperacao.json")

BAIXA_SIMILARIDADE = 0.40

PERGUNTAS = [
    "Quais são os principais problemas relatados pelos clientes?",
    "Quais reclamações relacionadas à entrega aparecem com maior frequência?",
    "Quais problemas são relatados por clientes insatisfeitos?",
    "O que os clientes relatam sobre problemas relacionados à entrega?",
    "O que os clientes mais elogiam em suas experiências de compra?",
    "Existem padrões recorrentes nas avaliações relacionadas à qualidade dos produtos?",
]

CONFIGURACOES = {
    "A. pergunta original, busca por significado":
        {"transformar": False},
    "B. pergunta original, significado e palavras":
        {"transformar": False, "palavras_na_pergunta": True},
    "C. com frases de busca, sem juntar parecidas":
        {"transformar": True, "juntar_parecidas": False},
    "D. configuração do projeto":
        {"transformar": True},
}


def contar_repetidas(recuperador: Recuperador, evidencias) -> int:
    vetores = np.stack([recuperador.indice.vetor(e.posicao) for e in evidencias])
    parecidos = vetores @ vetores.T >= settings.SIMILARIDADE_TEXTO_PARECIDO
    # conta a evidência i se alguma anterior (mais bem colocada) é quase igual a ela
    return int(sum(parecidos[i, :i].any() for i in range(len(evidencias))))


def executar() -> dict:
    recuperador = Recuperador()
    notas = carregar_avaliacoes().drop_duplicates("review_id").set_index("review_id")["review_score"]

    resumo = {"perguntas": [], "total_por_configuracao": {}}
    totais = {nome: {"baixa_similaridade": 0, "repetidas": 0} for nome in CONFIGURACOES}

    for pergunta in PERGUNTAS:
        item = {"pergunta": pergunta, "configuracoes": {}}
        for nome, opcoes in CONFIGURACOES.items():
            r = recuperador.recuperar(pergunta, **opcoes)
            medidas = {
                "baixa_similaridade": sum(e.similaridade < BAIXA_SIMILARIDADE for e in r.evidencias),
                "repetidas": contar_repetidas(recuperador, r.evidencias),
            }
            item["configuracoes"][nome] = medidas
            for chave, valor in medidas.items():
                totais[nome][chave] += valor
            if nome.startswith("D"):
                item["frases_de_busca"] = r.frases
                item["evidencias"] = [
                    {"texto": e.texto, "similaridade": e.similaridade,
                     "avaliacoes_na_base": e.avaliacoes_na_base, "nota": int(notas[e.review_id])}
                    for e in r.evidencias
                ]
        resumo["perguntas"].append(item)

    resumo["total_por_configuracao"] = totais
    resumo["evidencias_por_configuracao"] = len(PERGUNTAS) * settings.EVIDENCIAS
    os.makedirs(settings.PATHS["reports"], exist_ok=True)
    with open(CAMINHO_RESUMO, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    return resumo


if __name__ == "__main__":
    resumo = executar()
    total = resumo["evidencias_por_configuracao"]
    print(f"em {total} evidências ({len(PERGUNTAS)} perguntas):\n")
    print(f"  {'configuração':48s} baixa similaridade   repetidas")
    for nome, t in resumo["total_por_configuracao"].items():
        print(f"  {nome:48s} {t['baixa_similaridade']:10d} {t['repetidas']:16d}")
