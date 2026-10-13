# Recuperação

A recuperação recebe a pergunta do usuário e devolve as avaliações que vão servir
de evidência para a resposta.

```bash
python -m src.recuperacao.recuperador "Quais os problemas com a entrega?"   # mostra cada etapa
python -m src.recuperacao.comparacao                                        # compara as configurações
```

Os números da comparação estão em [`recuperacao.json`](recuperacao.json).

## Etapas

### 1. Transformação da pergunta

A pergunta do usuário é escrita de um jeito diferente dos comentários. "Quais
reclamações relacionadas à entrega aparecem com maior frequência?" não se parece
com "meu produto está atrasado e ainda não chegou".

Nesta etapa o Gemini reescreve a pergunta como cinco frases curtas que um cliente
escreveria em uma avaliação. Cada frase trata de uma situação diferente dentro do
assunto. O modelo não responde à pergunta, só ajuda a buscar. É uma variação da
técnica HyDE, vista na aula de bancos vetoriais.

As frases ficam em cache, em `cache/frases_de_busca.json`, para a mesma pergunta
não gastar cota da API de novo. O arquivo é versionado, então quem reproduzir o
projeto obtém as mesmas frases para as perguntas deste relatório. Se o modelo não
estiver disponível, a busca segue só com a pergunta original.

### 2. Busca

A pergunta original e as cinco frases são procuradas no índice de significado. As
cinco frases também são procuradas no índice de palavras. São 11 rankings, cada um
com até 20 avaliações de textos diferentes.

A busca por palavras não usa a pergunta original. As palavras de uma pergunta, como
"quais", "frequência" e "clientes", não são as palavras de um comentário, e essa
busca trazia textos sem relação com o assunto, como "Compro com frequência".

### 3. Fusão

Os rankings são combinados com RRF (Reciprocal Rank Fusion). Cada avaliação soma
`1 / (60 + colocação)` em cada ranking em que aparece. Quem aparece bem colocado em
vários rankings sobe na lista final.

### 4. Seleção

Ficam as 10 avaliações mais bem colocadas. Textos iguais ou quase iguais contam
como uma evidência só. O critério para "quase igual" é similaridade de cosseno a
partir de 0,85, valor em que os pares dizem a mesma coisa, como "Demorou muito pra
chegar" e "Demorou demais pra chegar".

Cada evidência guarda:

- o `review_id` e o texto;
- a similaridade com a pergunta ou com as frases de busca;
- em quais rankings apareceu;
- as outras avaliações recuperadas que dizem a mesma coisa.

## Exemplo

Pergunta: **Quais reclamações relacionadas à entrega aparecem com maior frequência?**

Frases de busca geradas:

1. Meu pacote chegou muito atrasado.
2. A caixa veio toda amassada hoje.
3. O entregador nem chamou no portão.
4. Passou do prazo e ninguém avisou.
5. Rastreamento não atualizava nunca o status.

Primeiro resultado de alguns rankings:

| Ranking | Primeiro resultado |
|---|---|
| significado, pergunta original | muitos desencontros nas entregas de produtos |
| significado, frase 1 | ENTREGA MUITO ATRASADA |
| palavras, frase 2 | O produto chegou com a caixa toda amassada! (...) |
| significado, frase 4 | Não recebi nenhuma satisfação. Nem havia acompanhamento. (...) |
| palavras, frase 5 | Vendedor não atualizava a situação da mercadoria (...) |

Evidências selecionadas:

| # | Similaridade | Avaliações | Texto |
|---|---|---|---|
| 1 | 0,73 | 2 | O produto chegou com a caixa toda amassada! Muito amassada mesmo.. nenhum cuidado com o produto! |
| 2 | 0,68 | 1 | Não houve nenhum comunicado sobre o atraso |
| 3 | 0,68 | 1 | Deveriam embalar melhor o produto. A caixa veio toda amassada e vou dar de presente. |
| 4 | 0,75 | 2 | O produto chegou certinho! Porém eu percebi que a caixa vem toda amassada (...) |
| 5 | 0,67 | 1 | A embalagem deixou a desejar, por pouco o produto não foi danificado, a caixa estava toda amassada. |
| 6 | 0,69 | 1 | Não recebi nem uma notificação de atraso |
| 7 | 0,71 | 1 | recomendo. chegou, obrigada mas a caixa, a embalagem amassada e é um presente. |
| 8 | 0,66 | 1 | não cumpre prazo. Não cumpriram prazo de entrega e nem avisaram o atraso. |
| 9 | 0,72 | 4 | Meu produto está atrasado e ainda não chegou |
| 10 | 0,65 | 1 | Bom, porem não otimo. A unica proteção foi a propria caixa do produto, que veio toda amassada. (...) |

## Comparação das configurações

Rodei seis perguntas do enunciado em quatro configurações e contei, nas 60
evidências de cada configuração, duas coisas:

- baixa similaridade: evidências com similaridade abaixo de 0,40, que entraram sem
  ter relação com o assunto;
- repetidas: evidências quase iguais a outra mais bem colocada.

| Configuração | Baixa similaridade | Repetidas |
|---|---|---|
| A. Pergunta original, busca por significado | 0 | 0 |
| B. Pergunta original, significado e palavras | 14 | 0 |
| C. Com frases de busca, sem juntar parecidas | 0 | 5 |
| D. Configuração do projeto | 0 | 0 |

A configuração B mostra por que a busca por palavras não usa a pergunta original:
14 das 60 evidências não tinham relação com o assunto. A configuração C mostra por
que os textos parecidos são agrupados: 5 evidências repetiam outra.

Essas duas medidas não dizem qual configuração traz as evidências mais relevantes.
A diferença entre a busca simples (A) e a configuração do projeto (D) aparece em
perguntas como "problemas com a entrega do pedido":

| Configuração | Primeiras evidências |
|---|---|
| A | Eficiente do pedido a entrega · Nao entrega o pedido no prazo certo · Pedido e entrega sem detalhes |
| D | O produto chegou com a caixa toda amassada! (...) · Apesar de estar dentro do prazo prometido, demorou quase 3 semanas para chegar. (...) · O entregador contratado não permitiu a conferência do produto antes da assinatura do boleto. (...) |

Na busca simples, a primeira evidência é um elogio. A comparação medida da
relevância entre as configurações é feita na etapa de avaliação.

## Reclamação não é o mesmo que nota baixa

Das 10 evidências do exemplo acima, todas são reclamações ligadas à entrega, mas só
4 vêm de avaliações com nota 1 ou 2. As outras 6 têm nota 3, 4 ou 5: o cliente
gostou do produto e reclamou da caixa amassada ou da falta de aviso sobre o atraso.

Um filtro por nota baixa deixaria essas reclamações de fora. A busca pelo texto
encontra a reclamação mesmo quando a nota é alta.

## Limitações

- As frases de busca são uma sugestão do modelo. Em perguntas amplas, um assunto
  pode ficar de fora. No exemplo acima nenhuma frase fala de produto não recebido,
  que é uma das reclamações mais comuns da base.
- O número de avaliações de cada evidência conta só as que foram recuperadas. Não é
  a frequência na base inteira.
- Sem acesso ao modelo, a busca usa só a pergunta original.
