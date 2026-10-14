# Avaliação da solução

A avaliação usa perguntas novas, que não foram usadas nos passos anteriores para
definir limites nem para ajustar a instrução do modelo. As perguntas estão em
[`src/avaliacao/perguntas.py`](../src/avaliacao/perguntas.py).

```bash
python -m src.avaliacao.avaliar

# inclui a comparação com outro modelo de embeddings (baixa 1,1 GB na primeira vez)
MODELO_COMPARADO=sentence-transformers/paraphrase-multilingual-mpnet-base-v2 python -m src.avaliacao.avaliar
```

Os números estão em [`avaliacao.json`](avaliacao.json).

## Critérios

Os critérios mínimos foram definidos em `config/settings.py` antes de rodar a
avaliação. Se algum não for atingido, o programa termina com erro.

| Critério | Mínimo | Medido | Atingido |
|---|---|---|---|
| Precisão das evidências | 0,70 | 0,75 | sim |
| Fidelidade das conclusões | 0,90 | 0,99 | sim |
| Recusa correta | 0,90 | 0,90 | sim |
| Recusa indevida (máximo) | 0,10 | 0,00 | sim |

A recusa correta ficou exatamente no mínimo. As duas falhas estão descritas mais
abaixo.

## Como foi medido

Duas medidas não saem só de contas: se uma evidência trata do assunto da pergunta,
e se uma conclusão está apoiada nas evidências que cita. Para essas duas usei o
Gemini como juiz, com instruções fixas que estão em
[`src/avaliacao/juiz.py`](../src/avaliacao/juiz.py).

Para saber se o juiz é confiável, conferi à mão uma amostra dos julgamentos. O
arquivo [`conferencia_manual.json`](conferencia_manual.json) tem os itens e as duas
decisões.

| Julgamento | Itens conferidos | Concordância |
|---|---|---|
| Relevância da evidência | 30 | 28 |
| Sustentação da conclusão | 16 | 16 |

Nos dois casos de discordância, o juiz foi mais rigoroso: para a pergunta sobre
produto com defeito, ele considerou não relevantes "Produto chegou com risco e
manchado" e "Muitas rebarbas na hélice do produto", que eu consideraria relevantes.
Por isso a precisão medida pode estar um pouco abaixo da real.

A avaliação não tem medida de recall por documento. Nesta base muitas avaliações
dizem a mesma coisa, então não existe uma única avaliação correta para cada
pergunta.

## 1. Precisão das evidências

Vinte perguntas que a base responde. Para cada uma, o juiz diz quais das evidências
recuperadas tratam do assunto.

| Configuração | Evidências relevantes | Precisão |
|---|---|---|
| Busca simples (pergunta original, só por significado) | 99 de 184 | 0,54 |
| Configuração do projeto | 150 de 200 | 0,75 |

A configuração do projeto foi melhor em 15 perguntas, igual em 1 e pior em 4. As
maiores diferenças aparecem quando a pergunta usa palavras que os clientes não
usam:

| Pergunta | Busca simples | Projeto |
|---|---|---|
| O que os clientes relatam sobre pedidos entregues em partes? | 0 de 10 | 9 de 10 |
| O que os clientes dizem sobre a retirada do produto nos Correios? | 0 de 10 | 8 de 10 |
| O que os clientes reclamam sobre o atendimento da loja? | 4 de 10 | 10 de 10 |

Duas das perguntas em que o projeto foi pior:

| Pergunta | Busca simples | Projeto |
|---|---|---|
| Quais motivos levam os clientes a pedir o dinheiro de volta? | 8 de 10 | 4 de 10 |
| Os clientes reclamam de cobrança indevida ou problemas no pagamento? | 8 de 10 | 6 de 10 |

Na primeira, as frases de busca descrevem os motivos, como produto quebrado e
tamanho errado, e a busca traz avaliações sobre esses problemas que não falam em
pedir o dinheiro de volta.

## 2. Fidelidade

Para as mesmas vinte perguntas, o juiz confere se cada conclusão da resposta está
apoiada nas evidências que ela cita.

| | |
|---|---|
| Conclusões geradas | 75 |
| Conclusões sustentadas | 74 |
| Evidências relevantes que o modelo usou | 141 de 150 |
| Evidências fora do assunto que o modelo citou | 4 de 50 |

O modelo usou quase todas as evidências relevantes e deixou de fora 46 das 50 que
não tratavam do assunto.

A conclusão não sustentada foi "Os clientes pedem o dinheiro de volta porque o
produto chegou quebrado". As duas avaliações citadas dizem que o produto chegou
quebrado, mas nenhuma fala em pedir o dinheiro de volta. O modelo juntou o texto
das avaliações com o assunto da pergunta.

## 3. Recusa

| Grupo | Perguntas | Resultado |
|---|---|---|
| Fora do escopo | 10 | 10 recusadas |
| Assunto que não existe na base | 10 | 8 recusadas |
| Respondíveis | 20 | 19 respondidas, 1 parcial, nenhuma recusada |

As duas perguntas que deveriam ter sido recusadas e não foram:

| Pergunta | O que o sistema respondeu | O que aconteceu |
|---|---|---|
| Os clientes reclamam do seguro contra roubo oferecido na compra? | "Os clientes afirmam que nunca houve problemas com o seguro", com aviso de pouca evidência | A avaliação citada diz "Seguro ... nunca houve problemas". A palavra "seguro" está no sentido de confiável, e o modelo leu como seguro do produto |
| O que os clientes acham do vale-presente da loja? | Problemas com restituição por voucher, com aviso de resposta parcial | A base tem avaliações sobre voucher de reembolso, que é um assunto próximo, mas não é vale-presente |

