"""
Julgamento automático usado na avaliação.

Duas medidas da avaliação não saem só de contas, e por isso são julgadas por um
modelo de linguagem:

    relevância    a evidência recuperada trata do assunto da pergunta?
    sustentação   a conclusão está apoiada nas evidências que ela cita?

Os julgamentos ficam em cache (cache/julgamentos.json). Uma amostra deles foi
conferida à mão, e o resultado está em reports/avaliacao.md.
"""

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from config import settings
from src import cache_llm, modelo

CACHE = "julgamentos"

INSTRUCAO_RELEVANCIA = """Você avalia um sistema de busca de avaliações de clientes de uma loja online.

Para a pergunta informada, diga se cada avaliação numerada é relevante. Uma avaliação \
é relevante quando trata do assunto da pergunta e ajuda a respondê-la.

Regras:
- Se a pergunta é sobre reclamações ou problemas, um elogio sobre o mesmo assunto não é relevante.
- Se a pergunta é sobre elogios, uma reclamação sobre o mesmo assunto não é relevante.
- Se a pergunta é sobre algo específico, a avaliação precisa mencionar esse assunto.
- Julgue cada avaliação separadamente e devolva uma decisão para cada número."""

INSTRUCAO_SUSTENTACAO = """Você confere se as conclusões de uma resposta estão apoiadas em avaliações de clientes.

Para cada conclusão numerada, leia as avaliações citadas logo abaixo dela e diga se a \
conclusão está sustentada.

Uma conclusão está sustentada quando o que ela afirma está dito, de forma direta, em \
pelo menos uma das avaliações citadas. Não está sustentada quando acrescenta um fato \
que nenhuma avaliação citada traz, como uma data, um motivo ou um produto que não \
aparece no texto.

Devolva uma decisão para cada número."""

class Decisao(BaseModel):
    numero: int
    sim: bool = Field(description="Verdadeiro se a avaliação é relevante, ou se a conclusão está sustentada")


class Decisoes(BaseModel):
    decisoes: list[Decisao]


def _consultar(instrucao: str, conteudo: str, formato):
    """Chama o modelo com cache. A chave muda se a instrução ou o conteúdo mudar."""
    chave = cache_llm.chave(settings.MODELO_GERACAO, instrucao, conteudo)
    cache = cache_llm.ler(CACHE)
    if chave not in cache:
        prompt = ChatPromptTemplate.from_messages([("system", instrucao), ("human", "{conteudo}")])
        saida = modelo.chamar(prompt | modelo.criar_modelo().with_structured_output(formato), {"conteudo": conteudo})
        cache = cache_llm.ler(CACHE)
        cache[chave] = saida.model_dump()
        cache_llm.gravar(CACHE, cache)
    return formato(**cache[chave])


def julgar_relevancia(pergunta: str, textos: list[str]) -> list[bool]:
    """Para cada texto, se ele é relevante para a pergunta. Sem decisão conta como não relevante."""
    linhas = "\n".join(f"[{n}] {t}" for n, t in enumerate(textos, start=1))
    saida = _consultar(INSTRUCAO_RELEVANCIA, f"Pergunta: {pergunta}\n\nAvaliações:\n{linhas}", Decisoes)
    decisoes = {d.numero: d.sim for d in saida.decisoes}
    return [decisoes.get(n, False) for n in range(1, len(textos) + 1)]


def julgar_sustentacao(conclusoes: list[tuple[str, list[str]]]) -> list[bool]:
    """Para cada (conclusão, avaliações citadas), se a conclusão está sustentada."""
    blocos = []
    for n, (conclusao, citadas) in enumerate(conclusoes, start=1):
        avaliacoes = "\n".join(f"  - {t}" for t in citadas)
        blocos.append(f"[{n}] Conclusão: {conclusao}\nAvaliações citadas:\n{avaliacoes}")
    saida = _consultar(INSTRUCAO_SUSTENTACAO, "\n\n".join(blocos), Decisoes)
    decisoes = {d.numero: d.sim for d in saida.decisoes}
    return [decisoes.get(n, False) for n in range(1, len(conclusoes) + 1)]
