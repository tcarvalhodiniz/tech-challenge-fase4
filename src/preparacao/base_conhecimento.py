"""
Construção da base de conhecimento a partir das avaliações da Olist.

Aplica as regras definidas na análise exploratória e grava um documento por
avaliação em data/processed/base_conhecimento.parquet. A contagem de cada etapa
e o resultado das validações ficam em reports/base_conhecimento.json.

Cada documento tem dois campos:
    review_id  identifica a avaliação de origem
    texto      título e comentário, limpos e com dados pessoais mascarados
"""

import json
import os

import pandas as pd

from config import settings
from src.preparacao.carga import carregar_avaliacoes
from src.preparacao.texto import eh_generico, mascarar, montar_texto, normalizar, tem_dado_pessoal, tokens

CAMINHO_BASE = os.path.join(settings.PATHS["processed"], "base_conhecimento.parquet")
CAMINHO_RESUMO = os.path.join(settings.PATHS["reports"], "base_conhecimento.json")


def construir(bruto: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Devolve a base de conhecimento e a contagem de avaliações em cada etapa."""
    etapas = {"linhas_no_arquivo": len(bruto)}

    # 1. Uma avaliação por review_id
    df = bruto.drop_duplicates("review_id")
    etapas["review_id_unicos"] = len(df)

    # 2. Só avaliações com título ou comentário. Valor ausente vira texto vazio,
    #    e quem não tem nenhum dos dois sai.
    titulos = df["review_comment_title"].fillna("")
    comentarios = df["review_comment_message"].fillna("")
    df = df[(titulos != "") | (comentarios != "")]
    etapas["com_titulo_ou_comentario"] = len(df)

    # 3. Título e comentário em um texto só, já sem quebras de linha
    texto = pd.Series(
        [montar_texto(t, c) for t, c in zip(df["review_comment_title"].fillna(""),
                                            df["review_comment_message"].fillna(""))],
        index=df.index,
    )

    # 4. Saem os textos sem nenhuma palavra e os que são só elogio genérico
    texto = texto[texto.map(lambda t: len(tokens(t)) > 0)]
    etapas["com_pelo_menos_uma_palavra"] = len(texto)
    texto = texto[~texto.map(eh_generico)]
    etapas["sem_elogio_generico"] = len(texto)

    # 5. Dados pessoais mascarados
    mascarado = texto.map(mascarar)
    etapas["textos_com_dado_mascarado"] = int((mascarado != texto).sum())

    base = pd.DataFrame({
        "review_id": df.loc[mascarado.index, "review_id"].to_numpy(),
        "texto": mascarado.to_numpy(),
    })
    etapas["documentos_na_base"] = len(base)
    return base, etapas


def validar(base: pd.DataFrame) -> dict:
    """Checagens que a base precisa passar. Se alguma falhar, a execução para."""
    checagens = {
        "review_id_sem_nulo": bool(base["review_id"].notna().all()),
        "review_id_sem_repeticao": bool(base["review_id"].is_unique),
        "texto_sem_vazio": bool(base["texto"].map(lambda t: len(tokens(t)) > 0).all()),
        "texto_sem_quebra_de_linha": not bool(base["texto"].map(lambda t: "\n" in t or "\r" in t).any()),
        "texto_sem_dado_pessoal": not bool(base["texto"].map(tem_dado_pessoal).any()),
        "texto_sem_elogio_generico": not bool(base["texto"].map(eh_generico).any()),
    }
    falhas = [nome for nome, ok in checagens.items() if not ok]
    if falhas:
        raise SystemExit(f"Base de conhecimento reprovada nas checagens: {', '.join(falhas)}")
    return checagens


def perfil(base: pd.DataFrame) -> dict:
    tamanho = base["texto"].str.len()
    palavras = base["texto"].map(lambda t: len(tokens(t)))
    repeticoes = base["texto"].map(normalizar).value_counts()
    return {
        "caracteres_mediana": int(tamanho.median()),
        "caracteres_max": int(tamanho.max()),
        "palavras_mediana": int(palavras.median()),
        "textos_distintos": int(len(repeticoes)),
        "documentos_com_texto_repetido": int(repeticoes[repeticoes > 1].sum()),
    }


def executar() -> dict:
    base, etapas = construir(carregar_avaliacoes())
    resumo = {"etapas": etapas, "checagens": validar(base), "perfil": perfil(base)}

    os.makedirs(settings.PATHS["processed"], exist_ok=True)
    base.to_parquet(CAMINHO_BASE, index=False)
    with open(CAMINHO_RESUMO, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    return resumo


def carregar_base() -> pd.DataFrame:
    """Lê a base de conhecimento, construindo antes se ela ainda não existir."""
    if not os.path.exists(CAMINHO_BASE):
        executar()
    return pd.read_parquet(CAMINHO_BASE)


if __name__ == "__main__":
    print(json.dumps(executar(), ensure_ascii=False, indent=2))