Nos dois casos a resposta saiu com aviso, mas o correto era recusar.

A primeira conferência, que compara a pergunta com a base antes de chamar o modelo,
não barrou nenhuma das 10 perguntas fora do escopo. Todas tinham similaridade entre
0,54 e 0,75, acima do limite de 0,50. As dez foram recusadas pelo modelo. Essa
conferência só serve para perguntas muito distantes da base, e a recusa depende do
modelo.

## 4. Elogios genéricos

Na preparação da base, 6.294 avaliações só com elogio genérico ficaram de fora.
Para saber o efeito dessa decisão, comparei a busca simples em seis perguntas sobre
elogios, com a base do projeto e com esses elogios de volta.

| Base | Evidências relevantes | Precisão |
|---|---|---|
| Base do projeto | 47 de 60 | 0,78 |
| Com os elogios genéricos de volta | 45 de 60 | 0,75 |

Com os elogios de volta, 3 das 60 evidências passaram a ser textos genéricos, como
"Satisfeita com a compra, recomendo". O efeito existe, mas é pequeno. A exclusão
não é o que sustenta a qualidade da busca.

## 5. Temas

Na análise exploratória medi os temas mais citados na base. Aqui confiro se eles
aparecem nas respostas a duas perguntas amplas: "Quais são os principais problemas
relatados pelos clientes?" e "Quais problemas são relatados por clientes
insatisfeitos?".

| Tema | % dos comentários | Aparece nas respostas |
|---|---|---|
| Entrega e prazo | 45,8% | sim |
| Atendimento e vendedor | 10,6% | sim |
| Qualidade e defeito | 9,5% | sim |
| Não recebeu o produto | 8,0% | sim |
| Troca e devolução | 3,8% | não |
| Preço | 3,4% | não |
| Embalagem | 3,3% | não |
| Produto errado ou diferente | 3,0% | sim |
| Item faltando | 1,6% | não |

Os quatro temas mais citados aparecem. Os temas menores podem ficar de fora, porque
cada resposta usa 10 evidências. Para um tema menor, o caminho é fazer uma pergunta
específica sobre ele.

## 6. Tempo

Tempo de cada etapa, com as chamadas ao modelo feitas sem cache:

| Etapa | Segundos |
|---|---|
| Transformação da pergunta | 1,1 |
| Busca, fusão e seleção | 0,1 |
| Geração da resposta | 1,2 |
| Total | cerca de 2,5 |

Quase todo o tempo é das duas chamadas ao modelo, e por isso o total varia de uma
rodada para outra. Nas rodadas que fiz ficou entre 2,4 e 3,2 segundos.

## 7. Modelo de embeddings

Comparei o modelo do projeto com a versão maior da mesma família. A medida é a
precisão da busca por significado com a pergunta original, nas mesmas vinte
perguntas, com as 10 primeiras avaliações de texto diferente.

| Modelo | Tamanho do vetor | Tempo para gerar os vetores | Evidências relevantes | Precisão |
|---|---|---|---|---|
| `paraphrase-multilingual-MiniLM-L12-v2` (projeto) | 384 | 14 s | 115 de 200 | 0,58 |
| `paraphrase-multilingual-mpnet-base-v2` | 768 | 40 s | 125 de 200 | 0,63 |

O modelo maior traz 10 evidências relevantes a mais em 200. Mantive o modelo do
projeto por três motivos:

- o ganho é menor que o da transformação da pergunta, que leva a precisão de 0,54
  para 0,75 com o modelo atual;
- os limites de similaridade do projeto (0,80 para textos iguais e 0,50 para a
  primeira conferência de recusa) foram medidos com o modelo atual, e teriam de
  ser medidos de novo;
- o modelo maior ocupa 1,1 GB e leva quase três vezes mais tempo para indexar.

Trocar o modelo é uma evolução possível. A comparação aqui foi só na busca simples.
Não medi o modelo maior na configuração completa do projeto.

A precisão da busca simples nesta tabela (0,58) é diferente da medida 1 (0,54)
porque lá os textos que dizem a mesma coisa são agrupados, e sobram menos
evidências por pergunta.

## O que a avaliação mostra

- A transformação da pergunta melhora a busca: a precisão passa de 0,54 para 0,75.
- As conclusões seguem o texto das evidências: 74 de 75 estão sustentadas.
- O sistema recusa bem perguntas fora do escopo, e erra quando a base tem um texto
  que parece tratar do assunto, como no caso do seguro.
- A precisão de 0,75 quer dizer que, em média, uma em cada quatro evidências
  recuperadas não trata do assunto. A geração corrige a maior parte disso: das 50
  evidências fora do assunto, o modelo citou 4.

## Limitações da avaliação

- São 20 perguntas respondíveis e 20 sem resposta. O conjunto é pequeno, e os
  números mudam alguns pontos com uma pergunta a mais ou a menos.
- O juiz é o mesmo modelo que gera as respostas. A conferência manual reduz esse
  risco, mas cobriu só uma amostra.
- A avaliação mede se as evidências e as conclusões estão corretas. Ela não mede se
  a resposta cobre tudo o que a base tem sobre o assunto.
