import random


def gerar_cnpj(formatado=False):
    """
    Gera um número de CNPJ válido.

    Args:
        formatado (bool): Se True, retorna o CNPJ no formato XX.XXX.XXX/XXXX-XX.
                          Se False, retorna apenas os 14 dígitos.

    Returns:
        str: O número do CNPJ gerado.
    """
    # 1. Gera os primeiros 8 dígitos aleatórios
    # 2. Adiciona os 4 dígitos do número da filial (0001 para matriz)
    n = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]

    # Função interna para calcular um dígito verificador
    def calcular_dv(base, pesos):
        # Multiplica cada dígito pelo seu peso correspondente e soma tudo
        soma = sum(d * p for d, p in zip(base, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    # 3. Calcula o primeiro dígito verificador (DV1)
    pesos_dv1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv1 = calcular_dv(n, pesos_dv1)

    # 4. Calcula o segundo dígito verificador (DV2)
    pesos_dv2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv2 = calcular_dv(n + [dv1], pesos_dv2)

    # 5. Junta todos os números
    cnpj_numeros = n + [dv1, dv2]

    # Converte a lista de números em uma string
    cnpj_str = "".join(map(str, cnpj_numeros))

    if formatado:
        # Aplica a máscara de formatação
        return f"{cnpj_str[:2]}.{cnpj_str[2:5]}.{cnpj_str[5:8]}/{cnpj_str[8:12]}-{cnpj_str[12:]}"
    else:
        # Retorna apenas os números
        return cnpj_str


# Bloco para testar a função quando o arquivo é executado diretamente
if __name__ == "__main__":
    # Gera e imprime um CNPJ sem formatação
    cnpj_sem_formato = gerar_cnpj()
    print(f"CNPJ Gerado (sem formatação): {cnpj_sem_formato}")
    print(f"Tamanho: {len(cnpj_sem_formato)} dígitos")

    print("-" * 20)

    # Gera e imprime um CNPJ com formatação
    cnpj_com_formato = gerar_cnpj(formatado=True)
    print(f"CNPJ Gerado (com formatação): {cnpj_com_formato}")
