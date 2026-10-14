# Exemplos de perguntas e respostas

Respostas do sistema para as cinco perguntas da seção "Exemplos de Exploração" do
enunciado, para uma pergunta respondida só em parte e para duas perguntas recusadas.

As respostas das cinco perguntas do enunciado estão em [`geracao.json`](geracao.json)
e são geradas por `python -m src.geracao.exemplos`. As outras podem ser refeitas na
interface ou com `python -m src.geracao.responder "pergunta"`. As chamadas ao modelo
ficam em cache, e por isso as respostas se repetem.

A coluna "Avaliações na base" conta as avaliações com texto igual ou muito parecido
com as evidências do ponto. É um mínimo, e não o total de avaliações sobre o tema.
Os pontos estão ordenados por essa coluna.

Em cada pergunta aparecem só as evidências citadas na resposta.

## Perguntas do enunciado

### 1. Quais são os principais problemas relatados pelos clientes em suas avaliações?

| Conclusão | Evidências | Avaliações na base |
|---|---|---|
| O produto veio com defeito de fábrica ou avariado. | [6] [9] | 34 |
| A entrega atrasou. | [3] [5] | 33 |
| A qualidade do material do produto é ruim. | [7] [8] | 27 |
| O produto foi entregue no tamanho ou dimensões erradas. | [4] [9] [10] | 26 |
| O atendimento é péssimo e sem canais adequados de suporte. | [1] [2] [3] | 11 |
| O produto não chegou na data prevista. | [3] [10] | 2 |

| # | Texto | `review_id` |
|---|---|---|
| 1 | Pessimo atendimento, sem canal de reclamação fornecedor | `10b73c782535c2ca6f5df1188f3785a6` |
| 2 | Péssimo atendimento | `8c6d55fb54f18ddd012b1fefecfc7292` |
| 3 | Péssimo atendimento, não entregam no prazo, sem qualquer tipo de satisfação ao cliente. Horrível! | `0b9740c80aede334780599d37387228c` |
| 4 | Não recomendo. O produto foi entregue no tamanho errado! | `5849ab48269292920477dbe2cf734707` |
| 5 | A entrega atrasou | `65e3d04aef73660b0b2145ef3d5762cd` |
| 6 | Infelizmente o produto veio com defeito de fábrica e já acionei a devolução do produto | `6e275c31eec908a4d12d91974e34408d` |
| 7 | Produto ruim, furações não bate e qualidade do material e péssima | `07b94e4e0f7e0687af02e144c510517c` |
| 8 | Qualidade. O material não é muito bom. | `25b1d540e68cadfeeb408d87ad6b12b3` |
| 9 | O produto veio com dimensões erradas e avariado. | `95d9b32ceb14e27ec00467d1792b457e` |
| 10 | não recomendado. O tapete não chegou na data prevista. e veio errado o tamanho que encomendei. | `b2bf9b39b2838c18913129075bd6e133` |

### 2. O que os clientes relatam sobre problemas relacionados à entrega?

| Conclusão | Evidências | Avaliações na base |
|---|---|---|
| Os clientes relatam que receberam o produto com a caixa ou o pacote amassado. | [1] [6] | 77 |
| Os clientes relatam que a entrega demorou muito ou está muito atrasada. | [3] [9] | 72 |
| Os clientes relatam que o produto chegou mal embalado ou com a caixa quase aberta. | [1] [4] | 12 |
| Os clientes relatam que receberam a caixa aberta. | [2] [5] [8] | 5 |
| Os clientes relatam que receberam o produto incompleto, faltando item. | [10] | 4 |
| Os clientes relatam que o pacote veio rasgado. | [7] | 1 |

