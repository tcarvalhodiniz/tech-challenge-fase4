"""
Funções de texto usadas na análise exploratória e na base de conhecimento.

A normalização usa o módulo `re` do Python, via `map`, e não os métodos de
`Series.str`: no pandas 3 eles rodam no PyArrow, em que `\\w` não reconhece
letras acentuadas.
"""

import re
import unicodedata

# Palavras que expressam satisfação sem dizer com o quê. Um comentário formado
# só por elas ("muito bom", "recomendo", "ótimo produto") não ajuda a responder
# nenhuma pergunta sobre a experiência de compra. A lista é conservadora: na
# dúvida a palavra fica de fora, e o comentário é mantido.
VOCAB_GENERICO = set("""
bom boa bons boas muito muita mto mt ótimo ótima otimo otima excelente
excelentes recomendo recomendado recomendaria super ok okay tudo certo
certinho gostei amei adorei legal perfeito perfeita top show nota dez
parabéns parabens satisfeito satisfeita obrigado obrigada grato grata
produto produtos compra loja maravilhoso maravilhosa lindo linda bem beleza
sim aprovado aprovei bastante sem comentário comentários comentario
comentarios nada declarar todos todas
e o a os as de do da dos das um uma em no na com para pelo pela eu estou
fiquei foi é está sou
""".split())

# Padrões estreitos de propósito, para não confundir com número de pedido ou
# data: o celular exige DDD seguido de 9, e o CPF candidato só conta se o
# dígito verificador fechar.
DADOS_PESSOAIS = {
    "e-mail": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "celular": r"(?<!\d)\(?\d{2}\)?[\s-]?9\d{4}[\s-]?\d{4}(?!\d)",
    "link": r"https?://\S+|www\.\S+",
}
CANDIDATO_CPF = r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)"

MASCARAS = {"e-mail": "[EMAIL]", "celular": "[CELULAR]", "link": "[LINK]"}


def tokens(texto: str) -> list[str]:
    return re.findall(r"\w+", texto.lower())


def normalizar(texto: str) -> str:
    """Minúsculas, sem pontuação e com espaços simples. Só para comparar textos."""
    return " ".join(tokens(texto))


def sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def eh_generico(texto: str) -> bool:
    """Verdadeiro quando todas as palavras são genéricas ou números soltos ("10", "nota 1000")."""
    tk = tokens(texto)
    return len(tk) > 0 and all(t in VOCAB_GENERICO or t.isdigit() for t in tk)


def cpf_valido(candidato: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", candidato)]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for pos in (9, 10):
        resto = sum(d[i] * (pos + 1 - i) for i in range(pos)) % 11
        if d[pos] != (0 if resto < 2 else 11 - resto):
            return False
    return True


def tem_cpf(texto: str) -> bool:
    return any(cpf_valido(c) for c in re.findall(CANDIDATO_CPF, texto))


def tem_dado_pessoal(texto: str) -> bool:
    return tem_cpf(texto) or any(re.search(p, texto) for p in DADOS_PESSOAIS.values())


def limpar(texto: str) -> str:
    """Troca quebras de linha e espaços repetidos por um espaço. O resto fica como o cliente escreveu."""
    return re.sub(r"\s+", " ", texto).strip()


def mascarar(texto: str) -> str:
    """Substitui e-mail, celular, link e CPF por marcadores."""
    for nome, padrao in DADOS_PESSOAIS.items():
        texto = re.sub(padrao, MASCARAS[nome], texto)
    return re.sub(CANDIDATO_CPF, lambda m: "[CPF]" if cpf_valido(m.group()) else m.group(), texto)


def montar_texto(titulo: str, comentario: str) -> str:
    """Junta título e comentário em um texto só.

    O título fica de fora quando já está contido no comentário, para não
    repetir a mesma frase ("MT lindo. MT lindo").
    """
    titulo, comentario = limpar(titulo or ""), limpar(comentario or "")
    if not comentario:
        return titulo
    # A comparação ignora acentos: "Entrega rapida" está contido em "Entrega rápida e ..."
    palavras_titulo = sem_acentos(normalizar(titulo))
    if not palavras_titulo or f" {palavras_titulo} " in f" {sem_acentos(normalizar(comentario))} ":
        return comentario
    separador = " " if titulo[-1] in ".!?:;" else ". "
    return titulo + separador + comentario
