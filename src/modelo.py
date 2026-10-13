"""
Acesso ao modelo de linguagem (Gemini).

Centraliza a criação do modelo e a espera quando a API recusa a chamada por
limite de requisições por minuto. No plano gratuito são 15 por minuto, e uma
sequência de perguntas passa disso com facilidade.
"""

import time

from langchain_google_genai import ChatGoogleGenerativeAI

from config import settings

ESPERA_SEGUNDOS = 45
TENTATIVAS = 5


def criar_modelo() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=settings.MODELO_GERACAO, temperature=0, max_retries=1)


def chamar(cadeia, entrada: dict):
    """Executa a cadeia. Se a API recusar por limite por minuto, espera e tenta de novo.

    Outros erros, como chave inválida ou limite diário, sobem na hora.
    """
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            return cadeia.invoke(entrada)
        except Exception as erro:
            limite_por_minuto = "RESOURCE_EXHAUSTED" in str(erro) and "PerMinute" in str(erro)
            if not limite_por_minuto or tentativa == TENTATIVAS:
                raise
            print(f"[modelo] limite de chamadas por minuto atingido; aguardando {ESPERA_SEGUNDOS}s")
            time.sleep(ESPERA_SEGUNDOS)
