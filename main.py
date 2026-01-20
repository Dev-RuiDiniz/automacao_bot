import sys
import os
import time
import hashlib
import threading
from bots.new_accounts_bot import NewAccountOrchestrator
from core.instance_manager import InstanceManager
from core.emulator_manager import EmulatorManager

# ==============================================================================
# MONITOR DE CONGELAMENTO (WATCHDOG)
# ==============================================================================
class FreezeWatchdog:
    """
    Monitora se a tela da instância está estática por muito tempo.
    """
    def __init__(self, emu_manager, timeout_minutes=5):
        self.emu = emu_manager
        self.timeout_seconds = timeout_minutes * 60
        self.last_hash = None
        self.last_change_time = time.time()
        self.package_name = "com.playshoo.texaspoker.romania" # Package atualizado

    def check_and_recover(self):
        """Verifica se a tela mudou ou se o app travou."""
        current_hash = self._get_screen_hash()
        
        if current_hash != self.last_hash:
            self.last_hash = current_hash
            self.last_change_time = time.time()
            return True 

        elapsed = time.time() - self.last_change_time
        if elapsed > self.timeout_seconds:
            print(f"\n[🚨] INSTÂNCIA {self.emu.instance_id} CONGELADA! Reiniciando...")
            self._force_restart_app()
            self.last_change_time = time.time()
            return False
        return True

    def _get_screen_hash(self):
        """Gera hash MD5 do screenshot atual."""
        temp_path = f"logs/freeze_check_{self.emu.instance_id}.png"
        try:
            self.emu.take_screenshot(temp_path)
            if os.path.exists(temp_path):
                with open(temp_path, "rb") as f:
                    return hashlib.md5(f.read()).hexdigest()
        except: return None
        return None

    def _force_restart_app(self):
        """Reinicia o app via ADB."""
        self.emu._execute_memuc(['adb', 'shell', 'am', 'force-stop', self.package_name])
        time.sleep(2)
        self.emu._execute_memuc(['adb', 'shell', 'monkey', '-p', self.package_name, '1'])

# ==============================================================================
# GESTÃO DE EXECUÇÃO PARALELA (TESTE DE ESTRESSE)
# ==============================================================================
def run_single_instance(instance_id, is_stress_test=False):
    """
    Executa o ciclo completo em uma instância específica.
    is_stress_test: Se True, suprime inputs manuais para não travar a execução paralela.
    """
    print(f"\n[🚀] INICIANDO: Instância {instance_id}")
    
    # 1. Validar Rede e Proxy
    if not check_instance_network(instance_id):
        if not is_stress_test:
            confirm = input("⚠️ Falha de rede. Continuar? (s/n): ")
            if confirm.lower() != 's': return
        else:
            print(f"[❌] Instância {instance_id} abortada por falha de rede/proxy.")
            return

    # 2. Setup dos Componentes
    emu = EmulatorManager(instance_id=instance_id)
    watchdog = FreezeWatchdog(emu, timeout_minutes=5)
    orchestrator = NewAccountOrchestrator(instance_id=instance_id)
    
    # 3. Execução do Fluxo de 15 Passos
    # Passamos o watchdog para monitorar o Slot (20 min)
    resultado = orchestrator.run(watchdog_callback=watchdog.check_and_recover)
    
    print(f"\n[🏁] RESULTADO INSTÂNCIA {instance_id}: {resultado}")

def run_stress_test(instance_ids):
    """
    
    Dispara múltiplas instâncias simultaneamente usando Threads.
    """
    threads = []
    print(f"\n[🔥] INICIANDO TESTE DE ESTRESSE EM {len(instance_ids)} INSTÂNCIAS...")
    
    for idx in instance_ids:
        t = threading.Thread(target=run_single_instance, args=(idx, True))
        threads.append(t)
        t.start()
        time.sleep(5) # Delay entre boots para não sobrecarregar o CPU/Disco

    for t in threads:
        t.join() # Aguarda todas terminarem

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def setup_environment():
    """Cria a estrutura de pastas necessária."""
    folders = ['logs', 'database', 'assets/ui', 'assets/profile', 'assets/slots']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def check_instance_network(instance_id):
    """Verifica IP e conectividade (ProxyManager)."""
    emu = EmulatorManager(instance_id=instance_id)
    if not emu.is_running():
        emu.launch_instance()

    cmd = ['adb', '-i', str(instance_id), 'shell', 'ip', 'addr', 'show', 'wlan0']
    output = emu._execute_memuc(cmd)
    
    if output and "inet " in output:
        ip = output.split("inet ")[1].split("/")[0]
        print(f"[✅] Instância {instance_id} Online. IP: {ip}")
        return True
    return False

# ==============================================================================
# MENU PRINCIPAL
# ==============================================================================
def main():
    setup_environment() #
    
    while True:
        print("\n--- 🃏 PAINEL DE CONTROLE BOT POKER ---")
        print("1. Rodar Workflow em 1 Instância")
        print("2. TESTE DE ESTRESSE (4 Instâncias Simultâneas)")
        print("3. Clonar Nova Instância da Base (ID 0)")
        print("4. Sair")
        
        opcao = input("\nSelecione: ")

        if opcao == "1":
            try:
                idx = int(input("ID da Instância: "))
                run_single_instance(idx)
            except ValueError: print("ID Inválido.")
        
        elif opcao == "2":
            # IDs das instâncias para o teste de estresse
            ids_teste = [1, 2, 3, 4] 
            run_stress_test(ids_teste)
        
        elif opcao == "3":
            emu_base = EmulatorManager(instance_id=0)
            im = InstanceManager(emu_base)
            novo_id = im.create_new_account_instance(base_id=0)
            print(f"[+] Nova instância criada: {novo_id}")

        elif opcao == "4": break
        else: print("Opção inválida.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()