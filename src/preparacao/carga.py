"""
Obtenção e leitura das avaliações da Olist.

O download usa o kagglehub, que guarda a base em um cache local. O CSV de
avaliações é copiado para data/raw para que o restante do projeto não dependa
do caminho desse cache.
"""

import os
import shutil

import pandas as pd

from config import settings

CAMINHO_CSV = os.path.join(settings.PATHS["raw"], settings.ARQUIVO_AVALIACOES)

COLUNAS_DATA = ["review_creation_date", "review_answer_timestamp"]


def baixar_avaliacoes(forcar: bool = False) -> str:
    """Baixa a base do Kaggle e copia o arquivo de avaliações para data/raw."""
    if os.path.exists(CAMINHO_CSV) and not forcar:
        return CAMINHO_CSV

    import kagglehub

    pasta = kagglehub.dataset_download(settings.KAGGLE_DATASET)
    os.makedirs(settings.PATHS["raw"], exist_ok=True)
    shutil.copy(os.path.join(pasta, settings.ARQUIVO_AVALIACOES), CAMINHO_CSV)
    return CAMINHO_CSV


def carregar_avaliacoes() -> pd.DataFrame:
    """Lê o CSV de avaliações com as datas já convertidas."""
    return pd.read_csv(baixar_avaliacoes(), parse_dates=COLUNAS_DATA)


if __name__ == "__main__":
    caminho = baixar_avaliacoes()
    print(f"Avaliações em {os.path.relpath(caminho, settings.RAIZ)}")
