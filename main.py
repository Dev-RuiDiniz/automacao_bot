import sys
import os
import time
from bots.new_accounts_bot import NewAccountOrchestrator
from core.instance_manager import InstanceManager
from core.emulator_manager import EmulatorManager

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
    
    # Tenta obter o IP externo (o que o jogo vê) para confirmar o Proxy
    # Se o ADB não responder, o EmulatorManager tentará ligar a instância
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

def run_single_instance(instance_id):
    """Executa o ciclo completo: Boot -> Rede -> App -> Maturação."""
    print(f"\n{'='*50}")
    print(f"🚀 INICIANDO TESTE INTEGRADO - INSTÂNCIA {instance_id}")
    print(f"{'='*50}")
    
    # 1. Validar Rede antes de começar
    if not check_instance_network(instance_id):
        confirm = input("⚠️ Falha de rede detectada. Deseja continuar assim mesmo? (s/n): ")
        if confirm.lower() != 's': return

    # 2. Iniciar Orquestrador
    orchestrator = NewAccountOrchestrator(instance_id=instance_id)
    resultado = orchestrator.run()
    
    # 3. Feedback do Resultado
    if resultado == "SUCCESS":
        print(f"\n✅ CONTA PRONTA: Finalizado com sucesso na instância {instance_id}")
    elif resultado == "RECYCLE":
        print(f"\n♻️ RECICLAGEM: Instância {instance_id} deletada por bloqueio.")
    else:
        print(f"\n❌ ERRO TÉCNICO: Verifique os logs em logs/bot_{instance_id}.log")

def main():
    setup_environment()
    
    while True:
        print("\n--- 🃏 MENU DO BOT POKER v1.0 (DIA 3) ---")
        print("1. Rodar Workflow Completo (Boot + Maturação)")
        print("2. Clonar Nova Instância da Base (ID 0)")
        print("3. Apenas Testar IP/Rede de uma Instância")
        print("4. Sair")
        
        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            idx = int(input("Digite o ID da instância: "))
            run_single_instance(idx)
        
        elif opcao == "2":
            emu_base = EmulatorManager(instance_id=0)
            im = InstanceManager(emu_base)
            print("[*] Clonando instância base... aguarde.")
            novo_id = im.create_new_account_instance(base_id=0)
            print(f"[+] Sucesso! Nova instância criada com ID: {novo_id}")
        
        elif opcao == "3":
            idx = int(input("Digite o ID para teste de rede: "))
            check_instance_network(idx)

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