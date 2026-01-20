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
    Monitora se a tela da instância está estática por muito tempo comparando hashes.
    """
    def __init__(self, emu_manager, timeout_minutes=5):
        self.emu = emu_manager
        self.timeout_seconds = timeout_minutes * 60
        self.last_hash = None
        self.last_change_time = time.time()
        self.package_name = "com.playshoo.texaspoker.romania" 

    def check_and_recover(self):
        """Verifica se a tela mudou ou se o app travou/congelou."""
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
        """Gera hash MD5 utilizando o método take_screenshot do EmulatorManager."""
        temp_path = f"logs/freeze_check_{self.emu.instance_id}.png"
        try:
            # Chama a função corrigida no emulator_manager.py
            self.emu.take_screenshot(temp_path)
            if os.path.exists(temp_path):
                with open(temp_path, "rb") as f:
                    return hashlib.md5(f.read()).hexdigest()
        except: return None
        return None

    def _force_restart_app(self):
        """Força o fechamento e reabertura do app via comandos ADB protegidos."""
        # Usa o executor do emu para garantir compatibilidade com caminhos de espaços
        self.emu._execute_memuc(['adb', '-i', str(self.emu.instance_id), 'shell', 'am', 'force-stop', self.package_name])
        time.sleep(2)
        self.emu._execute_memuc(['adb', '-i', str(self.emu.instance_id), 'shell', 'monkey', '-p', self.package_name, '1'])

# ==============================================================================
# FUNÇÕES DE GESTÃO E DIAGNÓSTICO
# ==============================================================================

def list_all_instances():
    """Lista instâncias usando o motor listv2 do EmulatorManager."""
    print(f"\n{'-'*65}")
    print(f"{'ID':<5} | {'NOME':<30} | {'STATUS':<15}")
    print(f"{'-'*65}")
    
    emu_helper = EmulatorManager(instance_id=0)
    instancias = emu_helper.list_instances() 
    
    if instancias:
        for inst in instancias:
            status = "🟢 Rodando" if inst['is_running'] else "⚪ Desligada"
            print(f"{inst['index']:<5} | {inst['title']:<30} | {status:<15}")
    else:
        print("[-] Nenhuma instância encontrada ou falha no serviço MEmu.")
    print(f"{'-'*65}\n")

def check_instance_network(instance_id):
    """Verifica IP atribuído usando o executor do EmulatorManager."""
    emu = EmulatorManager(instance_id=instance_id)
    print(f"[*] Verificando conectividade da Instância {instance_id}...")
    
    if not emu.is_running():
        print("[!] Instância desligada. Iniciando...")
        if not emu.launch_instance():
            return False

    # Comando ADB direcionado para a instância específica
    cmd = ['adb', '-i', str(instance_id), 'shell', 'ip', 'addr', 'show', 'wlan0']
    output = emu._execute_memuc(cmd)
    
    if output and "inet " in output:
        ip = output.split("inet ")[1].split("/")[0]
        print(f"\n[✅] REDE OK - IP: {ip}")
        return True
    
    print(f"\n[❌] ERRO DE REDE - Sem IP válido.")
    return False

# ==============================================================================
# ORQUESTRAÇÃO E TESTES
# ==============================================================================

def run_single_instance(instance_id):
    """Lança o bot completo. O orquestrador chamará get_screen_resolution."""
    try:
        orchestrator = NewAccountOrchestrator(instance_id=instance_id)
        resultado = orchestrator.run()
        print(f"\n[🏁] FINALIZADO: Instância {instance_id} retornou: {resultado}")
    except Exception as e:
        print(f"❌ Erro crítico na execução da instância {instance_id}: {e}")

def run_stress_test(instance_ids):
    """Dispara múltiplas instâncias em paralelo."""
    threads = []
    print(f"\n[🔥] INICIANDO ESTRESSE EM {len(instance_ids)} INSTÂNCIAS...")
    for idx in instance_ids:
        t = threading.Thread(target=run_single_instance, args=(idx,))
        threads.append(t)
        t.start()
        time.sleep(8) # Aumentado para dar tempo ao MEmu processar os logs iniciais
    for t in threads:
        t.join()

def setup_environment():
    """Garante que todas as pastas de suporte existam."""
    folders = ['logs', 'logs/errors', 'database', 'assets/ui', 'assets/profile', 'assets/slots']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def main():
    setup_environment()
    while True:
        print("\n" + "="*40)
        print("   🃏 PAINEL DE CONTROLE BOT POKER   ")
        print("="*40)
        print("1. Rodar Workflow em 1 Instância")
        print("2. TESTE DE ESTRESSE (Multi-Instâncias)")
        print("3. Clonar Nova Instância da Base (ID 0)")
        print("4. Testar Rede de uma Instância")
        print("5. LISTAR TODAS AS INSTÂNCIAS")
        print("6. Sair")
        
        opcao = input("\nSelecione: ")

        if opcao == "1":
            try:
                idx = int(input("Digite o ID da Instância: "))
                run_single_instance(idx)
            except ValueError: print("❌ Erro: O ID deve ser um número.")
        
        elif opcao == "2":
            run_stress_test([1, 2, 3, 4])
        
        elif opcao == "3":
            emu_base = EmulatorManager(instance_id=0)
            im = InstanceManager(emu_base)
            im.create_new_account_instance(base_id=0)

        elif opcao == "4":
            try:
                idx = int(input("Digite o ID da Instância para teste: "))
                check_instance_network(idx)
            except ValueError: print("❌ Erro: O ID deve ser um número.")

        elif opcao == "5":
            list_all_instances()

        elif opcao == "6":
            break
        else:
            print("⚠️ Opção inválida.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()