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
| Com título ou comentário | 42.389 |
| Documentos na base de conhecimento | 35.957 |

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

A base é gerada por `python -m src.preparacao.base_conhecimento`, que aplica as
regras da análise exploratória. O relatório está em
[`reports/base-de-conhecimento.md`](reports/base-de-conhecimento.md).

| Etapa | Avaliações |
|---|---|
| Linhas no arquivo | 99.224 |
| Uma avaliação por `review_id` | 98.410 |
| Com título ou comentário | 42.389 |
| Com pelo menos uma palavra | 42.251 |
| Sem os elogios genéricos | 35.957 |

Cada documento da base tem dois campos: `review_id`, que identifica a avaliação de
origem, e `texto`, com o título e o comentário juntos.

Tratamento do texto:

- Quando a avaliação só tem título ou só tem comentário, o texto é o campo que
  existe. Avaliações sem os dois não entram na base.
- Título e comentário são unidos em um texto. O título fica de fora quando já está
  contido no comentário.
- Quebras de linha e espaços repetidos são trocados por um espaço. Maiúsculas,
  pontuação e emojis são mantidos.
- Celular, link, e-mail e CPF são trocados por marcadores como `[CELULAR]`. Foram
  alterados 4 textos.

2.798 documentos têm o mesmo texto de outro documento, como "não recebi o produto".
Eles foram mantidos, porque cada um é a avaliação de um cliente diferente.

Antes de gravar, a base passa por seis checagens: `review_id` sem valor nulo e sem
repetição, e texto sem vazio, sem quebra de linha, sem dado pessoal e sem elogio
genérico. Se alguma falhar, a execução é interrompida.

## 6. Pipeline RAG

### Embeddings e indexação

Os índices são gerados por `python -m src.indexacao.indice`. O relatório está em
[`reports/indexacao.md`](reports/indexacao.md).

| | |
|---|---|
| Documentos indexados | 35.957 |
| Modelo de embeddings | `paraphrase-multilingual-MiniLM-L12-v2`, com vetores de 384 posições |
| Índice vetorial | FAISS com busca exata, 55 MB em disco |
| Índice de palavras | BM25, montado na carga |
| Tempo para gerar os vetores | cerca de 15 segundos com GPU (Mac) e 50 segundos em CPU |
| Tempo de uma busca | cerca de 10 ms em cada índice |

O projeto usa dois índices porque as duas buscas acertam em casos diferentes. A
busca por significado encontra frases escritas com outras palavras: para "cliente
não recebeu o que comprou" ela traz "O produto não foi entregue". A busca por
palavras acerta quando o termo exato importa: para "vendedor não respondeu às
mensagens" ela traz "Não respondeu nenhum de meus e-mails".

Na busca por palavras os acentos são retirados, porque os clientes escrevem
"ótimo" e "otimo", "não" e "nao". Palavras muito comuns também são retiradas, com
exceção de "não", que muda o sentido da frase.

1.122 comentários (3,1%) estão escritos em maiúsculas, e o modelo de embeddings
diferencia maiúsculas de minúsculas. Buscando 200 desses comentários pelo próprio
texto em minúsculas, só 27 apareciam entre os 20 primeiros resultados. Por isso o
vetor desses comentários é gerado com o texto em minúsculas, e os 200 passaram a
ser encontrados. O texto mostrado ao usuário não muda.

O índice guarda uma assinatura da base de conhecimento, o nome do modelo e a versão
do código. Se algum deles mudar, o programa não carrega o índice antigo e pede para
gerar de novo.

### Recuperação

A recuperação recebe a pergunta e devolve as 10 avaliações que servem de evidência.
O relatório, com um exemplo completo, está em
[`reports/recuperacao.md`](reports/recuperacao.md). Para ver cada etapa em uma
pergunta:

```bash
python -m src.recuperacao.recuperador "Quais os problemas com a entrega?"
```

