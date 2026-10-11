"""
Análise exploratória das avaliações da Olist.

Gera os números de reports/analise_exploratoria.json e as figuras de images/.
Cada achado daqui vira uma regra de seleção ou de limpeza no Passo 3.

A normalização de texto usa o módulo `re` do Python, via `map`, e não os
métodos de `Series.str`: no pandas 3 eles rodam no PyArrow, em que `\\w` não
reconhece letras acentuadas.
"""

import json
import os
import re
import unicodedata

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import settings
from src.preparacao.carga import carregar_avaliacoes

# ---------------------------------------------------------------------------
# Vocabulário e padrões
# ---------------------------------------------------------------------------

# Palavras que expressam satisfação sem dizer com o quê. Um comentário formado
# só por elas ("muito bom", "recomendo", "ótimo produto") não serve de
# evidência para nenhuma pergunta sobre a experiência. A lista é conservadora:
# na dúvida a palavra fica de fora, e o comentário é mantido.
VOCAB_GENERICO = set("""
bom boa bons boas muito muita mto mt ótimo ótima otimo otima excelente
excelentes recomendo recomendado recomendaria super ok okay tudo certo
certinho gostei amei adorei legal perfeito perfeita top show nota dez
parabéns parabens satisfeito satisfeita obrigado obrigada grato grata
produto produtos compra loja maravilhoso maravilhosa lindo linda bem beleza
sim aprovado aprovei bastante sem comentário comentários comentario
comentarios nada declarar todos todas
e o a os as de do da dos das um uma em no na com para pelo pela eu estou
fiquei foi é está sou
""".split())

# Temas por palavras-chave. É uma estimativa grosseira e independente do RAG:
# serve de referência para conferir, no Passo 8, se as respostas sobre
# frequência estão na ordem de grandeza certa. Um comentário pode citar
# mais de um tema.
TEMAS = {
    "Entrega e prazo": r"entreg|prazo|atras|demor|chegou|chegar|correios?",
    "Atendimento e vendedor": r"atendiment|vendedor|\bloja\b|\bsac\b|contato|retorno",
    "Qualidade e defeito": r"qualidade|defeit|quebr|danific|estrag|n[ãa]o funcion|fr[áa]gil",
    "Não recebeu o produto": r"n[ãa]o (recebi|chegou|foi entregue)|ainda n[ãa]o (recebi|chegou)",
    "Troca e devolução": r"\btroca|devolu|reembols|estorno|cancel",
    "Embalagem": r"embala",
    "Produto errado ou diferente": r"errad|diferente|outro produto|trocad",
    "Preço": r"pre[çc]o|barat|\bcaro\b|custo",
    "Item faltando": r"faltou|faltando|incomplet",
}

# Padrões estreitos de propósito, para não confundir com número de pedido ou
# data: o celular exige DDD seguido de 9, e o CPF candidato só conta se o
# dígito verificador fechar.
DADOS_PESSOAIS = {
    "e-mail": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "celular": r"(?<!\d)\(?\d{2}\)?[\s-]?9\d{4}[\s-]?\d{4}(?!\d)",
    "link": r"https?://\S+|www\.\S+",
}
CANDIDATO_CPF = r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)"

# Termos que fariam um texto parecer instrução para o modelo de linguagem.
TERMOS_INSTRUCAO = r"ignor|instru[cç]|desconsider|prompt|system|assistente|responda|esque[cç]a"

# Na anonimização da base, nomes de lojas foram trocados por casas de Game of Thrones.
LOJAS_ANONIMIZADAS = r"\b(lannister|targaryen|stark|baratheon|tyrell|martell|greyjoy|arryn|tully)\b"

LIMITE_CARACTERES = 200

# ---------------------------------------------------------------------------
# Funções de texto
# ---------------------------------------------------------------------------


def tokens(texto: str) -> list[str]:
    return re.findall(r"\w+", texto.lower())


def normalizar(texto: str) -> str:
    """Minúsculas, sem pontuação e com espaços simples. Só para comparar textos."""
    return " ".join(tokens(texto))


def eh_generico(texto: str) -> bool:
    """Verdadeiro quando todas as palavras são genéricas ou números soltos ("10", "nota 1000")."""
    tk = tokens(texto)
    return len(tk) > 0 and all(t in VOCAB_GENERICO or t.isdigit() for t in tk)


def contem(serie: pd.Series, padrao: str) -> pd.Series:
    return serie.map(lambda t: bool(re.search(padrao, t, flags=re.IGNORECASE)))


