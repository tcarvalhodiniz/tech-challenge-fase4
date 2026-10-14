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

# Semente dos sorteios, para os resultados se repetirem
SEMENTE = 42

# ---------------------------------------------------------------------------
# Recuperação
# ---------------------------------------------------------------------------
# Frases de busca geradas a partir da pergunta do usuário. Cada frase trata de
# uma situação diferente dentro do assunto, para a busca não ficar em um ponto só.
FRASES_DE_BUSCA = 5

# Resultados diferentes que cada busca devolve para cada frase
K_POR_BUSCA = 20

# Resultados pedidos ao índice antes de juntar os textos iguais. Precisa ser bem
# maior que K_POR_BUSCA, porque um mesmo texto pode aparecer em dezenas de
# avaliações ("não recebi o produto" aparece em 88).
K_BRUTO = 300

# Constante da fusão RRF. 60 é o valor usual e o usado nas aulas.
RRF_K = 60

# Avaliações que seguem como evidência para a geração da resposta
EVIDENCIAS = 10

# Similaridade de cosseno a partir da qual dois textos são tratados como dizendo a
# mesma coisa. É usada para juntar evidências parecidas e para contar, na base
# inteira, quantas avaliações repetem uma evidência. Medido em amostras por faixa
# de similaridade: acima de 0,80 os textos falam do mesmo assunto com a mesma
# opinião; entre 0,70 e 0,80 já aparecem textos de sentido oposto (para "Produto
# de péssima qualidade" vem "Produto de Qualidade").
SIMILARIDADE_TEXTO_PARECIDO = 0.80

# ---------------------------------------------------------------------------
# Perguntas sem evidência suficiente
# ---------------------------------------------------------------------------
# Similaridade mínima entre a pergunta e a avaliação mais parecida da base. Abaixo
# disso a pergunta é recusada antes de chamar o modelo. O valor é baixo de
# propósito, para nunca recusar uma pergunta válida: nos testes, perguntas válidas
# ficaram a partir de 0,61, e perguntas sem relação com a base, como "Qual é a
# capital da França?", ficaram abaixo de 0,50. As demais recusas ficam por conta
# do modelo, que vê a pergunta junto com as evidências.
SIMILARIDADE_MINIMA_DA_PERGUNTA = 0.50

# Quando a resposta se apoia em menos avaliações da base do que isto, ela é
# mostrada com um aviso de pouca evidência.
MINIMO_DE_AVALIACOES = 5

# ---------------------------------------------------------------------------
# Avaliação
#   Critérios mínimos, definidos antes de rodar a avaliação. Se algum não for
#   atingido, a avaliação termina com erro e o resultado é investigado.
# ---------------------------------------------------------------------------
CRITERIOS = {
    # Parcela das evidências recuperadas que tratam do assunto da pergunta
    "precisao_minima_das_evidencias": 0.70,
    # Parcela das conclusões que estão de fato sustentadas pelas evidências citadas
    "fidelidade_minima": 0.90,
    # Parcela das perguntas sem resposta possível que o sistema recusa
    "recusa_correta_minima": 0.90,
    # Parcela máxima das perguntas respondíveis que o sistema recusa por engano
    "recusa_indevida_maxima": 0.10,
}
