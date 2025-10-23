# core/logger_config.py

import logging
import os
from logging.handlers import RotatingFileHandler

# --- Configurações ---
LOG_DIR = "logs"  # Nome da pasta onde os logs serão salvos
LOG_FILENAME = "app.log"  # Nome do arquivo de log
LOG_LEVEL = logging.DEBUG  # Nível de log (DEBUG captura tudo)


def setup_logging():
    """Configura o sistema de logging para a aplicação."""

    # Cria o logger principal
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    # Evita adicionar múltiplos handlers se a função for chamada mais de uma vez
    if logger.hasHandlers():
        logger.handlers.clear()

    # Cria o diretório de logs se ele não existir
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # --- Handler 1: Escrever logs em um arquivo ---
    log_path = os.path.join(LOG_DIR, LOG_FILENAME)

    # RotatingFileHandler: Cria novos arquivos de log quando o atual atinge um tamanho máximo.
    # maxBytes=5*1024*1024 (5MB), backupCount=5 (mantém os últimos 5 arquivos)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(LOG_LEVEL)

    # --- Handler 2: Mostrar logs no console/terminal (para debug em tempo real) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Mostra apenas INFO e acima no console

    # --- Formato do Log ---
    # Define como cada linha de log será formatada
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )
    file_handler.setFormatter(log_format)
    console_handler.setFormatter(log_format)

    # Adiciona os handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info("=" * 50)
    logging.info("Sistema de Logging iniciado.")
    logging.info("=" * 50)

    # --- Captura de Erros Não Tratados ---
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Função para capturar exceções não tratadas e logá-las."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Não loga o erro se o usuário fechar com Ctrl+C
            return
        logging.critical(
            "Exceção não tratada:", exc_info=(exc_type, exc_value, exc_traceback)
        )

    # Substitui o manipulador de exceções padrão do Python pelo nosso
    logging.sys.excepthook = handle_exception
