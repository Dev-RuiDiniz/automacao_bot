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
        """
        Lista todas as instâncias e retorna uma lista de dicionários.
        O comando 'listv2' retorna: índice, título, top_level_window, 
        status_inicialização, processo_id, etc.
        """
        raw_data = self._execute_memuc(['listv2'])
        if not raw_data:
            return []

        instances = []
        for line in raw_data.splitlines():
            parts = line.split(',')
            if len(parts) >= 4:
                instance_info = {
                    "index": int(parts[0]),
                    "title": parts[1],
                    "is_running": parts[3] != "-1", # -1 significa desligado
                    "pid": parts[4] if len(parts) > 4 else None
                }
                instances.append(instance_info)
        return instances

    def get_active_ids(self):
        """Retorna apenas os IDs (índices) das instâncias que estão ligadas."""
        instances = self.list_instances()
        return [inst["index"] for inst in instances if inst["is_running"]]

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