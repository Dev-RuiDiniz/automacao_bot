import sys
import os
from bots.new_accounts_bot import NewAccountOrchestrator
from core.instance_manager import InstanceManager
from core.emulator_manager import EmulatorManager

def setup_environment():
    """Garante que as pastas necessárias existam antes da execução."""
    folders = ['logs', 'database', 'assets/ui', 'assets/profile', 'assets/slots']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    print("[*] Ambiente de pastas verificado.")

def run_single_instance(instance_id):
    """Executa o ciclo completo em uma única instância específica."""
    print(f"\n{'='*50}")
    print(f"SISTEMA DE CRIAÇÃO DE CONTAS - INSTÂNCIA {instance_id}")
    print(f"{'='*50}")
    
    orchestrator = NewAccountOrchestrator(instance_id=instance_id)
    resultado = orchestrator.run()
    
    if resultado == "SUCCESS":
        print(f"\n✅ Finalizado com sucesso na instância {instance_id}")
    elif resultado == "RECYCLE":
        print(f"\n♻️ Instância {instance_id} reciclada (Bloqueio detectado).")
    else:
        print(f"\n❌ Falha técnica na instância {instance_id}. Verifique os logs.")

def main():
    setup_environment()
    
    print("--- MENU DO BOT POKER v1.0 (DIA 3) ---")
    print("1. Rodar Instância Específica")
    print("2. Criar/Clonar Nova Instância da Base (Memu)")
    print("3. Sair")
    
    opcao = input("\nEscolha uma opção: ")

    if opcao == "1":
        idx = int(input("Digite o ID da instância (ex: 0, 1, 2...): "))
        run_single_instance(idx)
    
    elif opcao == "2":
        # Exemplo de uso do InstanceManager para expandir a fazenda
        emu_base = EmulatorManager(instance_id=0)
        im = InstanceManager(emu_base)
        novo_id = im.create_new_account_instance(base_id=0)
        print(f"[+] Nova instância criada com ID: {novo_id}")
    
    elif opcao == "3":
        print("Encerrando...")
        sys.exit()
    
    else:
        print("Opção inválida.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Parada forçada pelo usuário.")
        sys.exit()