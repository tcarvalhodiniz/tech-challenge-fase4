# Análise exploratória das avaliações

A análise passo a passo está em
[`notebooks/01_analise_exploratoria.ipynb`](../notebooks/01_analise_exploratoria.ipynb).
Os números estão em [`analise_exploratoria.json`](analise_exploratoria.json) e são
gerados por `python -m src.preparacao.exploracao`.

## Volume

| | Avaliações |
|---|---|
| Linhas no arquivo | 99.224 |
| `review_id` únicos | 98.410 |
| Com comentário | 40.668 (41,3%) |
| Com título | 11.519 |
| Só título, sem comentário | 1.721 |
| Sem título e sem comentário | 56.021 |
| Com algum texto | 42.293 |
| Previsão para a base de conhecimento | 35.957 |

As avaliações vão de 02/10/2016 a 31/08/2018.

Existem 789 `review_id` que aparecem em dois pedidos. Em todos os casos a nota e o
texto são iguais nas duas linhas, então é a mesma avaliação registrada duas vezes.
Na base de conhecimento cada `review_id` entra uma vez.

## Comentários por nota

| Nota | Com comentário | % entre todas as avaliações | % entre as com comentário |
|---|---|---|---|
| 1 | 76,6% | 11,5% | 21,2% |
| 2 | 68,0% | 3,2% | 5,2% |
| 3 | 43,6% | 8,2% | 8,7% |
| 4 | 31,3% | 19,3% | 14,6% |
| 5 | 35,9% | 57,8% | 50,3% |

Clientes que dão nota baixa comentam mais. As notas 1 e 2 somam 14,6% das
avaliações e 26,5% dos comentários. Como a base de conhecimento é formada pelos
comentários, ela tem proporcionalmente mais reclamações que o total de avaliações.
Por isso, quando uma resposta do sistema falar de frequência, ela vai se referir
aos comentários e não ao total de clientes.

![](../images/01_comentario_por_nota.png)

## Tamanho dos comentários

A mediana é de 53 caracteres (9 palavras) e 90% dos comentários têm até 161
caracteres. A plataforma limita o texto a 200 caracteres: 654 comentários têm
exatamente esse tamanho, e alguns foram cortados no meio de uma palavra.

Como os textos são curtos, cada avaliação vai ser um documento da base, sem dividir
o texto em partes.

![](../images/02_tamanho_comentarios.png)

## Comentários genéricos

6.294 avaliações com texto (14,9%) têm apenas elogio genérico, como "muito bom",
"recomendo", "ótimo produto" e "nota 10". A nota média dessas avaliações é 4,66. A
das demais é 3,54.

Esses comentários não informam qual aspecto da compra o cliente avaliou, então não
ajudam a responder as perguntas do projeto. Eles não entram na base.

Para identificar esses casos usei uma lista de palavras genéricas
(`VOCAB_GENERICO`). Um comentário só é considerado genérico quando todas as suas
palavras estão na lista. Não usei o tamanho do texto como critério porque isso
também tiraria comentários curtos e úteis, como "não recebi" e "entrega rápida".

![](../images/03_comentarios_mais_repetidos.png)

## Ruído e dados pessoais

| Ocorrência | Avaliações | Tratamento |
|---|---|---|
| Quebra de linha | 3.806 | Substituída por espaço |
| Texto todo em maiúsculas | 1.096 | Mantido |
| Letra repetida ("muuuito") | 256 | Mantido |
| Emoji | 288 | Mantido |
| Celular | 2 | Mascarado como `[CELULAR]` |
| Link | 2 | Mascarado como `[LINK]` |
| E-mail e CPF | 0 | |

Maiúsculas e emojis foram mantidos para que a avaliação apareça na resposta como o
cliente escreveu.

O detector de celular exige DDD seguido de 9 e o de CPF valida o dígito
verificador, para não confundir com número de pedido ou data.

## Textos com termos de instrução

82 avaliações têm termos como "ignorar", "instruções" ou "desconsiderar". Li todas.
São clientes pedindo manual de instruções, dizendo que foram ignorados pelo
vendedor, e um caso pedindo para "desconsiderar a primeira avaliação". Nenhuma é
uma tentativa de manipular um modelo de linguagem.

Mesmo assim, no prompt as avaliações vão ficar separadas das instruções do modelo e
identificadas como dados.

## Nomes de lojas

1.951 comentários citam nomes como "lannister", "stark", "baratheon" e
"targaryen". Na anonimização da base, os nomes das lojas foram trocados por esses
nomes. Por isso não é possível responder perguntas sobre uma loja pelo nome real.

## Temas

Para ter uma ideia dos assuntos mais citados, contei os comentários que têm
palavras-chave de cada tema. É uma estimativa simples, e um comentário pode citar
mais de um tema. Esses números vão ser usados na etapa de avaliação para comparar
com as respostas do sistema.

| Tema | % dos comentários | % com nota 1 ou 2 |
|---|---|---|
| Entrega e prazo | 45,8% | 26% |
| Atendimento e vendedor | 10,6% | 36% |
| Qualidade e defeito | 9,5% | 28% |
| Não recebeu o produto | 8,0% | 86% |
| Troca e devolução | 3,8% | 78% |
| Preço | 3,4% | 19% |
| Embalagem | 3,3% | 18% |
| Produto errado ou diferente | 3,0% | 70% |
| Item faltando | 1,6% | 65% |

Entrega é o tema mais citado, e a maior parte desses comentários é positiva
("chegou antes do prazo"). Os temas com mais notas baixas são não recebimento do
produto, troca e devolução e produto errado.

Como entrega aparece tanto em elogios quanto em reclamações, a busca vai precisar
diferenciar os dois casos.

![](../images/04_temas_por_palavra_chave.png)

## Regras para a base de conhecimento

1. Manter uma avaliação por `review_id`.
2. Usar apenas avaliações com título ou comentário.
3. Juntar título e comentário em um único texto.
4. Retirar avaliações só com elogio genérico e as que não têm nenhuma palavra.
5. Trocar quebra de linha por espaço e manter o restante do texto como está.
6. Mascarar celular e link.
7. Guardar o `review_id` em cada documento, para identificar a avaliação de origem.
