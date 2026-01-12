import subprocess
import os
from core.config_manager import ConfigManager

class EmulatorManager:
    def __init__(self):
        self.config = ConfigManager()
        # Busca o caminho do memuc definido no settings.yaml [cite: 27, 32]
        self.memuc_path = self.config.settings.get('emulator', {}).get('path', 'memuc.exe')

    def _execute_memuc(self, args):
        """Executa um comando via memuc.exe e retorna a saída [cite: 6]"""
        try:
            command = [self.memuc_path] + args
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar comando memuc: {e.stderr}")
            return None

    def list_instances(self):
        """Lista todas as instâncias do MEmu [cite: 6]"""
        return self._execute_memuc(['listv2'])

    def start_instance(self, index=0):
        """Inicia uma instância específica pelo índice [cite: 63]"""
        print(f"Iniciando instância {index}...")
        return self._execute_memuc(['start', '-i', str(index)])

    def stop_instance(self, index=0):
        """Fecha uma instância específica [cite: 58, 130]"""
        print(f"Fechando instância {index}...")
        return self._execute_memuc(['stop', '-i', str(index)])

    def clone_instance(self, source_index=0):
        """Clona uma nova instância a partir da base (MEmu 0) [cite: 62]"""
        print(f"Clonando instância a partir da base {source_index}...")
        return self._execute_memuc(['clone', '-i', str(source_index)])

    def create_instance(self):
        """Cria uma nova instância limpa [cite: 8]"""
        print("Criando nova instância...")
        return self._execute_memuc(['create'])

    def remove_instance(self, index):
        """Remove/Exclui uma instância (útil para contas bloqueadas) [cite: 56]"""
        print(f"Removendo instância {index}...")
        return self._execute_memuc(['remove', '-i', str(index)])