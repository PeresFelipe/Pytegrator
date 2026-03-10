# app/lib/mappers/codigo_mapper.py

import csv
import os
import sys

# --- LÓGICA DE CAMINHO UNIVERSAL PARA PYTHON ---


def obter_caminho_recurso(caminho_relativo):
    """
    Obtém o caminho absoluto para um recurso, funcionando tanto em modo de
    desenvolvimento (.py) quanto em modo "congelado" (executável PyInstaller).

    Esta função é crucial para garantir que a aplicação encontre seus arquivos
    (como CSVs e ícones) depois de ser empacotada em um único .exe.
    """
    # 1. Verifica se a aplicação está rodando como um executável ("frozen").
    # `getattr(sys, "frozen", False)` é uma forma segura de checar se o atributo 'frozen' existe no módulo 'sys'.
    # O PyInstaller define `sys.frozen = True` e cria `sys._MEIPASS`.
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # MODO PRODUÇÃO (.exe): Se for um executável, os arquivos de recurso
        # são extraídos para uma pasta temporária. O caminho para essa pasta
        # é armazenado em `sys._MEIPASS`. Este será nosso caminho base.
        base_path = sys._MEIPASS
    else:
        # MODO DESENVOLVIMENTO (.py): Se não for um executável, estamos rodando o script diretamente.
        # `os.path.dirname(__file__)` nos dá o diretório deste arquivo (`app/lib/mappers`).
        # Usamos `os.path.join` com ".." para "subir" na estrutura de pastas
        # até chegar ao diretório raiz do projeto.
        # app/lib/mappers -> app/lib -> app -> raiz do projeto
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )

    # 2. Concatena o caminho base (seja do modo dev ou prod) com o caminho relativo do arquivo.
    # Isso resulta no caminho absoluto e correto para o recurso, não importa como a aplicação é executada.
    return os.path.join(base_path, caminho_relativo)


# Define o caminho para o arquivo CSV, relativo à raiz do projeto.
CAMINHO_CSV_RELATIVO = os.path.join("app", "assets", "codigo.csv")

# Usa a função auxiliar para obter o caminho absoluto final e confiável do CSV.
CAMINHO_CSV = obter_caminho_recurso(CAMINHO_CSV_RELATIVO)

# --- FIM DA LÓGICA DE CAMINHO ---

# Dicionário global que servirá como um cache rápido na memória.
# Ele armazenará os dados do CSV no formato { 'codigo_ibge': 'codigo_interno' }.
MAPA_CODIGOS = {}


def carregar_mapa_codigos():
    """
    Lê o arquivo CSV de mapeamento e o carrega para o dicionário MAPA_CODIGOS.
    Esta função é projetada para ser chamada uma única vez, no início da aplicação,
    para evitar a leitura repetida do disco, otimizando a performance.
    """
    # Garante que, se a função for chamada novamente, o mapa antigo seja limpo
    # para evitar dados duplicados ou inconsistentes.
    MAPA_CODIGOS.clear()

    print(f"[codigo_mapper] Tentando carregar CSV de: {CAMINHO_CSV}")

    # Validação crucial: verifica se o arquivo CSV realmente existe no caminho calculado.
    if not os.path.exists(CAMINHO_CSV):
        erro_msg = (
            f"[codigo_mapper] ERRO CRÍTICO: Não foi possível encontrar 'codigo.csv'."
        )
        print(f"Caminho verificado: {CAMINHO_CSV}")
        # Lança uma exceção `FileNotFoundError`, que interromperá a inicialização
        # da aplicação, indicando que um recurso essencial está faltando.
        raise FileNotFoundError(erro_msg)

    try:
        # Abre o arquivo CSV em modo de leitura ('r') com a codificação 'utf-8',
        # que é padrão para suportar caracteres especiais e acentos.
        with open(CAMINHO_CSV, mode="r", encoding="utf-8") as infile:
            # `csv.DictReader` é um leitor que trata cada linha do CSV como um dicionário,
            # onde as chaves são os nomes das colunas do cabeçalho.
            # `delimiter=';'` informa que as colunas são separadas por ponto e vírgula.
            reader = csv.DictReader(infile, delimiter=";")

            # Itera sobre cada linha do arquivo CSV.
            for row in reader:
                # Obtém os valores das colunas 'MUN_IN_CODIGOIBGE' e 'MUN_IN_CODIGO'.
                # `.get(..., "")` é usado para evitar erros se uma coluna não existir.
                # `.strip()` remove espaços em branco do início e do fim dos valores.
                ibge = row.get("MUN_IN_CODIGOIBGE", "").strip()
                codigo_interno = row.get("MUN_IN_CODIGO", "").strip()

                # Adiciona ao dicionário somente se ambos os códigos (chave e valor) forem válidos.
                if ibge and codigo_interno:
                    MAPA_CODIGOS[ibge] = codigo_interno

        print(
            f"[codigo_mapper] Código CSV carregado com {len(MAPA_CODIGOS)} registros."
        )

    except Exception as e:
        # Captura qualquer outro erro que possa ocorrer durante a leitura do arquivo
        # (ex: permissão negada, arquivo corrompido).
        print(f"[codigo_mapper] ERRO AO LER O CSV de '{CAMINHO_CSV}': {e}")
        # Relança a exceção para que o ponto de entrada da aplicação possa tratá-la.
        raise


def get_codigo_interno_por_ibge(codigo_ibge: str) -> str:
    """
    Busca no mapa em memória o código interno correspondente a um código IBGE.

    :param codigo_ibge: O código IBGE a ser pesquisado.
    :return: O código interno correspondente.
    :raises RuntimeError: Se o mapa de códigos ainda não foi carregado.
    :raises KeyError: Se o código IBGE não for encontrado no mapa.
    """
    # Garante que a chave de busca seja sempre uma string, para corresponder ao formato das chaves do dicionário.
    codigo_ibge_str = str(codigo_ibge)

    # Verificação de segurança: se o dicionário `MAPA_CODIGOS` estiver vazio,
    # significa que `carregar_mapa_codigos()` não foi chamada ou falhou.
    if not MAPA_CODIGOS:
        raise RuntimeError(
            "O mapa de códigos não foi carregado. Chame carregar_mapa_codigos() primeiro."
        )

    try:
        # Tenta acessar o valor no dicionário usando o código IBGE como chave.
        # Esta é uma operação extremamente rápida (complexidade O(1)).
        codigo = MAPA_CODIGOS[codigo_ibge_str]
        print(f"[codigo_mapper] Código interno para IBGE {codigo_ibge_str}: {codigo}")
        return codigo
    except KeyError:
        # Se a chave (código IBGE) não existir no dicionário, um `KeyError` é levantado.
        # Capturamos esse erro e lançamos uma nova exceção com uma mensagem mais amigável,
        # informando qual código específico não foi encontrado.
        raise KeyError(f"Código interno não encontrado para o IBGE: {codigo_ibge_str}")