| Etapa | O que acontece |
|---|---|
| 1. Transformação da pergunta | O Gemini reescreve a pergunta como cinco frases curtas que um cliente escreveria, cada uma sobre uma situação diferente. É uma variação da técnica HyDE |
| 2. Busca | A pergunta e as frases são procuradas no índice de significado. As frases também são procuradas no índice de palavras. São 11 rankings com até 20 avaliações cada |
| 3. Fusão | Os rankings são combinados com RRF. Quem aparece bem colocado em vários rankings sobe na lista |
| 4. Seleção | Ficam as 10 mais bem colocadas. Textos que dizem a mesma coisa (similaridade a partir de 0,80) contam como uma evidência só |

A pergunta é transformada porque ela não se parece com os comentários. Para
"problemas com a entrega do pedido", a busca direta traz como primeiro resultado um
elogio ("Eficiente do pedido a entrega"). Com as frases de busca, vêm reclamações
como "demorou quase 3 semanas para chegar".

Comparei quatro configurações em seis perguntas do enunciado, com 60 evidências em
cada configuração:

| Configuração | Sem relação com o assunto | Repetidas |
|---|---|---|
| A. Pergunta original, busca por significado | 0 | 0 |
| B. Pergunta original, significado e palavras | 16 | 0 |
| C. Com frases de busca, sem juntar parecidas | 0 | 20 |
| D. Configuração do projeto | 0 | 0 |

Por causa do resultado de B, a busca por palavras usa só as frases, e não a
pergunta original. Por causa do resultado de C, os textos que dizem a mesma coisa
são agrupados. Na avaliação, a precisão das evidências foi de 0,54 na configuração A
e de 0,75 na D.

Cada evidência guarda o `review_id`, o texto, a similaridade com a pergunta, os
rankings em que apareceu e quantas avaliações da base inteira dizem a mesma coisa.
Essas informações são usadas depois para mostrar ao usuário de onde veio a resposta.

Nas quatro perguntas sobre problemas, 15 das 40 evidências vêm de avaliações com
nota 3, 4 ou 5. São clientes que gostaram do produto e reclamaram de um ponto
específico. A busca pelo texto encontra essas reclamações, que um filtro por nota
baixa deixaria de fora.

## 7. Respostas fundamentadas em evidências

O relatório, com um exemplo completo e os testes, está em
[`reports/geracao.md`](reports/geracao.md). Para fazer uma pergunta:

```bash
python -m src.geracao.responder "O que os clientes relatam sobre problemas relacionados à entrega?"
```

A resposta é montada assim:

| Etapa | O que acontece |
|---|---|
| 1. Contexto | As 10 evidências são numeradas e enviadas ao modelo. Cada uma informa em quantas avaliações da base aquilo é dito |
| 2. Geração | O Gemini devolve uma lista de pontos. Cada ponto é uma conclusão com os números das evidências que a sustentam |
| 3. Validação | O programa descarta números de evidência que não existem e pontos que ficam sem evidência |
| 4. Quantidade | O programa conta, na base inteira, quantas avaliações dizem o mesmo que as evidências de cada ponto |

A resposta não tem texto livre, como um resumo. Tudo o que é mostrado como
conclusão está em um ponto, e todo ponto tem evidência com `review_id`. A
quantidade de avaliações é calculada pelo programa, e não escrita pelo modelo.

Exemplo, para a pergunta "O que os clientes relatam sobre problemas relacionados à
entrega?":

| Conclusão | Evidências | Avaliações na base |
|---|---|---|
| Os clientes relatam que receberam o produto com a caixa ou o pacote amassado. | [1] [6] | 77 |
| Os clientes relatam que a entrega demorou muito ou está muito atrasada. | [3] [9] | 72 |
| Os clientes relatam que o produto chegou mal embalado ou com a caixa quase aberta. | [1] [4] | 12 |
| Os clientes relatam que receberam a caixa aberta. | [2] [5] [8] | 5 |
| Os clientes relatam que receberam o produto incompleto, faltando item. | [10] | 4 |
| Os clientes relatam que o pacote veio rasgado. | [7] | 1 |

