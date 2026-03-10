# Importa a função 'escape' da biblioteca padrão de XML do Python.
# É a maneira correta e mais segura de escapar caracteres XML.
from xml.sax.saxutils import escape as escape_xml


def preparar_campo(valor, limite=255):
    """
    Trunca e limpa um valor para uso seguro no XML.

    Args:
        valor (any): Texto a ser processado.
        limite (int): Número máximo de caracteres.

    Returns:
        str: O valor processado, truncado e sem espaços nas pontas.
    """
    # Em Python, 'if not valor:' checa se o valor é None, uma string vazia, 0, etc.
    if not valor:
        return ""

    # Converte para string, fatia até o limite e remove espaços em branco do início e fim.
    return str(valor)[:limite].strip()


def campo_xml(valor, limite=255):
    """
    Prepara e escapa um campo XML com limite de caracteres.

    Args:
        valor (any): Texto a ser incluído no XML.
        limite (int): Limite de caracteres.

    Returns:
        str: O valor pronto para ser inserido em uma tag XML.
    """
    # Compõe as duas funções, primeiro preparando o campo, depois escapando o resultado.
    return escape_xml(preparar_campo(valor, limite))


# Nota: Não há 'module.exports' em Python.
# As funções já estão prontas para serem importadas em outros arquivos.
# Por exemplo: from app.lib.formatters import campo_xml
