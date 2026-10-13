# Embeddings e indexação

Os índices são gerados por `python -m src.indexacao.indice`. Os números desta
página estão em [`indexacao.json`](indexacao.json).

## Resultado

| | |
|---|---|
| Documentos indexados | 35.957 |
| Modelo de embeddings | `paraphrase-multilingual-MiniLM-L12-v2` |
| Tamanho do vetor | 384 |
| Tempo para gerar os vetores | cerca de 15 segundos com GPU (Mac) e 50 segundos em CPU |
| Tamanho do índice em disco | 55 MB |
| Tempo para carregar os índices | 5 segundos |
| Tempo de uma busca por significado | 10 ms |
| Tempo de uma busca por palavras | 11 ms |

## Embeddings

Cada documento da base vira um vetor de 384 números. Textos com sentido parecido
ficam com vetores parecidos, e é isso que permite buscar por significado.

Escolhi o `paraphrase-multilingual-MiniLM-L12-v2` por três motivos:

- Funciona em português. Ele foi treinado em vários idiomas para reconhecer frases
  com o mesmo sentido.
- Roda no próprio computador, sem custo e sem depender de cota de API. A base tem
  quase 36 mil textos.
- É o modelo usado nas aulas de RAG do curso.

Os vetores são normalizados, e a comparação entre eles é a similaridade de cosseno.
Na etapa de avaliação esse modelo vai ser comparado com outro.

### Comentários em maiúsculas

1.122 documentos da base (3,1%) estão escritos em maiúsculas, como "ENTREGA MUITO
ATRASADA". O modelo de embeddings diferencia maiúsculas de minúsculas, e o vetor
desses textos fica distante do vetor do mesmo texto em minúsculas: a similaridade
mediana entre as duas versões é de 0,49.

Por isso, um texto com 70% ou mais das letras em maiúsculas é convertido para
minúsculas antes de gerar o vetor. O texto guardado na base e mostrado ao usuário
não muda.

Para medir o efeito, busquei 200 desses documentos pelo próprio texto em
minúsculas:

| | Documento encontrado entre os 20 primeiros |
|---|---|
| Vetor gerado com o texto em maiúsculas | 27 de 200 |
| Vetor gerado com o texto em minúsculas | 200 de 200 |

## Índice vetorial

Os vetores ficam em um índice FAISS do tipo `IndexFlatIP`, que faz busca exata:
compara a pergunta com todos os documentos. Com 35.957 vetores essa busca leva 10
ms, então não foi preciso usar um índice aproximado, que é mais rápido mas pode
deixar de fora um documento relevante.

O índice é gravado em `data/indice/vetorial.faiss` e não é versionado, porque pode
ser recriado com o comando acima.

## Índice de palavras

Além da busca por significado, o projeto usa a busca por palavras com BM25. Ela dá
mais peso para documentos que têm as palavras da pergunta, principalmente as
palavras mais raras.

Para essa busca o texto é dividido em palavras com dois ajustes:

- Os acentos são retirados. Os clientes escrevem "ótimo" e "otimo", "não" e "nao",
  e sem esse ajuste as duas formas seriam tratadas como palavras diferentes.
- Palavras muito comuns, como "de", "o" e "para", são retiradas. A palavra "não" é
  mantida, porque "não recebi" e "recebi" têm sentidos opostos.

O índice de palavras é montado na carga, em menos de um segundo, e por isso não é
gravado em disco.

## Conferência

O índice guarda uma assinatura da base de conhecimento, o nome do modelo e a
versão do código que gerou os vetores. Se algum deles mudar, o programa não
carrega o índice antigo e pede para gerar de novo.

Para conferir as duas buscas usei cinco perguntas escritas com palavras diferentes
das que os clientes costumam usar. A tabela mostra o primeiro resultado de cada
busca.

| Pergunta | Busca por significado | Busca por palavras |
|---|---|---|
| problemas com a entrega do pedido | Eficiente do pedido a entrega | Sem problemas na execução do pedido, satisfação. |
| produto chegou com defeito | produto veio com defeito | Um dos bonecos chegou com defeito |
| cliente não recebeu o que comprou | Descaso com o cliente. O produto não foi entregue. | minha filha que comprou e gostou |
| entrega mais rápida que o esperado | mais rápido que o esperado | Excelente produto, entrega mais rápida do que o esperado |
| vendedor não respondeu às mensagens | Produto não foi entregue. Sem resposta das lojas lannister (...) | A entrega demorou por conta de um problema com os correios (...) |

O que esses resultados mostram:

- A busca por significado encontra frases com outras palavras. Em "cliente não
  recebeu o que comprou" ela trouxe "O produto não foi entregue", enquanto a busca
  por palavras trouxe um comentário que só tem a palavra "comprou".
- A busca por palavras acerta quando o termo exato importa. Em "vendedor não
  respondeu às mensagens", o segundo resultado dela foi "Não respondeu nenhum de
  meus e-mails".
- Em "problemas com a entrega do pedido" as duas trouxeram elogios em primeiro
  lugar. A pergunta fala de problema, mas os comentários mais parecidos falam de
  entrega em geral. Esse caso vai ser tratado na etapa de recuperação, com a
  reescrita da pergunta.
- Os primeiros resultados muitas vezes são o mesmo texto repetido, de clientes
  diferentes. A etapa de recuperação vai agrupar textos iguais.
