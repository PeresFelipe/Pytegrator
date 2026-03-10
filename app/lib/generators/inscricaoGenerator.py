import random


def gerar_inscricao_estadual():
    """
    Gera um número aleatório de 9 dígitos para simular uma Inscrição Estadual.
    """
    # 1. Geração do Número Aleatório:
    # A função `random.randint(a, b)` sorteia um número inteiro entre 'a' e 'b', incluindo ambos.
    # - 100000000 é o menor número possível com 9 dígitos.
    # - 999999999 é o maior número possível com 9 dígitos.
    # Ao sortear um número nesse intervalo, garantimos que ele sempre terá 9 dígitos.
    numero_aleatorio = random.randint(100000000, 999999999)

    # 2. Conversão para String:
    # O número gerado é convertido para o formato de texto (string) antes de ser retornado,
    # que é o formato geralmente esperado para campos de inscrição em sistemas.
    return str(numero_aleatorio)


def gerar_inscricao_municipal():
    """
    Gera um número aleatório de 8 dígitos para simular uma Inscrição Municipal.
    """
    # 1. Geração do Número Aleatório:
    # A lógica é a mesma da função anterior, mas ajustada para 8 dígitos.
    # - 10000000 é o menor número possível com 8 dígitos.
    # - 99999999 é o maior número possível com 8 dígitos.
    numero_aleatorio = random.randint(10000000, 99999999)

    # 2. Conversão para String:
    # Converte o número inteiro de 8 dígitos em uma string.
    return str(numero_aleatorio)