def cpf_valido(candidato: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", candidato)]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for pos in (9, 10):
        resto = sum(d[i] * (pos + 1 - i) for i in range(pos)) % 11
        if d[pos] != (0 if resto < 2 else 11 - resto):
            return False
    return True


def tem_cpf(texto: str) -> bool:
    return any(cpf_valido(c) for c in re.findall(CANDIDATO_CPF, texto))


def tem_emoji(texto: str) -> bool:
    return any(unicodedata.category(c) == "So" for c in texto)


def texto_completo(df: pd.DataFrame) -> pd.Series:
    """Título e comentário juntos, como vão compor o documento no Passo 3."""
    titulo = df["review_comment_title"].fillna("").str.strip()
    comentario = df["review_comment_message"].fillna("").str.strip()
    return (titulo + ". " + comentario).str.strip(". ").str.strip()


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------


def perfil(bruto: pd.DataFrame) -> dict:
    r = {}

    # Unidade de análise: a avaliação. O mesmo review_id aparece em pedidos
    # diferentes com nota e texto idênticos; conta-se uma vez.
    repetidos = bruto[bruto["review_id"].duplicated(keep=False)]
    por_id = repetidos.groupby("review_id").agg(
        pedidos=("order_id", "nunique"),
        notas=("review_score", "nunique"),
        textos=("review_comment_message", lambda s: s.fillna("").nunique()),
    )
    df = bruto.drop_duplicates("review_id").copy()
    r["volume"] = {
        "linhas_no_arquivo": len(bruto),
        "review_id_unicos": int(bruto["review_id"].nunique()),
        "review_id_repetidos": int(len(por_id)),
        "linhas_removidas_na_deduplicacao": int(len(bruto) - len(df)),
        "repetidos_com_nota_ou_texto_diferente": int(((por_id["notas"] > 1) | (por_id["textos"] > 1)).sum()),
        "pedidos_com_mais_de_uma_avaliacao": int((bruto["order_id"].value_counts() > 1).sum()),
        "periodo": [str(df["review_creation_date"].min().date()), str(df["review_creation_date"].max().date())],
    }

    tem_coment = df["review_comment_message"].notna()
    tem_titulo = df["review_comment_title"].notna()
    r["cobertura"] = {
        "avaliacoes": len(df),
        "com_comentario": int(tem_coment.sum()),
        "com_titulo": int(tem_titulo.sum()),
        "com_titulo_e_comentario": int((tem_coment & tem_titulo).sum()),
        "so_titulo": int((~tem_coment & tem_titulo).sum()),
        "sem_texto": int((~tem_coment & ~tem_titulo).sum()),
        "pct_com_comentario": round(tem_coment.mean() * 100, 1),
    }

    # Viés de quem escreve: a taxa de comentário muda muito com a nota.
    notas = sorted(df["review_score"].unique())
    dist_todas = df["review_score"].value_counts(normalize=True)
    dist_coment = df.loc[tem_coment, "review_score"].value_counts(normalize=True)
    taxa = df.groupby("review_score")["review_comment_message"].apply(lambda s: s.notna().mean())
    r["vies_de_selecao"] = {
        "pct_com_comentario_por_nota": {int(n): round(taxa[n] * 100, 1) for n in notas},
        "distribuicao_notas_todas": {int(n): round(dist_todas[n] * 100, 1) for n in notas},
        "distribuicao_notas_com_comentario": {int(n): round(dist_coment[n] * 100, 1) for n in notas},
        "pct_notas_1_2_todas": round(dist_todas[[1, 2]].sum() * 100, 1),
        "pct_notas_1_2_com_comentario": round(dist_coment[[1, 2]].sum() * 100, 1),
    }

    coment = df.loc[tem_coment, "review_comment_message"]
    tamanho = coment.str.len()
    palavras = coment.map(lambda t: len(tokens(t)))
    r["tamanho"] = {
        "caracteres_mediana": int(tamanho.median()),
        "caracteres_p90": int(tamanho.quantile(0.9)),
        "caracteres_max": int(tamanho.max()),
        "palavras_mediana": int(palavras.median()),
        "palavras_p90": int(palavras.quantile(0.9)),
        "exatamente_no_limite": int((tamanho == LIMITE_CARACTERES).sum()),
        "a_ate_5_do_limite": int((tamanho >= LIMITE_CARACTERES - 5).sum()),
        "pct_a_ate_5_do_limite": round((tamanho >= LIMITE_CARACTERES - 5).mean() * 100, 1),
    }

    normalizados = coment.map(normalizar)
    contagem = normalizados.value_counts()
    r["repeticao"] = {
        "textos_unicos": int(len(contagem)),
        "pct_textos_unicos": round(len(contagem) / len(normalizados) * 100, 1),
        "mais_repetidos": {t if t else "(sem palavras)": int(n) for t, n in contagem.head(20).items()},
    }

    texto = texto_completo(df)
    com_texto = texto != ""
    generico = texto[com_texto].map(eh_generico)
    sem_palavra = texto[com_texto].map(lambda t: len(tokens(t)) == 0)
    r["informatividade"] = {
        "avaliacoes_com_algum_texto": int(com_texto.sum()),
        "so_elogio_generico": int(generico.sum()),
        "pct_so_elogio_generico": round(generico.mean() * 100, 1),
        "nota_media_genericos": round(df.loc[generico[generico].index, "review_score"].mean(), 2),
        "nota_media_demais": round(df.loc[generico[~generico].index, "review_score"].mean(), 2),
        "sem_nenhuma_palavra": int(sem_palavra.sum()),
        "previsao_base_de_conhecimento": int((~generico & ~sem_palavra).sum()),
    }

    r["ruido"] = {
        "quebra_de_linha": int(coment.str.contains(r"[\r\n]").sum()),
        "tudo_maiusculo": int(coment.map(lambda t: sum(c.isalpha() for c in t) >= 10 and t.upper() == t).sum()),
        "letra_repetida_3x": int(contem(coment, r"([a-zà-ú])\1\1").sum()),
        "emoji": int(coment.map(tem_emoji).sum()),
    }

    textos = texto[com_texto]
    r["dados_pessoais"] = {nome: int(contem(textos, p).sum()) for nome, p in DADOS_PESSOAIS.items()}
    r["dados_pessoais"]["CPF"] = int(textos.map(tem_cpf).sum())
    r["termos_de_instrucao"] = int(contem(textos, TERMOS_INSTRUCAO).sum())
    r["lojas_anonimizadas"] = int(contem(textos, LOJAS_ANONIMIZADAS).sum())

    base_temas = df.loc[tem_coment].copy()
    base_temas["texto"] = texto[tem_coment]
    temas = {}
    for tema, padrao in TEMAS.items():
        cita = contem(base_temas["texto"], padrao)
        temas[tema] = {
            "comentarios": int(cita.sum()),
            "pct_dos_comentarios": round(cita.mean() * 100, 1),
            "pct_com_nota_1_2": round((base_temas.loc[cita, "review_score"] <= 2).mean() * 100, 0),
        }
    r["temas_por_palavra_chave"] = temas

    return r


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

COR = {
    "serie": "#2a78d6",
    "destaque": "#eb6834",
    "texto": "#0b0b0b",
    "texto_sec": "#52514e",
    "grade": "#e4e3df",
    "fundo": "#fcfcfb",
}


def pct(v: float, casas: int = 1) -> str:
    return f"{v:.{casas}f}%".replace(".", ",")


def _eixo(titulo: str, subtitulo: str, figsize=(9, 5)):
    fig, ax = plt.subplots(figsize=figsize, facecolor=COR["fundo"])
    ax.set_facecolor(COR["fundo"])
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(COR["grade"])
    ax.tick_params(colors=COR["texto_sec"], labelsize=10)
    fig.text(0.02, 0.97, titulo, fontsize=14, fontweight="bold", color=COR["texto"], va="top")
    fig.text(0.02, 0.91, subtitulo, fontsize=10.5, color=COR["texto_sec"], va="top")
    return fig, ax


def _salvar(fig, nome: str) -> str:
    os.makedirs(settings.PATHS["images"], exist_ok=True)
    caminho = os.path.join(settings.PATHS["images"], nome)
    fig.savefig(caminho, dpi=150, facecolor=COR["fundo"], bbox_inches="tight")
    plt.close(fig)
    return caminho


def fig_comentario_por_nota(r: dict) -> str:
    v = r["vies_de_selecao"]
    taxa = v["pct_com_comentario_por_nota"]
    fig, ax = _eixo("Quem dá nota baixa escreve mais",
                    "Percentual de avaliações que trazem comentário, por nota")
    fig.subplots_adjust(top=0.80)
    notas = list(taxa.keys())
    barras = ax.bar([str(n) for n in notas], list(taxa.values()), width=0.55, color=COR["serie"])
    for b, val in zip(barras, taxa.values()):
        ax.text(b.get_x() + b.get_width() / 2, val + 1.2, pct(val), ha="center",
                color=COR["texto"], fontsize=11)
    ax.set_xlabel("Nota da avaliação", color=COR["texto_sec"])
    ax.set_ylim(0, 90)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.text(0.98, 0.95,
            f"Notas 1 e 2 são {pct(v['pct_notas_1_2_todas'])} das avaliações\n"
            f"e {pct(v['pct_notas_1_2_com_comentario'])} dos comentários",
            transform=ax.transAxes, ha="right", va="top", fontsize=10.5, color=COR["texto_sec"])
    return _salvar(fig, "01_comentario_por_nota.png")


def fig_tamanho(df: pd.DataFrame, r: dict) -> str:
    t = r["tamanho"]
    tamanho = df["review_comment_message"].dropna().str.len()
    fig, ax = _eixo("Comentários curtos, com teto de 200 caracteres",
                    f"Distribuição do tamanho dos comentários · mediana de {t['caracteres_mediana']} "
                    f"caracteres ({t['palavras_mediana']} palavras)")
    fig.subplots_adjust(top=0.80)
    # Faixas de 5 caracteres terminando em 201, para que os comentários com
    # exatamente 200 fiquem na última faixa antes da linha do limite
    ax.hist(tamanho, bins=range(1, 216, 5), color=COR["serie"], edgecolor=COR["fundo"], linewidth=1)
    ax.axvline(LIMITE_CARACTERES + 1, color=COR["texto_sec"], ls="--", lw=1.2)
    ax.text(LIMITE_CARACTERES - 4, ax.get_ylim()[1] * 0.92,
            f"limite da plataforma\n{t['exatamente_no_limite']} comentários com exatamente 200",
            ha="right", va="top", fontsize=10, color=COR["texto_sec"])
    ax.set_xlabel("Caracteres", color=COR["texto_sec"])
    ax.set_ylabel("Comentários", color=COR["texto_sec"])
    ax.grid(axis="y", color=COR["grade"], lw=0.8)
    ax.set_axisbelow(True)
    return _salvar(fig, "02_tamanho_comentarios.png")


def fig_repetidos(r: dict) -> str:
    itens = [(t, n) for t, n in r["repeticao"]["mais_repetidos"].items() if t != "(sem palavras)"]
    itens = itens[:14][::-1]
    i = r["informatividade"]
    milhar = f"{i['so_elogio_generico']:,}".replace(",", ".")
    fig, ax = _eixo("Entre os textos mais repetidos, só um diz o que aconteceu",
                    f"Comentários mais frequentes · {milhar} avaliações "
                    f"({pct(i['pct_so_elogio_generico'])}) são só elogio genérico",
                    figsize=(9, 6))
    fig.subplots_adjust(top=0.84, left=0.24)
    cores = [COR["serie"] if eh_generico(t) else COR["destaque"] for t, _ in itens]
    ax.barh([t for t, _ in itens], [n for _, n in itens], height=0.6, color=cores)
    for y, (_, n) in enumerate(itens):
        ax.text(n + 6, y, str(n), va="center", fontsize=10, color=COR["texto"])
    ax.tick_params(axis="y", labelsize=10.5, colors=COR["texto"])
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=COR["serie"], label="só elogio genérico"),
                       Patch(color=COR["destaque"], label="descreve algo da experiência")],
              loc="lower right", frameon=False, fontsize=10, labelcolor=COR["texto"])
    return _salvar(fig, "03_comentarios_mais_repetidos.png")


