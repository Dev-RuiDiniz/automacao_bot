import subprocess
import os
import time
from core.config_manager import ConfigManager
from core.log_manager import LogManager

class EmulatorManager:
    """
    Responsável pelo controle de ciclo de vida das instâncias do MEmu (memuc.exe).
    Gerencia criação, clonagem, inicialização, monitoramento de status e 
    extração de metadados da interface (UI).
    """

    def __init__(self, instance_id=0):
        """
        Inicializa o gerenciador com as configurações globais e o logger específico.
        :param instance_id: ID da instância principal que este objeto monitora.
        """
        self.config = ConfigManager()
        self.instance_id = instance_id
        
        # Inicializa o logger individual para garantir rastreabilidade por conta
        self.log = LogManager(instance_id)
        
        # Localiza o executável memuc definido no config/settings.yaml
        self.memuc_path = self.config.settings.get('emulator', {}).get('path', 'memuc.exe')
        
        self.log.info(f"EmulatorManager inicializado usando path: {self.memuc_path}")

    def _execute_memuc(self, args):
        """
        Executa comandos de baixo nível via subprocesso para o CLI do MEmu (memuc.exe).
        Retorna a saída limpa (string) ou None em caso de falha.
        """
        try:
            command = [self.memuc_path] + args
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                check=True,
                encoding='utf-8' # Suporte a caracteres especiais nos logs
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.log.error(f"Falha ao executar comando memuc {args}: {e.stderr}")
            return None
        except FileNotFoundError:
            self.log.error(f"Executável memuc.exe não encontrado no caminho: {self.memuc_path}")
            return None

    def list_instances(self):
        """
        Analisa a saída do comando 'listv2' para mapear todas as instâncias existentes.
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
                    "is_running": parts[3] != "-1", # -1 indica que o processo não existe
                    "pid": parts[4] if len(parts) > 4 else None
                }
                instances.append(instance_info)
        return instances

    def get_active_ids(self):
        """Retorna uma lista contendo apenas os IDs das instâncias ligadas."""
        instances = self.list_instances()
        return [inst["index"] for inst in instances if inst["is_running"]]

    def get_screen_resolution(self, index=None):
        """
        Obtém a resolução real da tela da instância via comando 'wm size' do ADB.
        Essencial para a normalização de coordenadas entre 720p/1080p.
        """
        target_index = index if index is not None else self.instance_id
        # Executa comando adb shell para pegar o tamanho da janela
        cmd_output = self._execute_memuc(['adb', '-i', str(target_index), 'shell', 'wm', 'size'])
        
        if not cmd_output:
            self.log.warning(f"Não foi possível obter resolução para instância {target_index}. Usando 1280x720.")
            return 1280, 720

        # Prioriza 'Override size' (resoluções customizadas) sobre 'Physical size'
        if "Override size:" in cmd_output:
            res_str = cmd_output.split("Override size: ")[1].strip()
        elif "Physical size:" in cmd_output:
            res_str = cmd_output.split("Physical size: ")[1].strip()
        else:
            return 1280, 720 # Fallback padrão
            
        try:
            width, height = map(int, res_str.split('x'))
            return width, height
        except ValueError:
            return 1280, 720

    def start_instance(self, index=None, timeout=None):
        """
        Inicia a instância e aguarda o boot completo do sistema Android.
        Verifica a prontidão real via variável sys.boot_completed do sistema.
        """
        target_index = index if index is not None else self.instance_id
        wait_time = timeout if timeout is not None else 90 
        
        self.log.info(f"[*] Iniciando instância {target_index} (Aguardando boot completo)...")
        
        # Envia comando de início
        self._execute_memuc(['start', '-i', str(target_index)])
        
        start_clock = time.time()
        while time.time() - start_clock < wait_time:
            instances = self.list_instances()
            for inst in instances:
                if inst["index"] == target_index:
                    # Verifica se o processo está rodando e tem um PID válido
                    if inst["is_running"] and inst["pid"] and int(inst["pid"]) > 0:
                        # Testa se o Android terminou de carregar o kernel e serviços base
                        check_adb = self._execute_memuc(['adb', '-i', str(target_index), 'shell', 'getprop', 'sys.boot_completed'])
                        
                        if check_adb and "1" in check_adb:
                            self.log.info(f"[+] Instância {target_index} pronta para comandos (PID: {inst['pid']}).")
                            return True
            
            time.sleep(5) 
            self.log.info(f"    - Boot da instância {target_index} em progresso...")

        self.log.error(f"[X] Timeout: Instância {target_index} não respondeu após {wait_time}s.")
        return False

    def stop_instance(self, index=None):
        """Finaliza a execução de uma instância de forma segura."""
        target_index = index if index is not None else self.instance_id
        self.log.warning(f"Encerrando instância {target_index}...")
        return self._execute_memuc(['stop', '-i', str(target_index)])

    def clone_instance(self, source_index=0):
        """Cria um clone de uma instância existente."""
        self.log.info(f"Clonando instância base {source_index}...")
        return self._execute_memuc(['clone', '-i', str(source_index)])

    def create_instance(self):
        """Cria uma nova instância limpa (Android padrão do MEmu)."""
        self.log.info("Criando nova instância Android...")
        return self._execute_memuc(['create'])

    def remove_instance(self, index):
        """Remove permanentemente uma instância do disco."""
        self.log.error(f"Removendo instância {index} permanentemente.")
        return self._execute_memuc(['remove', '-i', str(index)])