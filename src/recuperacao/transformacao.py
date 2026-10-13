"""
Transformação da pergunta em frases de busca.

A pergunta do usuário é escrita de um jeito diferente dos comentários. "Quais os
problemas com a entrega?" não se parece com "meu pedido não chegou". Aqui um
modelo de linguagem reescreve a pergunta como frases curtas que um cliente
escreveria em uma avaliação, e essas frases vão para a busca junto com a
pergunta original.

Nesta etapa o modelo não responde à pergunta. Ele só ajuda a buscar.

As frases geradas ficam em cache (cache/frases_de_busca.json), para a mesma
pergunta não gastar cota da API de novo. O arquivo é versionado: quem reproduzir
o projeto obtém as mesmas frases para as perguntas já feitas. Se o modelo não
estiver disponível, a função devolve uma lista vazia e a busca segue só com a
pergunta original.
"""

import hashlib
import json
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from config import settings

ARQ_CACHE = os.path.join(settings.RAIZ, "cache", "frases_de_busca.json")

INSTRUCAO = """Você ajuda a buscar avaliações de clientes de uma loja online brasileira.

Reescreva a pergunta do usuário como {quantidade} frases curtas que um cliente \
escreveria em uma avaliação sobre esse assunto. As frases vão ser usadas em uma \
busca, então devem se parecer com comentários reais.

Regras:
- No máximo 8 palavras por frase, em linguagem simples de cliente.
- Se a pergunta é sobre problemas ou reclamações, escreva reclamações.
- Se a pergunta é sobre elogios, escreva elogios.
- Cada frase deve tratar de uma situação diferente dentro do assunto da pergunta. \
Não escreva duas frases sobre a mesma situação.
- Não responda à pergunta."""


class FrasesDeBusca(BaseModel):
    frases: list[str] = Field(description="Frases curtas que um cliente escreveria em uma avaliação")


def _chave(pergunta: str) -> str:
    """Muda se a pergunta, o modelo, a instrução ou a quantidade de frases mudar."""
    conteudo = "|".join([settings.MODELO_GERACAO, INSTRUCAO, str(settings.FRASES_DE_BUSCA), pergunta.strip().lower()])
    return hashlib.sha256(conteudo.encode()).hexdigest()


def _ler_cache() -> dict:
    if not os.path.exists(ARQ_CACHE):
        return {}
    with open(ARQ_CACHE, encoding="utf-8") as f:
        return json.load(f)


def _gravar_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(ARQ_CACHE), exist_ok=True)
    with open(ARQ_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _pedir_ao_modelo(pergunta: str) -> list[str]:
    modelo = ChatGoogleGenerativeAI(model=settings.MODELO_GERACAO, temperature=0)
    prompt = ChatPromptTemplate.from_messages([("system", INSTRUCAO), ("human", "Pergunta: {pergunta}")])
    cadeia = prompt | modelo.with_structured_output(FrasesDeBusca)
    return cadeia.invoke({"pergunta": pergunta, "quantidade": settings.FRASES_DE_BUSCA}).frases


def gerar_frases(pergunta: str, usar_cache: bool = True) -> list[str]:
    """Frases de busca para a pergunta. Lista vazia se o modelo não responder."""
    cache = _ler_cache() if usar_cache else {}
    chave = _chave(pergunta)
    if chave in cache:
        return cache[chave]["frases"]

    try:
        geradas = _pedir_ao_modelo(pergunta)
    except Exception as erro:
        print(f"[transformação] modelo indisponível ({type(erro).__name__}); busca só com a pergunta original")
        return []

    # Tira repetições e a própria pergunta, e limita à quantidade pedida
    frases, vistas = [], {pergunta.strip().lower()}
    for frase in geradas:
        frase = frase.strip()
        if frase and frase.lower() not in vistas:
            vistas.add(frase.lower())
            frases.append(frase)
    frases = frases[: settings.FRASES_DE_BUSCA]

    if usar_cache:
        cache = _ler_cache()
        cache[chave] = {"pergunta": pergunta, "frases": frases}
        _gravar_cache(cache)
    return frases


if __name__ == "__main__":
    import sys

    pergunta = " ".join(sys.argv[1:]) or "Quais são os principais problemas com a entrega?"
    print(pergunta)
    for frase in gerar_frases(pergunta):
        print("  -", frase)
