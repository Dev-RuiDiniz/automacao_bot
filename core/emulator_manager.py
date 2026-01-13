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
        
        # Caminho do executável MEmu
        self.memuc_path = self.config.settings.get('emulator', {}).get('path', 'memuc.exe')
        self.log.info(f"EmulatorManager inicializado: {self.memuc_path}")

    def _execute_memuc(self, args):
        """Executa comandos no CLI do MEmu e retorna a saída limpa."""
        try:
            command = [self.memuc_path] + args
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                check=True,
                encoding='utf-8'
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.log.error(f"Falha memuc {args}: {e.stderr}")
            return None
        except FileNotFoundError:
            self.log.error(f"Executável não encontrado em: {self.memuc_path}")
            return None

    # --- NOVO: GERENCIAMENTO DE ESTADO E INICIALIZAÇÃO ---

    def is_running(self):
        """Verifica se a instância específica está ativa."""
        output = self._execute_memuc(['isrunning', '-i', str(self.instance_id)])
        return "Running" in str(output)

    def launch_instance(self, timeout=120):
        """
        Liga o emulador e aguarda o sistema Android estar pronto para receber comandos ADB.
        Garante que o 'ADB Pull' não falhe por falta de inicialização.
        """
        if self.is_running():
            self.log.info(f"[!] Instância {self.instance_id} já está rodando.")
            return True

        self.log.info(f"[*] Iniciando Instância {self.instance_id} (Aguardando Boot)...")
        self._execute_memuc(['start', '-i', str(self.instance_id)])
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Comando de teste para verificar se o sistema de arquivos está montado
            check = self._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'echo', 'ready'])
            if check and "ready" in check:
                self.log.info(f"✅ Instância {self.instance_id} pronta!")
                time.sleep(5) # Buffer de estabilidade
                return True
            time.sleep(5)
            self.log.info(f"  - Boot em curso ({int(time.time() - start_time)}s)...")

        self.log.error(f"❌ Timeout ao iniciar instância {self.instance_id}.")
        return False

    def launch_app(self, package_name="com.playshoo.texaspoker.romania"):
        """Lança o app de Poker de forma forçada e limpa."""
        self.log.info(f"[*] Lançando aplicativo: {package_name}")
        
        # 1. Garante que qualquer instância travada do app seja fechada antes
        self._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'am', 'force-stop', package_name])
        time.sleep(1)
        
        # 2. Comando Monkey para disparar a Intent principal
        cmd = ['adb', '-i', str(self.instance_id), 'shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1']
        self._execute_memuc(cmd)
        
        # 3. Aguarda o processo aparecer no sistema
        time.sleep(5)
        check = self._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'pidof', package_name])
        if check:
            self.log.info(f"✅ App {package_name} carregando (PID: {check})")
            return True
        return False

    def stop_app(self, package_name="com.poker.package"):
        """Força o encerramento do app (útil para economizar CPU após maturação)."""
        self.log.info(f"[*] Encerrando app: {package_name}")
        return self._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'am', 'force-stop', package_name])

    # --- GERENCIAMENTO DE INSTÂNCIAS ---

    def list_instances(self):
        """Mapeia todas as instâncias existentes."""
        raw_data = self._execute_memuc(['listv2'])
        if not raw_data: return []
        
        instances = []
        for line in raw_data.splitlines():
            parts = line.split(',')
            if len(parts) >= 4:
                instances.append({
                    "index": int(parts[0]),
                    "title": parts[1],
                    "is_running": parts[3] != "-1",
                    "pid": parts[4] if len(parts) > 4 else None
                })
        return instances

    def get_screen_resolution(self):
        """Detecta resolução para normalizar cliques."""
        cmd_output = self._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'wm', 'size'])
        if not cmd_output: return 1280, 720
        
        try:
            res_line = [l for l in cmd_output.splitlines() if "size:" in l][0]
            res_str = res_line.split(": ")[1].strip()
            return map(int, res_str.split('x'))
        except:
            return 1280, 720

    def clone_instance(self, source_index=0):
        """Clona a instância base (Tarefa 1)."""
        self.log.info(f"Clonando base {source_index}...")
        return self._execute_memuc(['clone', '-i', str(source_index)])

    def remove_instance(self, index):
        """Deleta a instância do disco (Tarefa 8)."""
        self.log.error(f"Removendo instância {index} permanentemente.")
        return self._execute_memuc(['remove', '-i', str(index)])