| # | Texto | `review_id` |
|---|---|---|
| 1 | Nao gostei do pacote, veio todo amassado, mal embalado | `27b6c874b2a73a28a86101dd925aea70` |
| 2 | caixa veio aberta! | `86eef897f1e35a439802645adcdfad4c` |
| 3 | Demorou muito para chegar. | `e3560b1fd3dd7d96fb0be8962bd15476` |
| 4 | Produto chegou, mas mal embalado, caixa quase aberta. | `7eb528b3f5718e82b6fcf45eaa88e2f1` |
| 5 | Entregaram antes do prazo, porém, recebemos uma caixa aberta. | `c4a3d03959615200eeef02944ac989a1` |
| 6 | Recebi o produto porém veio amassado | `aab5578d9c3b538a382064790d63a8c4` |
| 7 | O pacote veio rasgado | `5d858cb57b57ca49764f5881d69f6e02` |
| 8 | Só nao entendi porque a caixa veio aberta. Mais fora isso tá perfeito veio tudo certinho. | `5e3d47c3831035a159beb6207412933f` |
| 9 | Não recebi a mercadoria...ESTÁ MUITO ATRASADA A ENTREGA... | `1a6763b35ea712ac4530a70a61898a6c` |
| 10 | Recebi o produto incompleto, faltou 01 item! | `0afdaef42f4cef6492069412f42443d3` |

### 3. Quais aspectos da experiência de compra são mais elogiados pelos clientes?

| Conclusão | Evidências | Avaliações na base |
|---|---|---|
| A entrega foi rápida. | [1] [10] | 113 |
| A compra foi fácil e o site é recomendado. | [3] [4] | 11 |
| O atendimento foi considerado ótimo quando foi preciso tirar dúvidas. | [5] | 8 |
| As expectativas foram atendidas. | [8] [9] | 7 |
| O atendimento no site foi bom e de fácil acesso. | [6] | 6 |

| # | Texto | `review_id` |
|---|---|---|
| 1 | A entrega foi muito rápida. | `769f489559ab6a993674da69a2dcc36d` |
| 3 | Bem embalado, facil de usar. | `80ae9cd409fdc1622dcc80f44398f86c` |
| 4 | compra fácil e site recomendado | `6b8afef2db830a63fe099a319b3198a0` |
| 5 | Pedido entregue no prazo e ótimo atendimento quando precisei tirar duvidas | `659dfaa0ac8a6ebacb2f1b30d991aebc` |
| 6 | Bom atendimento no site, de fácil acesso Muito bom | `e38ef8bc1a1c625b3c93686578133558` |
| 8 | Todas as expectativas foram atendidas. | `ad56efa0c028e233603c66f17fb57216` |
| 9 | Atingiu todas as expectativas.Parabéns | `24ad47a692fb30418e0416fc6c6aaca2` |
| 10 | Preço compatível e entrega rápida! Valeu a pena. | `e346daea3db3095a261b9b6b098c2824` |

### 4. Quais padrões podem ser identificados nas avaliações de clientes insatisfeitos?

| Conclusão | Evidências | Avaliações na base |
|---|---|---|
| Os clientes relatam que o produto é de péssima qualidade e acabamento. | [3] [8] | 57 |
| Há reclamações de que o produto chegou com defeito. | [10] | 46 |
| Clientes consideram o preço caro associado à péssima qualidade. | [3] | 14 |
| Houve insatisfação com a falta de uma embalagem adequada, com os itens jogados na caixa. | [1] [5] | 13 |
| Clientes apontam que faltou produto na caixa entregue. | [4] | 4 |
| Alguns clientes reclamam que a entrega demorou, considerando o prazo longo demais. | [6] | 4 |

| # | Texto | `review_id` |
|---|---|---|
| 1 | Bom. Lindo, só faltou uma caixa bonita. | `fbe2d06d09571b61ec2064c7ae49e275` |
| 3 | Caro e de péssima qualidade. | `68160ba199e9b65869c10aca2d695704` |
| 4 | faltou produto na caixa. foi entregue uma caixa lacrada, mas somente 1 produto estava dentro da caixa. | `4212c52fdd32a8361ba2d655f3811fb3` |
| 5 | Porém faltou uma embalagem descente! Vieram jogadas dentro da caixa de papelão | `20f4e2a3123d0f8fc6bd514727eba788` |
| 6 | Apesar de estar dentro do prazo prometido, demorou quase 3 semanas para chegar. Prazo muito além do praticado no mercado. | `71d3388f71d75c44554318cfd5c4e34c` |
| 8 | Produto de péssima qualidade e acabamento. | `074c39cb5e90578eaeb560e6f632ae1e` |
| 10 | Minha queixa é que o produto chegou com defeito. | `390c78a5aa8b87a0e74a827fd5736078` |

