import random


def gerar_cpf(formatado=False):
    """
    Gera um número de CPF válido.
    ... (o resto da função gerar_cpf como antes) ...
    """
    n = [random.randint(0, 9) for _ in range(9)]

    def calcular_dv(base):
        multiplicador_inicial = len(base) + 1
        soma = sum(num * (multiplicador_inicial - i) for i, num in enumerate(base))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    d1 = calcular_dv(n)
    d2 = calcular_dv(n + [d1])

    cpf_numeros = n + [d1, d2]
    cpf_str = "".join(map(str, cpf_numeros))

    if formatado:
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"
    else:
        return cpf_str


# Bloco de teste
if __name__ == "__main__":
    print(f"CPF Gerado: {gerar_cpf(formatado=True)}")