| # | Evidência | `review_id` |
|---|---|---|
| 6 | Recebi o produto porém veio amassado | `aab5578d9c3b538a382064790d63a8c4` |
| 9 | Não recebi a mercadoria...ESTÁ MUITO ATRASADA A ENTREGA... | `1a6763b35ea712ac4530a70a61898a6c` |
| 3 | Demorou muito para chegar. | `e3560b1fd3dd7d96fb0be8962bd15476` |

A lista completa das evidências está no relatório.

A quantidade de avaliações de cada ponto é um mínimo: conta só os textos muito
parecidos com as evidências (similaridade a partir de 0,80), e não todas as
avaliações sobre o tema. Ela vale para os comentários, e não para todos os clientes.

Nas cinco perguntas de exemplo do enunciado foram gerados 27 pontos. Nenhum foi
descartado na validação, e 41 das 50 evidências recuperadas foram citadas.

As avaliações são texto escrito por clientes e entram no prompt entre marcas, com a
instrução de que devem ser analisadas e não obedecidas. Testei com duas avaliações
inventadas que traziam instruções escondidas, e o modelo não obedeceu em nenhuma.

## 8. Perguntas sem evidência suficiente

O relatório, com todas as perguntas de teste, está em
[`reports/recusa.md`](reports/recusa.md).

O sistema passa por três conferências antes de mostrar uma resposta:

| Conferência | O que acontece |
|---|---|
| 1. A pergunta se parece com alguma avaliação? | A pergunta é comparada com a base. Se a avaliação mais parecida tiver similaridade abaixo de 0,50, a pergunta é recusada sem chamar o modelo |
| 2. As evidências respondem à pergunta? | O modelo vê a pergunta e as evidências. Se elas não respondem, ele marca que não responde e explica o que faltou. Se respondem só a uma parte, ele responde essa parte e diz o que ficou de fora |
| 3. O que sobrou tem evidência? | Se nenhum ponto ficou com evidência válida, a resposta é recusada. Se a resposta se apoia em menos de 5 avaliações da base, ela leva um aviso |

A resposta sai em uma de três situações:

| Situação | O que o usuário vê |
|---|---|
| respondida | Os pontos com as evidências |
| parcial | Os pontos com as evidências e um aviso do que faltou ou de que há pouca evidência |
| recusada | Só o aviso, com o motivo |

Testei com 31 perguntas em quatro grupos:

| Grupo | Perguntas | Como esperado |
|---|---|---|
| Respondível | 10 | 10 |
| Fora do escopo, como "Qual é a capital da França?" | 10 | 10 recusadas |
| Assunto que não existe na base, como "O que os clientes acham do pagamento por Pix?" | 8 | 8 recusadas |
| Só uma parte tem evidência, ou há pouca evidência | 3 | 3 respondidas com aviso |

Das 18 recusadas, 5 foram barradas na primeira conferência e 13 pelo modelo. Um
exemplo do que o usuário vê em uma recusa: "As avaliações encontradas não permitem
responder a essa pergunta. As avaliações fornecidas não mencionam o pagamento por
Pix."

O limite de 0,50 da primeira conferência é baixo de propósito, para nunca recusar
uma pergunta válida. Em 25 perguntas válidas escritas de jeitos diferentes, a menor
similaridade foi 0,61.

Essas 31 perguntas foram as mesmas usadas para definir os limites. Com perguntas
novas, na avaliação, o sistema recusou 18 de 20 perguntas sem resposta e nenhuma
das 20 respondíveis.

## 9. Avaliação da solução

O relatório completo está em [`reports/avaliacao.md`](reports/avaliacao.md). A
avaliação usa 40 perguntas novas, que não foram usadas nos passos anteriores para
definir limites nem para ajustar a instrução do modelo.

Os critérios mínimos foram definidos em `config/settings.py` antes de rodar a
avaliação:

| Critério | O que mede | Mínimo | Medido |
|---|---|---|---|
| Precisão das evidências | Parcela das evidências recuperadas que tratam do assunto da pergunta | 0,70 | 0,75 |
| Fidelidade | Parcela das conclusões que estão apoiadas nas evidências citadas | 0,90 | 0,99 |
| Recusa correta | Parcela das perguntas sem resposta que o sistema recusa | 0,90 | 0,90 |
| Recusa indevida | Parcela das perguntas respondíveis recusadas por engano (máximo) | 0,10 | 0,00 |