### 5. Quais avaliações sustentam a conclusão de que existem problemas recorrentes relacionados ao prazo de entrega?

| Conclusão | Evidências | Avaliações na base |
|---|---|---|
| O produto demorou demais para chegar. | [2] [5] [10] | 39 |
| O prazo de entrega não foi cumprido ou a encomenda ainda não chegou. | [3] | 33 |
| A entrega atrasou. | [9] | 32 |
| A entrega atrasou muito. | [6] | 16 |

| # | Texto | `review_id` |
|---|---|---|
| 2 | achei que demorou demais a entrega pelo tempo da compra. | `82a25968fb6712fc4dc1d9f76b59494e` |
| 3 | Prazo de entrega não foi cumprido. Encomenda ainda não chegou. | `6bb17113a061e2e8bb65b706278b4d75` |
| 5 | Demorou demais pra entregar | `022b63030708e5fd241fca5dde29708b` |
| 6 | atrasou muito | `c18cc462b5b75bd723af0f25168cbb77` |
| 9 | A entrega atrasou | `65e3d04aef73660b0b2145ef3d5762cd` |
| 10 | bom dia não sei se foi os correios que atrasou mas o produto demorou demais para chegar | `e4758a5d4173c04ce04772bddd572ce8` |

## Pergunta respondida em parte

### O que os clientes dizem sobre a entrega e sobre o pagamento por Pix?

O sistema respondeu só sobre a entrega e mostrou o aviso: "As avaliações não
respondem a uma parte da pergunta. As avaliações não mencionam o pagamento por Pix."

| Conclusão | Evidências | Avaliações na base |
|---|---|---|
| Os clientes receberam os produtos antes do prazo ou rapidamente. | [2] [3] [4] [9] | 730 |
| Houve reclamações sobre atrasos e demora na entrega. | [1] [5] | 35 |
| Houve cobrança de frete, mas o cliente precisou retirar na agência dos Correios. | [7] | 5 |

| # | Texto | `review_id` |
|---|---|---|
| 1 | A entrega atrasou demais, eu já estava cancelando. | `d6d1e908191ce44ad6b1625fea2dd4bd` |
| 2 | Recebi dentro do prazo, rápido e tudo certinho. | `417b5dd61150cabf1b015457075baa28` |
| 3 | Adorei. Chegou bem antes do que o prazo de entrega. | `6cfab8b004bedd946de33cea0a17173b` |
| 4 | Recebido rapidamente e sem problemas | `95506b858fda155eb88ea7278040a44e` |
| 5 | Demora na entrega e ainda atrasou. | `6964442cd4b5a5a0c5bbfa8d6fb914ef` |
| 7 | Paguei frete em vão. Paguei frete para que o produto fosse entregue e tive que retirar na agência do Correio! | `5a4502a7144cd0fabb30da633bd92d6a` |
| 9 | parabens chegou em tempo abel | `b977cc1b1a011d1be2de85e4af5b6bcf` |

## Perguntas recusadas

| Pergunta | Similaridade com a base | Onde foi recusada | O que o usuário vê |
|---|---|---|---|
| Qual é a capital da França? | 0,36 | Na primeira conferência, sem chamar o modelo | Não encontrei na base avaliações relacionadas a essa pergunta. A base tem comentários de clientes sobre suas compras: produto, entrega, atendimento e pagamento. |
| O que os clientes acham do pagamento por Pix? | 0,61 | Pelo modelo, depois de ver as evidências | As avaliações encontradas não permitem responder a essa pergunta. As avaliações fornecidas não mencionam o pagamento por Pix. |
