import sys
import os
import time
import hashlib
from bots.new_accounts_bot import NewAccountOrchestrator
from core.instance_manager import InstanceManager
from core.emulator_manager import EmulatorManager

# ==============================================================================
# MONITOR DE CONGELAMENTO (WATCHDOG)
# ==============================================================================
class FreezeWatchdog:
    """
    Monitora a atividade da tela da instância. Se a imagem não mudar por um 
    período determinado (5 min), considera que o app travou e força o restart.
    """
    def __init__(self, emu_manager, timeout_minutes=5):
        self.emu = emu_manager
        self.timeout_seconds = timeout_minutes * 60
        self.last_hash = None
        self.last_change_time = time.time()
        self.package_name = "com.poker.android" # Defina o package do seu jogo aqui

    def check_and_recover(self):
        """
        Verifica se a tela mudou. Retorna True se estiver OK, 
        ou reinicia o app e retorna False se detectar travamento.
        """
        current_hash = self._get_screen_hash()
        
        # Se o hash mudou, a tela está ativa. Atualizamos o timestamp.
        if current_hash != self.last_hash:
            self.last_hash = current_hash
            self.last_change_time = time.time()
            return True 

        # Se o hash é o mesmo, verificamos há quanto tempo está assim
        elapsed = time.time() - self.last_change_time
        if elapsed > self.timeout_seconds:
            print(f"\n[🚨] INSTÂNCIA {self.emu.instance_id} TRAVADA HÁ {int(elapsed/60)} MIN!")
            self._force_restart_app()
            # Reseta o timer para evitar loops de restart imediatos
            self.last_change_time = time.time()
            return False
        
        return True

    def _get_screen_hash(self):
        """Tira um print e gera uma assinatura MD5 da imagem."""
        temp_path = f"logs/freeze_check_{self.emu.instance_id}.png"
        try:
            self.emu.take_screenshot(temp_path)
            if os.path.exists(temp_path):
                with open(temp_path, "rb") as f:
                    return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            print(f"[-] Erro ao gerar hash de tela: {e}")
        return None

    def _force_restart_app(self):
        """Comando ADB para fechar e reabrir o aplicativo."""
        print(f"[*] Forçando reinicialização do app: {self.package_name}")
        # Comando para fechar
        self.emu._execute_memuc(['adb', 'shell', 'am', 'force-stop', self.package_name])
        time.sleep(2)
        # Comando para abrir (Monkey tool é o jeito mais rápido de disparar a MAIN intent)
        self.emu._execute_memuc([
            'adb', 'shell', 'monkey', '-p', self.package_name, 
            '-c', 'android.intent.category.LAUNCHER', '1'
        ])
        time.sleep(5) # Aguarda o início do carregamento

# ==============================================================================
# FUNÇÕES DE AMBIENTE E REDE
# ==============================================================================
def setup_environment():
    """Garante que as pastas necessárias existam antes da execução."""
    folders = ['logs', 'database', 'assets/ui', 'assets/profile', 'assets/slots']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    print("[*] Ambiente de pastas verificado.")

def check_instance_network(instance_id):
    """Valida se a instância tem rede e exibe o IP."""
    emu = EmulatorManager(instance_id=instance_id)
    print(f"[*] Verificando conectividade da Instância {instance_id}...")
    
    if not emu.is_running():
        print("[!] Instância desligada. Iniciando para validar rede...")
        emu.launch_instance()

    cmd = ['adb', '-i', str(instance_id), 'shell', 'ip', 'addr', 'show', 'wlan0']
    output = emu._execute_memuc(cmd)
    
    if output and "inet " in output:
        ip = output.split("inet ")[1].split("/")[0]
        print(f"[✅] Rede OK. IP Local da Instância: {ip}")
        return True
    else:
        print(f"[❌] Falha de rede na Instância {instance_id}. Verifique o Proxy.")
        return False

# ==============================================================================
# FLUXO PRINCIPAL DE EXECUÇÃO
# ==============================================================================
def run_single_instance(instance_id):
    """Executa o ciclo completo: Boot -> Rede -> App -> Maturação com Watchdog."""
    print(f"\n{'='*50}")
    print(f"🚀 INICIANDO WORKFLOW - INSTÂNCIA {instance_id}")
    print(f"{'='*50}")
    
    # 1. Validar Rede
    if not check_instance_network(instance_id):
        confirm = input("⚠️ Falha de rede detectada. Deseja continuar assim mesmo? (s/n): ")
        if confirm.lower() != 's': return

    # 2. Inicializar Gerenciadores e Watchdog
    emu = EmulatorManager(instance_id=instance_id)
    watchdog = FreezeWatchdog(emu, timeout_minutes=5)
    orchestrator = NewAccountOrchestrator(instance_id=instance_id)
    
    # 3. Executar Orquestrador passando o callback do Watchdog
    # O orquestrador deve chamar watchdog.check_and_recover() em seus loops
    resultado = orchestrator.run(watchdog_callback=watchdog.check_and_recover)
    
    # 4. Feedback do Resultado
    if resultado == "SUCCESS":
        print(f"\n✅ CONTA PRONTA: Finalizado com sucesso na instância {instance_id}")
    elif resultado == "RECYCLE":
        print(f"\n♻️ RECICLAGEM: Instância {instance_id} deletada por bloqueio.")
    else:
        print(f"\n❌ ERRO TÉCNICO: Verifique os logs em logs/bot_{instance_id}.log")

def main():
    setup_environment()
    
    while True:
        print("\n--- 🃏 MENU DO BOT POKER v1.0 (Watchdog Ativo) ---")
        print("1. Rodar Workflow Completo (Boot + Maturação)")
        print("2. Clonar Nova Instância da Base (ID 0)")
        print("3. Apenas Testar IP/Rede de uma Instância")
        print("4. Sair")
        
        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            try:
                idx = int(input("Digite o ID da instância: "))
                run_single_instance(idx)
            except ValueError:
                print("ID inválido.")
        
        elif opcao == "2":
            emu_base = EmulatorManager(instance_id=0)
            im = InstanceManager(emu_base)
            print("[*] Clonando instância base... aguarde.")
            novo_id = im.create_new_account_instance(base_id=0)
            print(f"[+] Sucesso! Nova instância criada com ID: {novo_id}")
        
        elif opcao == "3":
            try:
                idx = int(input("Digite o ID para teste de rede: "))
                check_instance_network(idx)
            except ValueError:
                print("ID inválido.")

        elif opcao == "4":
            print("Encerrando sistema...")
            break
        
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Parada forçada pelo usuário. Finalizando processos...")
        sys.exit()