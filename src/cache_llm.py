"""
Cache das chamadas ao modelo de linguagem.

Guarda em arquivos JSON na pasta cache/ o que o modelo já respondeu, para a
mesma chamada não gastar cota da API de novo. Os arquivos são versionados: quem
reproduzir o projeto obtém os mesmos resultados para as perguntas já feitas.
"""

import hashlib
import json
import os

from config import settings

PASTA = os.path.join(settings.RAIZ, "cache")


def chave(*partes: str) -> str:
    """Identifica uma chamada. Muda se qualquer parte mudar (modelo, instrução, pergunta...)."""
    return hashlib.sha256("|".join(partes).encode()).hexdigest()


def ler(nome: str) -> dict:
    caminho = os.path.join(PASTA, f"{nome}.json")
    if not os.path.exists(caminho):
        return {}
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def gravar(nome: str, dados: dict) -> None:
    os.makedirs(PASTA, exist_ok=True)
    with open(os.path.join(PASTA, f"{nome}.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
