import requests
import random
from urllib.parse import (
    quote,
)  # Para codificar a URL corretamente, similar ao encodeURIComponent


def buscar_endereco_por_municipio(municipio, uf):
    """
    Tenta encontrar um endereço genérico para um município e UF, usando a API do ViaCEP.

    Args:
        municipio (str): Nome do município (ex: "Campinas").
        uf (str): Sigla da UF (ex: "SP").

    Returns:
        dict: Um dicionário com dados do endereço em caso de sucesso.

    Raises:
        Exception: Se nenhum endereço for encontrado após todas as tentativas.
    """
    if not municipio or not uf:
        raise ValueError("Município e UF são obrigatórios.")

    # Lista de tipos de logradouro para tentar
    tipos_a_tentar = ["rua", "avenida", "praca", "estrada"]

    # Itera sobre a lista, tentando encontrar um endereço válido
    for tipo in tipos_a_tentar:
        try:
            # Monta a URL, codificando os parâmetros para segurança
            url = f"https://viacep.com.br/ws/{quote(uf )}/{quote(municipio)}/{quote(tipo)}/json/"
            print(f"[ViaCEP] Tentando com tipo '{tipo}': {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Lança erro para status 4xx/5xx

            enderecos = response.json()

            # A API do ViaCEP pode retornar um dicionário com a chave 'erro'
            if not isinstance(enderecos, list) or not enderecos or "erro" in enderecos:
                print(f"[ViaCEP] Nenhum endereço encontrado para tipo '{tipo}'.")
                continue  # Pula para a próxima iteração do loop

            # Tenta encontrar um endereço com CEP e logradouro, ou pega o primeiro como fallback
            endereco_valido = next(
                (e for e in enderecos if e.get("cep") and e.get("logradouro")),
                enderecos[0],
            )

            print(f"[ViaCEP] Endereço encontrado: {endereco_valido.get('logradouro')}")

            # Processa e retorna os dados do endereço encontrado
            return {
                "cep": endereco_valido.get("cep", "").replace("-", ""),
                "logradouro": endereco_valido.get("logradouro", "Rua Principal"),
                "bairro": endereco_valido.get("bairro", "Centro"),
                "numero": random.randint(100, 999),
                "sigla": (
                    "Avenida"
                    if "av" in endereco_valido.get("logradouro", "").lower()
                    else "R"
                ),
            }

        except requests.exceptions.RequestException as e:
            print(f"[ViaCEP] Erro de rede na tentativa com tipo '{tipo}': {e}")
            continue  # Tenta o próximo tipo em caso de erro de rede
        except Exception as e:
            print(f"[ViaCEP] Erro inesperado na tentativa com tipo '{tipo}': {e}")
            continue  # Tenta o próximo tipo

    # Se o loop terminar sem sucesso, lança uma exceção final
    raise Exception(
        f"Não foi possível encontrar um endereço para o município '{municipio}' - '{uf}' após todas as tentativas."
    )


# Exemplo de como usar a função (para teste)
if __name__ == "__main__":
    try:
        # Teste 1: Sucesso
        endereco_campinas = buscar_endereco_por_municipio("Campinas", "SP")
        print("\nEndereço encontrado para Campinas:", endereco_campinas)

        print("-" * 20)

        # Teste 2: Sucesso com outra cidade
        endereco_salvador = buscar_endereco_por_municipio("Salvador", "BA")
        print("\nEndereço encontrado para Salvador:", endereco_salvador)

    except Exception as e:
        print(f"\nOcorreu um erro esperado no teste: {e}")
