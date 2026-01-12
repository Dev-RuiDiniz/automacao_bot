import subprocess
import os
import time
from core.config_manager import ConfigManager
from core.log_manager import LogManager

class EmulatorManager:
    """
    Responsável pelo controle de ciclo de vida das instâncias do MEmu (memuc.exe).
    Gerencia criação, clonagem, inicialização e monitoramento de status[cite: 6, 24].
    """

    def __init__(self, instance_id=0):
        """
        Inicializa o gerenciador com as configurações globais e o logger específico.
        :param instance_id: ID da instância principal que este objeto monitora.
        """
        self.config = ConfigManager()
        self.instance_id = instance_id
        
        # Inicializa o logger individual conforme requisito de logs detalhados [cite: 129]
        self.log = LogManager(instance_id)
        
        # Localiza o executável memuc definido no config/settings.yaml [cite: 27, 45]
        self.memuc_path = self.config.settings.get('emulator', {}).get('path', 'memuc.exe')
        
        self.log.info(f"EmulatorManager inicializado usando path: {self.memuc_path}")

    def _execute_memuc(self, args):
        """
        Executa comandos de baixo nível via subprocesso para o CLI do MEmu[cite: 6].
        """
        try:
            command = [self.memuc_path] + args
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                check=True,
                encoding='utf-8' # Garante compatibilidade com logs de terminal
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.log.error(f"Falha ao executar comando memuc {args}: {e.stderr}")
            return None

    def list_instances(self):
        """
        Analisa a saída do comando listv2 para mapear todas as instâncias existentes[cite: 17].
        Retorna: Lista de dicionários com [index, title, is_running, pid].
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
                    "is_running": parts[3] != "-1", # No memuc, -1 indica instância desligada
                    "pid": parts[4] if len(parts) > 4 else None
                }
                instances.append(instance_info)
        return instances

    def get_active_ids(self):
        """Retorna os IDs das instâncias que já estão em execução."""
        instances = self.list_instances()
        return [inst["index"] for inst in instances if inst["is_running"]]

    def start_instance(self, index=None, timeout=None):
        """
        Inicia uma instância e aguarda o boot completo até o timeout[cite: 63, 127].
        Resiliência: Verifica o status continuamente antes de liberar para o bot[cite: 130].
        """
        target_index = index if index is not None else self.instance_id
        wait_time = timeout if timeout is not None else self.config.get_timing('timeout_boot', 60)
        
        self.log.info(f"Solicitando boot da instância {target_index}...")
        
        # Evita comando redundante se já estiver rodando
        if target_index in self.get_active_ids():
            self.log.warning(f"Instância {target_index} já está ativa.")
            return True

        self._execute_memuc(['start', '-i', str(target_index)])
        
        # Loop de monitoramento de Boot (Requisito 7: Controle de Erros) [cite: 126]
        start_clock = time.time()
        while time.time() - start_clock < wait_time:
            instances = self.list_instances()
            for inst in instances:
                # O status de execução no listv2 confirma que o processo Android subiu
                if inst["index"] == target_index and inst["is_running"]:
                    self.log.info(f"Instância {target_index} carregada (PID: {inst['pid']}).")
                    
                    # Delay para estabilização do ADB interno [cite: 132]
                    time.sleep(5) 
                    return True
            
            time.sleep(3) 
            self.log.info(f"Aguardando boot da instância {target_index}...")

        self.log.error(f"Timeout atingido ao tentar iniciar instância {target_index}.")
        return False

    def stop_instance(self, index=None):
        """Finaliza a execução de uma instância[cite: 58]."""
        target_index = index if index is not None else self.instance_id
        self.log.warning(f"Encerrando instância {target_index}...")
        return self._execute_memuc(['stop', '-i', str(target_index)])

    def clone_instance(self, source_index=0):
        """Clona contas a partir da instância base (Requisito 6.1)[cite: 62]."""
        self.log.info(f"Clonando nova instância a partir da base {source_index}...")
        return self._execute_memuc(['clone', '-i', str(source_index)])

    def create_instance(self):
        """Cria uma nova instância limpa no MEmu[cite: 8]."""
        self.log.info("Criando nova instância vazia...")
        return self._execute_memuc(['create'])

    def remove_instance(self, index):
        """Exclui instância em caso de conta bloqueada (Requisito 5.1)[cite: 56]."""
        self.log.error(f"Removendo/Excluindo instância {index} permanentemente.")
        return self._execute_memuc(['remove', '-i', str(index)])