def fig_temas(r: dict) -> str:
    temas = sorted(r["temas_por_palavra_chave"].items(), key=lambda kv: kv[1]["pct_dos_comentarios"])
    fig, ax = _eixo("Entrega domina os comentários, para o bem e para o mal",
                    "Percentual de comentários que citam cada tema · estimativa por palavras-chave;\n"
                    "um comentário pode citar mais de um tema", figsize=(9, 5.5))
    fig.subplots_adjust(top=0.80, left=0.27)
    nomes = [t for t, _ in temas]
    valores = [d["pct_dos_comentarios"] for _, d in temas]
    ax.barh(nomes, valores, height=0.6, color=COR["serie"])
    for y, (_, d) in enumerate(temas):
        ax.text(d["pct_dos_comentarios"] + 0.8, y,
                f"{pct(d['pct_dos_comentarios'])}  ·  {int(d['pct_com_nota_1_2'])}% com nota 1 ou 2",
                va="center", fontsize=10, color=COR["texto"])
    ax.set_xlim(0, 75)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", labelsize=10.5, colors=COR["texto"])
    return _salvar(fig, "04_temas_por_palavra_chave.png")


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------


def executar() -> dict:
    bruto = carregar_avaliacoes()
    resumo = perfil(bruto)
    unicas = bruto.drop_duplicates("review_id")
    resumo["figuras"] = [
        os.path.relpath(p, settings.RAIZ)
        for p in (fig_comentario_por_nota(resumo), fig_tamanho(unicas, resumo),
                  fig_repetidos(resumo), fig_temas(resumo))
    ]
    os.makedirs(settings.PATHS["reports"], exist_ok=True)
    with open(os.path.join(settings.PATHS["reports"], "analise_exploratoria.json"), "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    return resumo


if __name__ == "__main__":
    resumo = executar()
    print(json.dumps({k: v for k, v in resumo.items() if k != "repeticao"}, ensure_ascii=False, indent=2))