Para julgar se uma evidência trata do assunto e se uma conclusão está apoiada,
usei o Gemini como juiz. Conferi à mão uma amostra de 46 julgamentos e concordei
com 44. Nos 2 em que discordei, o juiz tinha sido mais rigoroso do que eu.

Principais resultados:

- **A transformação da pergunta melhora a busca.** A precisão das evidências foi de
  0,54 na busca simples e de 0,75 na configuração do projeto. Em "O que os clientes
  relatam sobre pedidos entregues em partes?", a busca simples trouxe 0 evidências
  relevantes em 10, e a do projeto trouxe 9.
- **As conclusões seguem as evidências.** 74 das 75 conclusões estão sustentadas. O
  modelo usou 141 das 150 evidências relevantes e citou só 4 das 50 que não
  tratavam do assunto.
- **O sistema recusou as 10 perguntas fora do escopo** e 8 das 10 sobre assuntos que
  não existem na base. Nenhuma das 20 perguntas respondíveis foi recusada.
- **Uma resposta leva entre 2,5 e 3 segundos**, quase tudo nas duas chamadas ao
  modelo.
- **Um modelo de embeddings maior ajuda pouco.** Na busca simples, a versão maior
  da mesma família teve precisão de 0,63 contra 0,58 do modelo do projeto, levando
  quase três vezes mais tempo para indexar. O ganho é menor que o da transformação
  da pergunta, e por isso o modelo foi mantido.

Onde o sistema errou:

- Em "Os clientes reclamam do seguro contra roubo oferecido na compra?", ele
  respondeu que "nunca houve problemas com o seguro". A avaliação citada diz
  "Seguro ... nunca houve problemas", em que "seguro" quer dizer confiável.
- A única conclusão não sustentada foi "Os clientes pedem o dinheiro de volta
  porque o produto chegou quebrado". As avaliações citadas falam do produto
  quebrado, mas não do pedido de dinheiro de volta.
- Em quatro das vinte perguntas a busca simples foi melhor que a do projeto.

