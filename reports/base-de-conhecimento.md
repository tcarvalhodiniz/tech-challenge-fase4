# Base de conhecimento

A base é gerada por `python -m src.preparacao.base_conhecimento`. As regras vêm da
[análise exploratória](analise-exploratoria.md). Os números desta página estão em
[`base_conhecimento.json`](base_conhecimento.json).

## Etapas

| Etapa | Avaliações | Saíram |
|---|---|---|
| Linhas no arquivo | 99.224 | |
| Uma avaliação por `review_id` | 98.410 | 814 |
| Com título ou comentário | 42.389 | 56.021 |
| Com pelo menos uma palavra | 42.251 | 138 |
| Sem os elogios genéricos | 35.957 | 6.294 |

A base final tem **35.957 documentos**.

## Formato do documento

Cada documento tem dois campos:

| Campo | Conteúdo |
|---|---|
| `review_id` | Identificador da avaliação na base da Olist |
| `texto` | Título e comentário em um texto só |

O `review_id` permite voltar da resposta do sistema para a avaliação original. A
base fica em `data/processed/base_conhecimento.parquet` e não é versionada, porque
pode ser recriada com o comando acima.

## Tratamento do texto

### Valores ausentes

O título está ausente em 88% das avaliações e o comentário em
59%. Quando só um dos dois existe, o texto do documento é o campo que existe.
Avaliações sem título e sem comentário não entram na base.

### Título e comentário

Os dois são unidos em um texto, separados por ponto. O
título fica de fora quando já está contido no comentário, para não repetir a mesma
frase.

### Limpeza

Quebras de linha e espaços repetidos são trocados por um espaço.
Maiúsculas, pontuação, emojis e erros de digitação são mantidos, para que a
avaliação apareça na resposta como o cliente escreveu.

### Dados pessoais

Celular, link, e-mail e CPF são trocados por marcadores como
`[CELULAR]` e `[LINK]`. Foram alterados 4 textos.

### Exemplos

| Título | Comentário | Texto do documento |
|---|---|---|
| Não chegou meu produto | Péssimo | Não chegou meu produto. Péssimo |
| MT lindo | MT lindo | MT lindo |
| (ausente) | Ótima compra, o prazo era para o dia 28, e chegou no dia 10.↵Eu paguei a entrega econômica. | Ótima compra, o prazo era para o dia 28, e chegou no dia 10. Eu paguei a entrega econômica. |
| Recomendo a compra nessa | (ausente) | Recomendo a compra nessa |

## Textos repetidos

2.798 documentos têm o mesmo texto de outro documento. O caso mais comum é "não
recebi o produto", que aparece 88 vezes. Esses documentos foram mantidos, porque
cada um é a avaliação de um cliente diferente e a repetição mostra que o problema
é frequente. Na etapa de busca, textos iguais vão ser agrupados para não ocupar o
contexto com a mesma frase.

## Checagens

Antes de gravar, a base passa por seis checagens. Se alguma falhar, a execução é
interrompida.

| Checagem | Resultado |
|---|---|
| `review_id` sem valor nulo | ok |
| `review_id` sem repetição | ok |
| Texto com pelo menos uma palavra | ok |
| Texto sem quebra de linha | ok |
| Texto sem celular, link, e-mail ou CPF | ok |
| Texto que não é só elogio genérico | ok |

## Limitação

A lista de palavras usada para identificar elogio genérico é conservadora. Alguns
textos com pouca informação continuam na base, como títulos cortados ("Recomendo a
compra nessa"). Eles têm pouca chance de serem recuperados, porque não se parecem
com nenhuma pergunta sobre a experiência de compra.
