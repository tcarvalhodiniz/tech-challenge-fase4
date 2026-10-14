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

Ficam as 10 avaliações mais bem colocadas. Textos que dizem a mesma coisa contam
como uma evidência só. O critério é similaridade de cosseno a partir de 0,80.

Esse limite foi escolhido lendo amostras por faixa de similaridade. Acima de 0,80
os textos falam do mesmo assunto com a mesma opinião, como "Demorou muito pra
chegar" e "Achei que demora muita pra entregar". Entre 0,70 e 0,80 já aparecem
textos de sentido oposto: para "Produto de péssima qualidade" aparece "Produto de
Qualidade".

Cada evidência guarda:

- o `review_id` e o texto;
- a similaridade com a pergunta ou com as frases de busca;
- em quais rankings apareceu;
- quantas avaliações da base inteira dizem a mesma coisa que ela.

## Exemplo

Pergunta: **Quais reclamações relacionadas à entrega aparecem com maior frequência?**

Frases de busca geradas:

1. Meu pacote chegou muito atrasado.
2. A caixa veio toda amassada hoje.
3. O entregador nem chamou no portão.
4. Passou do prazo e ninguém avisou.
5. Rastreamento não atualizava nunca o status.

Evidências selecionadas:

| # | Similaridade | Avaliações na base | Texto |
|---|---|---|---|
| 1 | 0,73 | 12 | O produto chegou com a caixa toda amassada! Muito amassada mesmo.. nenhum cuidado com o produto! |
| 2 | 0,68 | 1 | Não houve nenhum comunicado sobre o atraso |
| 3 | 0,68 | 3 | Deveriam embalar melhor o produto. A caixa veio toda amassada e vou dar de presente. |
| 4 | 0,69 | 3 | Não recebi nem uma notificação de atraso |
| 5 | 0,72 | 69 | Meu produto está atrasado e ainda não chegou |
| 6 | 0,66 | 2 | não cumpre prazo. Não cumpriram prazo de entrega e nem avisaram o atraso. |
| 7 | 0,65 | 1 | Bom, porem não otimo. A unica proteção foi a propria caixa do produto, que veio toda amassada. (...) |
| 8 | 0,65 | 24 | O prazo já passou e nada do produto chegar. |
| 9 | 0,66 | 1 | muitos desencontros nas entregas de produtos |
| 10 | 0,76 | 35 | ENTREGA MUITO ATRASADA |

A coluna "Avaliações na base" mostra quantas avaliações da base inteira dizem a
mesma coisa que a evidência. Ela é usada na geração da resposta para indicar o peso
de cada conclusão.

## Comparação das configurações

Rodei seis perguntas do enunciado em quatro configurações e contei, nas 60
evidências de cada configuração, duas coisas:

- baixa similaridade: evidências com similaridade abaixo de 0,40, que entraram sem
  ter relação com o assunto;
- repetidas: evidências que dizem o mesmo que outra mais bem colocada.

| Configuração | Baixa similaridade | Repetidas |
|---|---|---|
| A. Pergunta original, busca por significado | 0 | 0 |
| B. Pergunta original, significado e palavras | 16 | 0 |
| C. Com frases de busca, sem juntar parecidas | 0 | 20 |
| D. Configuração do projeto | 0 | 0 |

A configuração B mostra por que a busca por palavras não usa a pergunta original:
16 das 60 evidências não tinham relação com o assunto. A configuração C mostra por
que os textos parecidos são agrupados: 20 das 60 evidências repetiam outra.

Essas duas medidas não dizem qual configuração traz as evidências mais relevantes.
A diferença entre a busca simples (A) e a configuração do projeto (D) aparece em
perguntas como "problemas com a entrega do pedido": na busca simples, a primeira
evidência é um elogio ("Eficiente do pedido a entrega"). Na [avaliação](avaliacao.md),
a precisão das evidências foi de 0,54 na busca simples e de 0,75 na configuração do
projeto.

## Reclamação não é o mesmo que nota baixa

Nas quatro perguntas sobre problemas, 15 das 40 evidências vêm de avaliações com
nota 3, 4 ou 5. São clientes que gostaram do produto e reclamaram de um ponto
específico, como em "Só nao entendi porque a caixa veio aberta. Mais fora isso tá
perfeito veio tudo certinho", de uma avaliação com nota 5.

Um filtro por nota baixa deixaria essas reclamações de fora. A busca pelo texto
encontra a reclamação mesmo quando a nota é alta. A nota foi usada aqui só para
essa conferência. Ela não está na base de conhecimento e a busca não usa a nota.

## Limitações

- As frases de busca são uma sugestão do modelo. Em perguntas amplas, um assunto
  pode ficar de fora.
- Sem acesso ao modelo, a busca usa só a pergunta original.