A avaliação não tem medida de recall por documento. Nesta base muitas avaliações
dizem a mesma coisa, então não existe uma única avaliação correta para cada
pergunta.

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
| Elogios genéricos fora da base | Com eles de volta, a precisão da busca em perguntas sobre elogios cai de 0,78 para 0,75. O efeito é pequeno, mas esses textos não dizem o que foi elogiado |
| Elogio genérico identificado por lista de palavras | Um corte por tamanho também tiraria comentários curtos e úteis, como "não recebi" e "entrega rápida" |
| Modelo de embeddings multilíngue | Os comentários estão em português, e o modelo foi treinado para reconhecer frases com o mesmo sentido em vários idiomas |
| Modelo de embeddings menor (MiniLM) em vez do maior (mpnet) | Na busca simples o maior teve precisão de 0,63 contra 0,58, com quase três vezes mais tempo de indexação e 1,1 GB. A transformação da pergunta traz um ganho maior, de 0,54 para 0,75 |
| Índice vetorial com busca exata | Com 35.957 vetores a busca exata leva cerca de 10 ms. Um índice aproximado seria mais rápido, mas pode deixar de fora um documento relevante |
| Busca por palavras sem acento e com a palavra "não" | Os clientes escrevem a mesma palavra com e sem acento, e "não recebi" tem sentido oposto a "recebi" |
| Transformação da pergunta em frases de busca | A pergunta do usuário não se parece com os comentários. Com as frases, a busca traz reclamações quando a pergunta é sobre problemas |
| Busca por palavras só com as frases de busca | Com a pergunta original, 16 de 60 evidências não tinham relação com o assunto, como "Compro com frequência" |
| Textos que dizem a mesma coisa contam como uma evidência | Sem isso, 20 de 60 evidências repetiam outra, como "Demorou muito pra chegar" e "Demorou demais pra chegar" |
| Vetor dos comentários em maiúsculas gerado em minúsculas | O modelo diferencia maiúsculas de minúsculas. Sem a conversão, só 27 de 200 comentários em maiúsculas eram encontrados pela busca por significado |
| Resposta só com pontos, sem resumo livre | Um resumo escrito pelo modelo pode trazer informações sem indicar a evidência |
| Quantidade de avaliações contada pelo programa | O modelo não deve escrever números nem expressões como "a maioria". A contagem é feita na base, a partir das evidências citadas |
| Limite de 0,80 para tratar dois textos como iguais | Em amostras por faixa de similaridade, acima de 0,80 os textos têm o mesmo assunto e a mesma opinião. Abaixo disso já aparecem textos de sentido oposto |
| Avaliações entre marcas no prompt | O texto do cliente é dado, e não instrução. Um comentário como "favor desconsiderar a primeira avaliação" não pode mudar o comportamento do modelo |
| Recusa em três conferências | A similaridade da pergunta com a base não separa tudo: "receita de bolo de chocolate" tem similaridade de 0,73, porque há comentários sobre produtos sabor chocolate. Por isso o modelo também decide, vendo as evidências |
| Limite de 0,50 na primeira conferência | Perguntas válidas chegam a 0,61. Um limite mais alto recusaria perguntas que a base responde |
| Aviso quando a pergunta é respondida só em parte | Sem o aviso, uma pergunta sobre entrega e Pix era respondida só sobre entrega, e o usuário não ficava sabendo que o Pix não tinha evidência |
| Avaliação por precisão, e não por recall de documento | Muitas avaliações dizem a mesma coisa, então não existe uma única avaliação correta para cada pergunta |
| Critérios mínimos definidos antes de medir | Para o resultado não ser ajustado ao que o sistema consegue |
| Título junto com o comentário | Em parte das avaliações a informação está no título, como em "Não chegou meu produto" com o comentário "Péssimo" |
| Textos repetidos mantidos na base | São avaliações de clientes diferentes, e a repetição mostra que o problema é frequente |
| Frequências calculadas sobre os comentários | As notas 1 e 2 são 14,6% das avaliações e 26,5% dos comentários, então a base de texto tem mais reclamações que o total de avaliações |

_Atualizado a cada passo._

## 13. Limitações e evoluções

_Preenchido no Passo 10._

---

## Estrutura do repositório

```
tech-challenge-fase4/
├── config/            # caminhos, fonte dos dados e modelos
├── cache/             # o que o modelo já respondeu, para reproduzir sem gastar cota
├── data/              # não versionado
│   ├── raw/           # CSV de avaliações da Olist
│   ├── processed/     # base de conhecimento pronta
│   └── indice/        # índices FAISS e BM25
├── notebooks/         # análise exploratória
├── src/
│   ├── preparacao/    # carga, análise exploratória e base de conhecimento
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
- Cerca de 500 MB livres para o modelo de embeddings, baixado do Hugging Face na
  primeira execução

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
python -m src.preparacao.base_conhecimento   # monta a base em data/processed
python -m src.indexacao.indice               # gera os embeddings e o índice em data/indice
python -m src.recuperacao.comparacao         # compara as configurações da busca
python -m src.geracao.exemplos               # roda as perguntas de exemplo e os testes da geração
python -m src.geracao.recusa                 # testa as perguntas sem evidência suficiente
python -m src.avaliacao.avaliar              # avaliação com perguntas novas e conferência dos critérios
```

Para incluir na avaliação a comparação com outro modelo de embeddings, que baixa
mais 1,1 GB na primeira vez:

```bash
MODELO_COMPARADO=sentence-transformers/paraphrase-multilingual-mpnet-base-v2 python -m src.avaliacao.avaliar
```

No plano gratuito do Gemini são 15 chamadas por minuto. Quando esse limite é
atingido, o programa espera 45 segundos e tenta de novo.

_Os comandos das próximas etapas entram aqui à medida que os passos forem concluídos._

---

## Autor

**Thiago Corrêa Carvalho Diniz** — RM 371212

Pós-Graduação AI Scientist — FIAP
