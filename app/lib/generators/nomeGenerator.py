import random
import unicodedata
import re

# --- Constantes (listas de dados) ---
# Em Python, a convenção para constantes é usar letras maiúsculas.
NOMES = [
    "Lucas",
    "Mariana",
    "Joao",
    "Patricia",
    "Carlos",
    "Fernanda",
    "Gabriel",
    "Ana",
    "Mateus",
    "Juliana",
    "Rafael",
    "Camila",
    "Felipe",
    "Larissa",
    "Thiago",
    "Bruna",
    "Diego",
    "Aline",
    "Eduardo",
    "Leticia",
    "Vinicius",
    "Tatiane",
    "Daniel",
    "Carla",
    "Gustavo",
    "Vanessa",
    "Pedro",
    "Renata",
    "Igor",
    "Simone",
]

SOBRENOMES = [
    "Silva",
    "Oliveira",
    "Souza",
    "Lima",
    "Costa",
    "Pereira",
    "Almeida",
    "Gomes",
    "Martins",
    "Rocha",
    "Ribeiro",
    "Fernandes",
    "Barbosa",
    "Moura",
    "Carvalho",
    "Freitas",
    "Dias",
    "Monteiro",
    "Cardoso",
    "Batista",
]

SUFIXOS_CORPORATIVOS = [
    "Solucoes",
    "Consultoria",
    "Tech",
    "Servicos",
    "Inteligencia",
    "Logistica",
    "Estrategia",
    "Digital",
    "Seguranca",
    "Analytics",
    "Automacao",
    "Financeira",
    "RH",
    "Design",
    "Engenharia",
    "TI",
]

SIGLAS = [
    "SS",
    "JT",
    "GJ",
    "LP",
    "NX",
    "RM",
    "ACM",
    "VTX",
    "GRP",
    "X9",
    "TRX",
    "MGX",
    "BZ",
]


def remover_acentos(texto: str) -> str:
    """
    Remove acentos e caracteres especiais de uma string.
    """
    # Normaliza para o formato NFD (Canonical Decomposition)
    texto_normalizado = unicodedata.normalize("NFD", texto)
    # Remove caracteres de combinação (acentos)
    texto_sem_acentos = "".join(
        c for c in texto_normalizado if unicodedata.category(c) != "Mn"
    )
    # Remove caracteres especiais, exceto letras, números e espaços
    texto_limpo = re.sub(r"[^a-zA-Z0-9\s]", "", texto_sem_acentos)
    # Normaliza espaços múltiplos para um único espaço
    texto_limpo = re.sub(r"\s+", " ", texto_limpo)
    return texto_limpo.strip()


def gerar_nome_aleatorio() -> str:
    """Gera um nome completo aleatório (nome + sobrenome)."""
    nome = random.choice(NOMES)
    sobrenome = random.choice(SOBRENOMES)
    return remover_acentos(f"{nome} {sobrenome}")


def gerar_nome_empresa() -> str:
    """Gera um nome de empresa combinando dois sobrenomes diferentes."""
    # random.sample garante que pegamos 2 itens únicos da lista
    s1, s2 = random.sample(SOBRENOMES, 2)
    nome_empresa = f"{s1} & {s2}"
    return remover_acentos(nome_empresa)


def gerar_fantasia_empresa() -> str:
    """Gera um nome fantasia corporativo aleatório."""
    sigla = random.choice(SIGLAS)
    sufixo = random.choice(SUFIXOS_CORPORATIVOS)
    return remover_acentos(f"{sigla} {sufixo}")


def gerar_fantasia_pessoa_fisica(nome_pessoa: str) -> str:
    """Gera um nome fantasia baseado no primeiro nome de uma pessoa."""
    primeiro_nome = nome_pessoa.split(" ")[0]
    ideias = [
        f"Atelie {primeiro_nome}",
        f"Cantinho do {primeiro_nome}",
        f"{primeiro_nome} Presentes",
        f"By {primeiro_nome}",
        f"{primeiro_nome} Artes",
        f"Espaco {primeiro_nome}",
        f"Doces da {primeiro_nome}",
        f"Salao da {primeiro_nome}",
        f"Barbearia {primeiro_nome}",
        f"Studio {primeiro_nome}",
    ]
    return remover_acentos(random.choice(ideias))


# Bloco de teste
if __name__ == "__main__":
    print("--- GERADOR DE NOMES ---")
    nome_pf = gerar_nome_aleatorio()
    print(f"Nome de Pessoa Física: {nome_pf}")

    nome_pj = gerar_nome_empresa()
    print(f"Nome de Empresa (Razão Social): {nome_pj}")

    fantasia_pj = gerar_fantasia_empresa()
    print(f"Nome Fantasia (Empresa): {fantasia_pj}")

    fantasia_pf = gerar_fantasia_pessoa_fisica(nome_pf)
    print(f"Nome Fantasia (Pessoa Física): {fantasia_pf}")
