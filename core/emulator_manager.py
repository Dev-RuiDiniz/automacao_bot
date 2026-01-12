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
        target_index = index if index is not None else self.instance_id
        # Versões novas do MEmu podem levar até 90s para boot completo em HDDs ou CPUs carregadas
        wait_time = timeout if timeout is not None else 90 
        
        self.log.info(f"[*] Iniciando instância {target_index} (Versão Recente MEmu)...")
        
        # Comando para iniciar
        self._execute_memuc(['start', '-i', str(target_index)])
        
        start_clock = time.time()
        while time.time() - start_clock < wait_time:
            instances = self.list_instances()
            for inst in instances:
                if inst["index"] == target_index:
                    # Verifica se o PID é válido e se o status indica atividade
                    if inst["is_running"] and inst["pid"] and int(inst["pid"]) > 0:
                        # Teste de prontidão real: tentamos um comando ADB simples
                        check_adb = self._execute_memuc(['adb', '-i', str(target_index), 'shell', 'getprop', 'sys.boot_completed'])
                        
                        if check_adb and "1" in check_adb:
                            self.log.info(f"[+] Instância {target_index} totalmente carregada e responsiva!")
                            return True
            
            time.sleep(5) 
            self.log.info(f"    - Aguardando sistema Android {target_index} (Status: Booting)...")

        self.log.error(f"[X] Erro Crítico: A instância {target_index} não respondeu ao comando ADB pós-boot.")
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