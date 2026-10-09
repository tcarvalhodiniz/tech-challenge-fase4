# Voice of Customer Intelligence com RAG
> **Pós-Graduação em AI Scientist – FIAP** · Tech Challenge – Fase 4

Solução que transforma as avaliações escritas pelos clientes da Olist em uma base
de conhecimento consultável em linguagem natural. O gestor faz uma pergunta e
recebe uma resposta construída a partir dos comentários reais, acompanhada das
avaliações que a sustentam.

---

## 1. Contexto e problema de negócio

A nota de uma avaliação mostra *quanto* o cliente ficou satisfeito, mas não *por
quê*. O motivo está no comentário: o pedido que atrasou, o produto que chegou
diferente do anúncio, a entrega que veio antes do prazo. É nesse texto livre que
estão os insights mais úteis, e é justamente ele que não cabe em um painel de
indicadores.

Ler milhares de comentários à mão não escala. A proposta é usar
**Retrieval-Augmented Generation (RAG)**: recuperar as avaliações relevantes para
cada pergunta e entregá-las como contexto a um modelo de linguagem, que responde
apoiado no que os clientes de fato escreveram.

## 2. Objetivo da solução

Permitir que gestores e analistas façam perguntas como:

- Quais são os principais problemas relatados pelos clientes?
- Quais reclamações relacionadas à entrega aparecem com maior frequência?
- O que os clientes mais elogiam em suas experiências de compra?
- Quais problemas são relatados por clientes insatisfeitos?
- Existem padrões recorrentes nas avaliações relacionadas à qualidade dos produtos?

E receber respostas que cumpram quatro exigências:

1. **Fundamentadas:** todo insight vem de avaliações recuperadas da base.
2. **Rastreáveis:** a resposta mostra quais avaliações a sustentam.
3. **Honestas sobre frequência:** quando a pergunta é sobre o que é mais comum, a
   resposta informa em quantas avaliações o padrão aparece, em vez de generalizar
   a partir de poucos exemplos.
4. **Capazes de recusar:** sem evidência suficiente, ou diante de uma pergunta
   fora do escopo, a solução diz que não encontrou a informação em vez de inventar.

O desafio adicional de exploração por metadados (filtros por nota, período,
categoria ou entrega) não faz parte desta entrega.

## 3. Base de dados

**Brazilian E-Commerce Public Dataset by Olist**, disponível no
[Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce): cerca de 100
mil pedidos feitos entre 2016 e 2018. O foco está no arquivo de avaliações
(`olist_order_reviews_dataset.csv`), que traz a nota, o título e o comentário
escrito pelo cliente.

_Volume, cobertura de comentários e qualidade do texto: Passo 2._

## 4. Arquitetura

_Preenchido no Passo 10._

## 5. Preparação da base de conhecimento

_Preenchido nos Passos 2 e 3._

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

_Os comandos de cada etapa entram aqui à medida que os passos forem concluídos._

---

## Autor

**Thiago Corrêa Carvalho Diniz** — RM 371212

Pós-Graduação AI Scientist — FIAP
