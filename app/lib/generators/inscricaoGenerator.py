import random


def gerar_inscricao_estadual():
    """Gera um número aleatório de 9 dígitos para a Inscrição Estadual."""
    return str(random.randint(100000000, 999999999))


def gerar_inscricao_municipal():
    """Gera um número aleatório de 8 dígitos para a Inscrição Municipal."""
    return str(random.randint(10000000, 99999999))


# Bloco de teste
if __name__ == "__main__":
    print(f"Inscrição Estadual: {gerar_inscricao_estadual()}")
    print(f"Inscrição Municipal: {gerar_inscricao_municipal()}")
