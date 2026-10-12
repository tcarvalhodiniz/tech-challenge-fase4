"""
Configuração central da solução de Voice of Customer com RAG.

Caminhos, fonte dos dados e modelos ficam aqui. Os parâmetros de recuperação e
os critérios mínimos de qualidade entram nos passos em que são definidos, para
que cada valor tenha a sua justificativa ao lado.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATHS = {
    "raw": os.path.join(RAIZ, "data", "raw"),
    "processed": os.path.join(RAIZ, "data", "processed"),
    "indice": os.path.join(RAIZ, "data", "indice"),
    "reports": os.path.join(RAIZ, "reports"),
    "images": os.path.join(RAIZ, "images"),
}

# ---------------------------------------------------------------------------
# Fonte: Brazilian E-Commerce Public Dataset by Olist (Kaggle)
#   O foco do desafio é o texto das avaliações, que está em um único arquivo.
# ---------------------------------------------------------------------------
KAGGLE_DATASET = "olistbr/brazilian-ecommerce"
ARQUIVO_AVALIACOES = "olist_order_reviews_dataset.csv"

# ---------------------------------------------------------------------------
# Modelos
#   Embeddings rodam localmente: dezenas de milhares de avaliações pela API
#   estourariam a cota gratuita, e local o índice é reproduzível sem chave.
#   A geração usa o Gemini, configurável pelo .env.
# ---------------------------------------------------------------------------
MODELO_EMBEDDINGS = os.getenv(
    "MODELO_EMBEDDINGS", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
MODELO_GERACAO = os.getenv("GEMINI_CHAT_MODEL", "gemini-flash-lite-latest")

SEMENTE = 42
