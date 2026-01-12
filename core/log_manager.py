import logging
import os
from datetime import datetime

class LogManager:
    def __init__(self, instance_id=None):
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.instance_id = instance_id
        self.logger = self._setup_logger()

    def _setup_logger(self):
        # Define o nome do logger baseado no ID da instância ou 'main'
        logger_name = f"Instance_{self.instance_id}" if self.instance_id is not None else "Main_System"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # Evita duplicar handlers se o logger já existir
        if not logger.handlers:
            # Formato do log: Data - Nome - Nível - Mensagem
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            # Handler para arquivo individual
            file_name = f"bot_{self.instance_id if self.instance_id is not None else 'system'}.log"
            file_handler = logging.FileHandler(os.path.join(self.log_dir, file_name), encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # Handler para o console (opcional, para visualização em tempo real)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)