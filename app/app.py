"""
Interface de demonstração.

Mostra, para uma pergunta, a resposta com as evidências e o caminho que o
sistema fez até chegar nela.

Uso:  streamlit run app/app.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from config import settings
from src.geracao.contexto import montar_contexto
from src.geracao.responder import PARCIAL, RECUSADA, Respondedor

EXEMPLOS = [
    "Quais são os principais problemas relatados pelos clientes em suas avaliações?",
    "O que os clientes relatam sobre problemas relacionados à entrega?",
    "Quais aspectos da experiência de compra são mais elogiados pelos clientes?",
    "Quais padrões podem ser identificados nas avaliações de clientes insatisfeitos?",
    "Quais avaliações sustentam a conclusão de que existem problemas recorrentes relacionados ao prazo de entrega?",
    "O que os clientes dizem sobre a entrega e sobre o pagamento por Pix?",
    "O que os clientes acham do pagamento por Pix?",
    "Qual é a capital da França?",
]

SITUACOES = {
    "respondida": "As avaliações respondem à pergunta.",
    "parcial": "As avaliações respondem só a uma parte da pergunta, ou há pouca evidência.",
    "recusada": "Não foi possível responder com as avaliações da base.",
}


def numero(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def quantidade(n: int) -> str:
    return "1 avaliação" if n == 1 else f"{n:,} avaliações".replace(",", ".")


@st.cache_resource(show_spinner="Carregando a base de avaliações e os índices...")
def carregar() -> Respondedor:
    return Respondedor()


def usar_exemplo() -> None:
    if st.session_state.get("exemplo"):
        st.session_state["pergunta"] = st.session_state["exemplo"]
        st.session_state["enviar"] = True


def mostrar_resposta(r) -> None:
    st.subheader("Resposta")
    if r.situacao == RECUSADA:
        st.error(SITUACOES[r.situacao])
    elif r.situacao == PARCIAL:
        st.warning(SITUACOES[r.situacao])
    else:
        st.success(SITUACOES[r.situacao])
    for aviso in r.avisos:
        st.markdown(f"**Aviso:** {aviso}")

    for ponto in r.pontos:
        citacoes = " ".join(f"`[{n}]`" for n in ponto.evidencias)
        verbo = "diz" if ponto.avaliacoes_na_base == 1 else "dizem"
        st.markdown(f"- {ponto.conclusao} {citacoes}  \n"
                    f"  <small>{quantidade(ponto.avaliacoes_na_base)} na base {verbo} o mesmo</small>",
                    unsafe_allow_html=True)
    if r.descartados:
        st.caption(f"{len(r.descartados)} ponto(s) descartado(s) por não ter evidência válida.")


def mostrar_evidencias(r) -> None:
    st.subheader("Evidências")
    if not r.pontos:
        st.caption("Sem conclusões, não há evidências a mostrar.")
        return
    st.caption("Avaliações que sustentam as conclusões. O número é o mesmo que aparece ao lado de cada conclusão.")
    for n in r.citadas:
        e = r.evidencias[n - 1]
        with st.container(border=True):
            st.markdown(f"**[{n}]** {e.texto}")
            st.caption(f"review_id `{e.review_id}` · dito em {quantidade(e.avaliacoes_na_base)} da base · "
                       f"similaridade {numero(e.similaridade)}")

    outras = [n for n in range(1, len(r.evidencias) + 1) if n not in r.citadas]
    if outras:
        with st.expander(f"Recuperadas e não usadas na resposta ({len(outras)})"):
            for n in outras:
                e = r.evidencias[n - 1]
                st.markdown(f"**[{n}]** {e.texto}")
                st.caption(f"review_id `{e.review_id}` · similaridade {numero(e.similaridade)}")


def mostrar_caminho(r, indice) -> None:
    st.subheader("Como a resposta foi encontrada")
    if not r.evidencias:
        st.markdown(
            f"A pergunta foi comparada com a base antes de chamar o modelo. A avaliação mais parecida tem "
            f"similaridade de **{numero(r.similaridade_da_pergunta)}**, abaixo do mínimo de "
            f"{numero(settings.SIMILARIDADE_MINIMA_DA_PERGUNTA)}. Por isso a pergunta foi recusada sem busca e "
            f"sem chamada ao modelo.")
        return

    etapas = st.tabs(["1. Transformação da pergunta", "2. Busca", "3. Fusão e seleção", "4. Contexto", "5. Resposta"])

    with etapas[0]:
        st.markdown("A pergunta é reescrita como frases curtas que um cliente escreveria em uma avaliação. "
                    "Essas frases vão para a busca junto com a pergunta original.")
        for frase in r.recuperacao.frases or ["(nenhuma: o modelo não estava disponível, e a busca usou só a pergunta)"]:
            st.markdown(f"- {frase}")

    with etapas[1]:
        st.markdown(f"A pergunta e as frases são procuradas no índice de significado. As frases também são "
                    f"procuradas no índice de palavras. Foram {len(r.recuperacao.rankings)} rankings. "
                    f"Abaixo, os três primeiros resultados de cada um.")
        for nome, posicoes in r.recuperacao.rankings.items():
            tipo, consulta = nome.split(" | ", 1)
            with st.expander(f"{tipo}: {consulta}"):
                for posicao in posicoes[:3]:
                    st.markdown(f"- {indice.texto(posicao)}")

    with etapas[2]:
        st.markdown("Os rankings são combinados com RRF, e ficam as avaliações mais bem colocadas. Textos que dizem "
                    "a mesma coisa contam como uma evidência só.")
        linhas = ["| # | Pontuação RRF | Similaridade | Rankings | Avaliações na base | Texto |",
                  "|---|---|---|---|---|---|"]
        for n, e in enumerate(r.evidencias, start=1):
            texto = e.texto.replace("|", "/")
            texto = texto if len(texto) <= 90 else texto[:90] + "..."
            linhas.append(f"| {n} | {numero(e.pontuacao, 4)} | {numero(e.similaridade)} | {len(e.rankings)} | "
                          f"{e.avaliacoes_na_base} | {texto} |")
        st.markdown("\n".join(linhas))

    with etapas[3]:
        st.markdown("Texto enviado ao modelo junto com a pergunta. O que está entre as marcas é tratado como dado "
                    "escrito por clientes, e não como instrução.")
        st.code(montar_contexto(r.evidencias), language=None, wrap_lines=True)

    with etapas[4]:
        st.markdown("O modelo devolve as conclusões com os números das evidências. O programa confere se cada "
                    "número existe, descarta conclusões sem evidência e conta as avaliações na base.")
        st.markdown(f"- Conclusões mostradas: **{len(r.pontos)}**\n"
                    f"- Conclusões descartadas: **{len(r.descartados)}**\n"
                    f"- Evidências citadas: **{len(r.citadas)} de {len(r.evidencias)}**\n"
                    f"- Avaliações da base que sustentam a resposta: **{r.avaliacoes_que_sustentam}**")


st.set_page_config(page_title="Voz do Cliente", layout="wide")

st.title("Voz do Cliente")
st.caption("Perguntas sobre a experiência dos clientes da Olist, respondidas com as avaliações que eles escreveram.")

if not os.getenv("GOOGLE_API_KEY"):
    st.error("Configure GOOGLE_API_KEY no arquivo .env para usar a interface.")
    st.stop()

respondedor = carregar()
indice = respondedor.recuperador.indice

with st.sidebar:
    st.header("Sobre")
    st.markdown(
        f"- **{len(indice.documentos):,}** avaliações na base de conhecimento\n".replace(",", ".")
        + f"- Embeddings: `{settings.MODELO_EMBEDDINGS.split('/')[-1]}`\n"
        + f"- Geração: `{settings.MODELO_GERACAO}`")
    st.markdown("**Como ler a resposta**")
    st.markdown("- Cada conclusão aponta para as avaliações que a sustentam.\n"
                "- A quantidade ao lado conta as avaliações da base com texto igual ou muito parecido.\n"
                "- A base tem só os clientes que escreveram comentário. Quem dá nota baixa comenta mais.")

st.text_input("Pergunta", key="pergunta", placeholder="Ex.: O que os clientes relatam sobre problemas na entrega?")
coluna_botao, coluna_exemplos = st.columns([1, 4])
clicou = coluna_botao.button("Perguntar", type="primary", width="stretch")
coluna_exemplos.selectbox("Exemplos", EXEMPLOS, index=None, key="exemplo", on_change=usar_exemplo,
                          placeholder="Ou escolha uma pergunta de exemplo", label_visibility="collapsed")

if clicou or st.session_state.pop("enviar", False):
    pergunta = st.session_state.get("pergunta", "").strip()
    if pergunta:
        with st.spinner("Buscando avaliações e gerando a resposta..."):
            try:
                st.session_state["resposta"] = respondedor.responder(pergunta)
            except Exception as erro:
                st.session_state.pop("resposta", None)
                st.error(f"Não foi possível gerar a resposta ({type(erro).__name__}). "
                         f"Confira a chave da API e o limite de uso, e tente de novo.")

resposta = st.session_state.get("resposta")
if resposta:
    st.divider()
    st.markdown(f"#### {resposta.pergunta}")
    esquerda, direita = st.columns(2, gap="large")
    with esquerda:
        mostrar_resposta(resposta)
    with direita:
        mostrar_evidencias(resposta)
    st.divider()
    mostrar_caminho(resposta, indice)
