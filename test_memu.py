import time
from core.emulator_manager import EmulatorManager

def test_ciclo_vida_memu():
    print("=== INICIANDO TESTE DE CONEXÃO MEmu ===")
    
    # Inicializa o gerenciador (o ID 0 é a instância base) [cite: 62]
    emu = EmulatorManager(instance_id=0)
    
    try:
        # 1. Tenta iniciar a instância e aguarda o boot [cite: 63, 127]
        # O timeout de 60s segue a regra de resiliência [cite: 130]
        sucesso = emu.start_instance(index=0, timeout=60)
        
        if sucesso:
            print("[TESTE] Instância 0 está online e pronta!")
            
            # Aguarda 5 segundos apenas para visualização no teste [cite: 132]
            print("[TESTE] Aguardando 5 segundos antes de fechar...")
            time.sleep(5)
            
            # 2. Tenta fechar a instância [cite: 58]
            emu.stop_instance(index=0)
            print("[TESTE] Comando de fechamento enviado com sucesso.")
        else:
            print("[TESTE] FALHA: A instância não iniciou dentro do tempo limite.")

    except Exception as e:
        print(f"[TESTE] Ocorreu um erro inesperado: {e}")
    
    print("=== FIM DO TESTE ===")

if __name__ == "__main__":
    test_ciclo_vida_memu()