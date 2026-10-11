# Voice of Customer Intelligence com RAG
> **Pós-Graduação em AI Scientist – FIAP** · Tech Challenge – Fase 4

Solução de RAG sobre as avaliações de clientes da Olist. O usuário faz uma pergunta
em linguagem natural e recebe uma resposta baseada nos comentários dos clientes,
junto com as avaliações usadas para montar a resposta.

---

## 1. Contexto e problema de negócio

Empresas de e-commerce recebem milhares de avaliações de clientes. A nota mostra o
nível de satisfação, mas o motivo da nota está no comentário escrito: atraso na
entrega, produto diferente do anúncio, entrega antes do prazo.

Analisar esses comentários manualmente é demorado. Este projeto usa
**Retrieval-Augmented Generation (RAG)** para isso: o sistema busca as avaliações
mais relacionadas à pergunta e envia esses textos como contexto para um modelo de
linguagem, que gera a resposta com base neles.

## 2. Objetivo da solução

O objetivo é permitir que gestores e analistas façam perguntas como:

- Quais são os principais problemas relatados pelos clientes?
- Quais reclamações relacionadas à entrega aparecem com maior frequência?
- O que os clientes mais elogiam em suas experiências de compra?
- Quais problemas são relatados por clientes insatisfeitos?
- Existem padrões recorrentes nas avaliações relacionadas à qualidade dos produtos?

A solução precisa atender a quatro pontos:

1. As respostas devem ser baseadas nas avaliações recuperadas da base.
2. Cada resposta deve mostrar quais avaliações foram usadas.
3. Em perguntas sobre o que é mais comum, a resposta deve informar em quantas
   avaliações o padrão aparece.
4. Quando não houver avaliações suficientes, ou a pergunta estiver fora do escopo,
   o sistema deve informar que não encontrou a resposta.

O desafio adicional de metadados (filtros por nota, período, categoria ou entrega)
não foi implementado.

## 3. Base de dados

A base é o **Brazilian E-Commerce Public Dataset by Olist**, disponível no
[Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), com cerca de
100 mil pedidos feitos entre 2016 e 2018. O projeto usa o arquivo de avaliações
(`olist_order_reviews_dataset.csv`), que tem a nota, o título e o comentário de
cada avaliação.

| | Avaliações |
|---|---|
| Linhas no arquivo | 99.224 |
| `review_id` únicos | 98.410 |
| Com algum texto (título ou comentário) | 42.293 |
| Previsão para a base de conhecimento | 35.957 |

Dois pontos da base influenciam o projeto:

- Clientes que dão nota baixa comentam mais. As notas 1 e 2 representam 14,6% das
  avaliações e 26,5% dos comentários. Por isso, a base de conhecimento representa
  os clientes que comentaram, e não o total de clientes.
- Os comentários são curtos. A mediana é de 53 caracteres e a plataforma limita o
  texto a 200 caracteres.

## 4. Arquitetura

_Preenchido no Passo 10._

## 5. Preparação da base de conhecimento

### Análise exploratória

O relatório está em [`reports/analise-exploratoria.md`](reports/analise-exploratoria.md)
e a análise passo a passo em
[`notebooks/01_analise_exploratoria.ipynb`](notebooks/01_analise_exploratoria.ipynb).

| Resultado da análise | O que foi decidido |
|---|---|
| 789 `review_id` aparecem em dois pedidos com o mesmo texto | Manter uma avaliação por `review_id` |
| 56.021 avaliações não têm título nem comentário | Não entram na base, porque não têm texto |
| 6.294 avaliações (14,9% das que têm texto) têm só elogio genérico, como "muito bom" | Não entram na base. A identificação é feita por uma lista de palavras, porque um corte por tamanho também tiraria comentários curtos e úteis, como "não recebi" |
| Os comentários têm no máximo 200 caracteres | Cada avaliação é um documento, sem dividir o texto |
| 2 avaliações com celular e 2 com link | Mascarar antes de indexar |
| 82 textos têm termos como "ignorar" ou "desconsiderar" | No prompt, as avaliações ficam separadas das instruções do modelo |
| Entrega aparece em 45,8% dos comentários, e 26% deles têm nota 1 ou 2 | A busca precisa diferenciar elogio e reclamação sobre entrega |
| Os nomes das lojas foram anonimizados na base ("lannister", "stark") | Não é possível responder perguntas sobre uma loja pelo nome real |

### Construção da base

_Preenchido no Passo 3._

## 6. Pipeline RAG

_Preenchido nos Passos 4 e 5._

## 7. Respostas fundamentadas em evidências

_Preenchido no Passo 6._

## 8. Perguntas sem evidência suficiente

_Preenchido no Passo 7._

## 9. Avaliação da solução

_Preenchido no Passo 8._

## 10. Exemplos de perguntas e respostas

_Preenchido no Passo 9._

## 11. Tecnologias e bibliotecas

| Etapa | Tecnologia |
|---|---|
| Dados | pandas, kagglehub |
| Embeddings | sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`) |
| Índice vetorial | FAISS |
| Busca lexical | BM25 (`rank_bm25`) |
| Geração da resposta | Gemini, via LangChain (`langchain-google-genai`) |
| Interface | Streamlit |

## 12. Decisões técnicas

| Decisão | Justificativa |
|---|---|
| Embeddings gerados localmente | A quantidade de textos ultrapassaria a cota gratuita da API do Gemini. Rodando local, o índice pode ser recriado sem chave de API |
| Uma avaliação por documento | Os comentários têm no máximo 200 caracteres, e dividir o texto dificultaria identificar a avaliação de origem |
| Elogio genérico identificado por lista de palavras | Um corte por tamanho também tiraria comentários curtos e úteis, como "não recebi" e "entrega rápida" |
| Frequências calculadas sobre os comentários | As notas 1 e 2 são 14,6% das avaliações e 26,5% dos comentários, então a base de texto tem mais reclamações que o total de avaliações |

_Atualizado a cada passo._

## 13. Limitações e evoluções

_Preenchido no Passo 10._

---

## Estrutura do repositório

```
tech-challenge-fase4/
├── config/            # caminhos, fonte dos dados e modelos
├── data/              # não versionado
│   ├── raw/           # CSV de avaliações da Olist
│   ├── processed/     # base de conhecimento pronta
│   └── indice/        # índices FAISS e BM25
├── notebooks/         # análise exploratória
├── src/
│   ├── preparacao/    # seleção, limpeza e montagem dos documentos
│   ├── indexacao/     # embeddings e índices de busca
│   ├── recuperacao/   # transformação da pergunta e busca híbrida
│   ├── geracao/       # contexto, resposta com citações e recusa
│   └── avaliacao/     # recuperação, citações e recusas
├── app/               # interface de demonstração (Streamlit)
├── reports/           # números e resultados de cada etapa
├── images/            # figuras da análise
└── docs/              # arquitetura, apresentação e vídeo
```

## Como executar

**Pré-requisitos**
- Python 3.12
- Chave gratuita da API do Gemini, gerada no
  [Google AI Studio](https://aistudio.google.com/apikey)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # preencha GOOGLE_API_KEY
```

**Etapas**

```bash
python -m src.preparacao.carga         # baixa a base do Kaggle para data/raw (sem login)
python -m src.preparacao.exploracao    # números e figuras da análise exploratória
```

_Os comandos das próximas etapas entram aqui à medida que os passos forem concluídos._

---

## Autor

**Thiago Corrêa Carvalho Diniz** — RM 371212

Pós-Graduação AI Scientist — FIAP
