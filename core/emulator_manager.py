import subprocess
import os
import time
from core.config_manager import ConfigManager
from core.log_manager import LogManager

class EmulatorManager:
    """
    Gerenciador de Ciclo de Vida do MEmu (memuc.exe).
    Responsável por: Ligar/Desligar, Clonagem, Gerenciamento de Apps e 
    Verificação de saúde via ADB.
    """

    def __init__(self, instance_id=0):
        self.config = ConfigManager()
        self.instance_id = instance_id
        self.log = LogManager(instance_id)
        
        # [AJUSTE] Busca o caminho e garante que as barras sejam tratadas corretamente
        path_raw = self.config.settings.get('emulator', {}).get('path', 'memuc.exe')
        self.memuc_path = os.path.normpath(path_raw)
        self.log.info(f"EmulatorManager inicializado: {self.memuc_path}")

    def _execute_memuc(self, args):
        """
        Executa comandos no CLI do MEmu usando lista de argumentos.
        Blindado contra espaços no caminho do diretório (Ex: Program Files).
        """
        # Monta o comando como uma lista: [executável, arg1, arg2...]
        command = [self.memuc_path] + args
        
        try:
            # Usamos shell=False para que o Windows não tente separar o caminho por espaços
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                encoding='utf-8',
                errors='ignore',
                shell=False 
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                return stdout.strip()
            else:
                self.log.error(f"Falha memuc {args}: {stderr or stdout}")
                return None
        except FileNotFoundError:
            self.log.error(f"Executável não encontrado: {self.memuc_path}")
            return None
        except Exception as e:
            self.log.error(f"Erro inesperado no subprocesso: {e}")
            return None

    # --- NOVO: MÉTODOS REQUISITADOS PELAS AÇÕES ---

    def get_screen_resolution(self):
        """
        Detecta a resolução da instância via ADB para normalizar cliques.
        Essencial para o ClickActions.py.
        """
        # Adicionamos -i <id> para garantir que pegamos a resolução da instância correta
        cmd = ['adb', '-i', str(self.instance_id), 'shell', 'wm', 'size']
        output = self._execute_memuc(cmd)
        
        if not output: 
            return 1280, 720
        
        try:
            # O output costuma ser "Physical size: 1280x720"
            res_line = [l for l in output.splitlines() if "size:" in l][0]
            res_str = res_line.split(": ")[1].strip()
            w, h = map(int, res_str.split('x'))
            return w, h
        except Exception:
            return 1280, 720

    def take_screenshot(self, save_path):
        """
        Captura a tela da instância e salva no caminho especificado.
        Essencial para o Watchdog (FreezeWatchdog).
        """
        # Comando nativo do memuc para screenshot é mais rápido que ADB
        return self._execute_memuc(['screencap', '-i', str(self.instance_id), save_path])

    # --- GERENCIAMENTO DE ESTADO ---

    def is_running(self):
        """Verifica se a instância específica está ativa."""
        output = self._execute_memuc(['isrunning', '-i', str(self.instance_id)])
        return "Running" in str(output)

    def launch_instance(self, timeout=120):
        """Liga o emulador e aguarda o ADB estar pronto."""
        if self.is_running():
            self.log.info(f"[!] Instância {self.instance_id} já está rodando.")
            return True

        self.log.info(f"[*] Iniciando Instância {self.instance_id} (Aguardando Boot)...")
        self._execute_memuc(['start', '-i', str(self.instance_id)])
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            check = self._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'echo', 'ready'])
            if check and "ready" in check:
                self.log.info(f"✅ Instância {self.instance_id} pronta!")
                time.sleep(3) 
                return True
            time.sleep(5)
            self.log.info(f"  - Boot em curso ({int(time.time() - start_time)}s)...")

        self.log.error(f"❌ Timeout ao iniciar instância {self.instance_id}.")
        return False

    def launch_app(self, package_name="com.playshoo.texaspoker.romania"):
        """Lança o app de Poker de forma forçada."""
        self.log.info(f"[*] Lançando aplicativo: {package_name}")
        self._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'am', 'force-stop', package_name])
        time.sleep(1)
        
        cmd = ['adb', '-i', str(self.instance_id), 'shell', 'monkey', '-p', package_name, '1']
        self._execute_memuc(cmd)
        
        time.sleep(5)
        return True

    def stop_app(self, package_name):
        """Encerra o app."""
        return self._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'am', 'force-stop', package_name])

    def list_instances(self):
        """
        Mapeia todas as instâncias existentes com limpeza de cache.
        """
        # Passo 1: Forçar uma atualização do estado do serviço memu
        self._execute_memuc(['none']) # Comando vazio apenas para 'acordar' o serviço
        
        # Passo 2: Tentar listv2
        raw_data = self._execute_memuc(['listv2'])
        
        # Passo 3: Fallback para list -l se o primeiro falhar
        if not raw_data or len(raw_data.strip()) < 5:
            self.log.info("Aviso: listv2 falhou. Tentando comando clássico...")
            raw_data = self._execute_memuc(['list', '-l'])
            
        if not raw_data: 
            return []
        
        instances = []
        for line in raw_data.splitlines():
            # Trata separadores: vírgula ou tabulação
            parts = line.replace('\t', ',').split(',')
            
            # O MEmu às vezes envia linhas de cabeçalho ou erro, filtramos pelo primeiro item (ID)
            if len(parts) >= 4 and parts[0].isdigit():
                try:
                    instances.append({
                        "index": int(parts[0]),
                        "title": parts[1],
                        "is_running": parts[3] != "-1",
                        "pid": parts[4] if len(parts) > 4 else None
                    })
                except (ValueError, IndexError):
                    continue
        return instances