# A biblioteca 'requests' é o padrão para fazer chamadas HTTP em Python.
# Você precisa instalá-la: py -m pip install requests
import requests


def buscar_codigo_municipio(nome_municipio, uf):
    """
    Busca o código IBGE de um município com base no nome e na UF.

    Args:
        nome_municipio (str): Nome do município a ser buscado.
        uf (str): Sigla do estado (UF) onde o município está localizado.

    Returns:
        dict: Um dicionário com {'codigo': 'codigo_ibge', 'cep': None} em caso de sucesso.

    Raises:
        Exception: Se a requisição falhar, o JSON for inválido ou o município não for encontrado.
    """
    # Validação básica dos inputs
    if not nome_municipio or not uf:
        raise ValueError("Nome do município e UF são obrigatórios.")

    # Monta a URL da API do IBGE
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf.upper( )}/municipios"

    print(f"[IBGE] Buscando municípios da UF: {uf.upper()}, URL: {url}")

    try:
        # Faz a requisição GET. O timeout é uma boa prática para evitar que a aplicação trave.
        response = requests.get(url, timeout=10)

        # Lança uma exceção se a resposta tiver um status de erro (4xx ou 5xx)
        response.raise_for_status()

        # Converte a resposta para JSON diretamente
        municipios = response.json()

        # Normaliza o nome do município para comparação (sem espaços e minúsculo)
        nome_normalizado = nome_municipio.strip().lower()
        print(f"[IBGE] Procurando nome: {nome_normalizado}")

        # Itera sobre a lista de municípios para encontrar o correspondente
        for municipio in municipios:
            if municipio.get("nome", "").lower() == nome_normalizado:
                codigo_encontrado = municipio.get("id")
                print(
                    f"[IBGE] Município encontrado: {municipio.get('nome')}, Código IBGE: {codigo_encontrado}"
                )
                # Retorna o dicionário em caso de sucesso
                return {"codigo": codigo_encontrado, "cep": None}

        # Se o loop terminar e não encontrar, lança uma exceção
        print(
            f"[IBGE] Município '{nome_normalizado}' não encontrado na UF '{uf.upper()}'."
        )
        raise Exception("Município não encontrado.")

    except requests.exceptions.RequestException as e:
        # Captura erros de rede (DNS, timeout, etc.)
        print(f"[IBGE] Erro na requisição: {e}")
        raise Exception(f"Erro de rede ao conectar à API do IBGE: {e}") from e
    except ValueError as e:
        # Captura erros de parsing do JSON
        print(f"[IBGE] Erro ao interpretar resposta JSON: {e}")
        raise Exception("Erro ao interpretar JSON da API do IBGE.") from e


# Exemplo de como usar a função (para teste)
if __name__ == "__main__":
    try:
        # Teste 1: Sucesso
        resultado_sp = buscar_codigo_municipio("São Paulo", "SP")
        print("Resultado para São Paulo:", resultado_sp)

        print("-" * 20)

        # Teste 2: Sucesso com nome "bagunçado"
        resultado_bh = buscar_codigo_municipio("  belo horizonte  ", "mg")
        print("Resultado para Belo Horizonte:", resultado_bh)

        print("-" * 20)

        # Teste 3: Falha (município não existe)
        buscar_codigo_municipio("Cidade Inexistente", "SP")

    except Exception as e:
        print(f"\nOcorreu um erro esperado no teste: {e}")
