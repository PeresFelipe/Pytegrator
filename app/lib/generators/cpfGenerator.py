import random


def gerar_cpf(formatado=False):
    """
    Gera um número de CPF válido, com ou sem formatação.

    :param formatado: Se True, retorna o CPF no formato 'XXX.XXX.XXX-XX'.
                      Se False, retorna apenas os 11 dígitos.
    :return: Uma string contendo um CPF válido.
    """
    # 1. Geração da Base: Cria uma lista com 9 números inteiros aleatórios (de 0 a 9).
    # Estes serão os primeiros nove dígitos do CPF, que formarão a base para o cálculo.
    n = [random.randint(0, 9) for _ in range(9)]

    # Função interna para calcular um dígito verificador (DV).
    def calcular_dv(base):
        # O cálculo do DV do CPF usa um multiplicador decrescente.
        # Para o primeiro DV, o multiplicador começa em 10 (tamanho da base 9 + 1).
        # Para o segundo DV, começa em 11 (tamanho da base 10 + 1).
        multiplicador_inicial = len(base) + 1

        # 2. Cálculo da Soma Ponderada: Multiplica cada número da base pelo seu respectivo peso.
        # Ex: (n1*10) + (n2*9) + (n3*8) + ...
        # O `enumerate` ajuda a obter tanto o índice (i) quanto o número (num) para o cálculo.
        soma = sum(num * (multiplicador_inicial - i) for i, num in enumerate(base))

        # 3. Obtenção do Resto: Calcula o resto da divisão da soma por 11.
        resto = soma % 11

        # 4. Definição do Dígito Verificador:
        # Se o resto da divisão for menor que 2 (0 ou 1), o dígito verificador é 0.
        # Caso contrário, o dígito é 11 menos o valor do resto.
        return 0 if resto < 2 else 11 - resto

    # 5. Cálculo do Primeiro Dígito Verificador (d1):
    # Usa os 9 números aleatórios gerados como base para o cálculo.
    d1 = calcular_dv(n)

    # 6. Cálculo do Segundo Dígito Verificador (d2):
    # A base para este cálculo são os 9 números originais MAIS o primeiro dígito (d1) já calculado.
    d2 = calcular_dv(n + [d1])

    # 7. Montagem do CPF: Concatena os 9 números base com os 2 dígitos verificadores.
    cpf_numeros = n + [d1, d2]
    # Converte a lista de números em uma única string.
    cpf_str = "".join(map(str, cpf_numeros))

    # 8. Formatação (Opcional):
    # Se o parâmetro 'formatado' for True, aplica a máscara de CPF.
    # Caso contrário, retorna a string com os 11 dígitos puros.
    if formatado:
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"
    else:
        return cpf_str
