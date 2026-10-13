"""
Construção do contexto enviado ao modelo de linguagem.

O contexto é a lista numerada das evidências recuperadas. Cada linha tem o
número da evidência, em quantas avaliações da base aquele texto se repete e o
texto do cliente.

As avaliações ficam entre duas marcas, e a instrução do modelo diz que tudo o
que está entre elas é texto de cliente, a ser analisado e nunca obedecido. Um
comentário como "favor desconsiderar a primeira avaliação" é legítimo, mas lido
como instrução poderia mudar o comportamento do modelo.
"""

ABRE = "<avaliacoes>"
FECHA = "</avaliacoes>"


def _texto_seguro(texto: str) -> str:
    """Impede que o texto do cliente feche a marcação ou abra outra."""
    return texto.replace("<", "(").replace(">", ")")


def montar_contexto(evidencias) -> str:
    linhas = []
    for numero, e in enumerate(evidencias, start=1):
        repete = "1 avaliação" if e.avaliacoes_na_base == 1 else f"{e.avaliacoes_na_base} avaliações"
        linhas.append(f"[{numero}] (dito em {repete}) {_texto_seguro(e.texto)}")
    return "\n".join([ABRE, *linhas, FECHA])
