# app/lib/mappers/codigo_mapper.py

import csv
import os
import sys

# --- LÓGICA DE CAMINHO UNIVERSAL PARA PYTHON ---


def obter_caminho_recurso(caminho_relativo):
    """
    Obtém o caminho absoluto para um recurso, funcionando tanto em modo de
    desenvolvimento quanto em modo "congelado" (executável PyInstaller).
    """
    # Verifica se a aplicação está rodando como um executável PyInstaller
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # MODO PRODUÇÃO (.exe): O caminho base é a pasta temporária _MEIPASS
        base_path = sys._MEIPASS
    else:
        # MODO DESENVOLVIMENTO (.py): O caminho base é a raiz do projeto.
        # __file__ é o caminho deste script. Vamos "subir" 3 níveis para chegar na raiz.
        # app/lib/mappers/codigo_mapper.py -> app/lib/mappers -> app/lib -> app -> raiz
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )

    return os.path.join(base_path, caminho_relativo)


# Define o caminho relativo do CSV a partir da raiz do projeto
CAMINHO_CSV_RELATIVO = os.path.join("app", "assets", "codigo.csv")

# Obtém o caminho absoluto final
CAMINHO_CSV = obter_caminho_recurso(CAMINHO_CSV_RELATIVO)

# --- FIM DA LÓGICA DE CAMINHO ---

# Dicionário para armazenar o mapeamento de IBGE para código interno
MAPA_CODIGOS = {}


def carregar_mapa_codigos():
    """
    Lê o arquivo CSV e carrega os dados para o dicionário MAPA_CODIGOS.
    Esta função deve ser chamada uma vez, no início da aplicação.
    """
    # Limpa o mapa caso a função seja chamada mais de uma vez
    MAPA_CODIGOS.clear()

    print(f"[codigo_mapper] Tentando carregar CSV de: {CAMINHO_CSV}")

    if not os.path.exists(CAMINHO_CSV):
        erro_msg = (
            f"[codigo_mapper] ERRO CRÍTICO: Não foi possível encontrar 'codigo.csv'."
        )
        print(f"Caminho verificado: {CAMINHO_CSV}")
        raise FileNotFoundError(erro_msg)

    try:
        # Abre o arquivo CSV com a codificação correta (geralmente 'utf-8')
        with open(CAMINHO_CSV, mode="r", encoding="utf-8") as infile:
            # Usa o leitor de dicionário do Python, especificando o delimitador
            reader = csv.DictReader(infile, delimiter=";")

            for row in reader:
                ibge = row.get("MUN_IN_CODIGOIBGE", "").strip()
                codigo_interno = row.get("MUN_IN_CODIGO", "").strip()

                if ibge and codigo_interno:
                    MAPA_CODIGOS[ibge] = codigo_interno

        print(
            f"[codigo_mapper] Código CSV carregado com {len(MAPA_CODIGOS)} registros."
        )

    except Exception as e:
        print(f"[codigo_mapper] ERRO AO LER O CSV de '{CAMINHO_CSV}': {e}")
        # Lança a exceção para que a aplicação saiba que falhou em carregar
        raise


def get_codigo_interno_por_ibge(codigo_ibge: str) -> str:
    """
    Busca o código interno correspondente a um código IBGE.

    Raises:
        KeyError: Se o código IBGE não for encontrado no mapa.
    """
    # Converte para string para garantir a consistência da chave
    codigo_ibge_str = str(codigo_ibge)

    if not MAPA_CODIGOS:
        # Garante que os dados foram carregados antes de tentar usar
        raise RuntimeError(
            "O mapa de códigos não foi carregado. Chame carregar_mapa_codigos() primeiro."
        )

    try:
        codigo = MAPA_CODIGOS[codigo_ibge_str]
        print(f"[codigo_mapper] Código interno para IBGE {codigo_ibge_str}: {codigo}")
        return codigo
    except KeyError:
        # Lança um erro mais específico se a chave não for encontrada
        raise KeyError(f"Código interno não encontrado para o IBGE: {codigo_ibge_str}")


# Bloco de teste
if __name__ == "__main__":
    try:
        # Simula o carregamento dos dados
        carregar_mapa_codigos()

        # Simula uma busca (substitua por um código IBGE real do seu CSV)
        if MAPA_CODIGOS:
            # Pega a primeira chave do dicionário para teste
            primeiro_ibge = next(iter(MAPA_CODIGOS))
            print(f"\nTestando busca para o código IBGE: {primeiro_ibge}")
            codigo_encontrado = get_codigo_interno_por_ibge(primeiro_ibge)
            print(f"SUCESSO: Código encontrado -> {codigo_encontrado}")

            print("\nTestando busca para um código inexistente...")
            get_codigo_interno_por_ibge("0000000")

    except Exception as e:
        print(f"\nERRO NO TESTE: {e}")
