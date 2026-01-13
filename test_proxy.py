from core.emulator_manager import EmulatorManager
from core.proxy_manager import ProxyManager
import time

def test_proxy_validation():
    print("\n=== TESTE DE VALIDAÇÃO DE PROXY ===")
    instance_id = 0
    
    # 1. Setup inicial
    emu = EmulatorManager(instance_id=instance_id)
    proxy = ProxyManager(emu, instance_id=instance_id)

    if not emu.start_instance(): 
        print("[ERRO] Falha ao iniciar emulador.")
        return

    # 2. Captura o IP original (Sem Proxy)
    ip_original = proxy.get_current_ip()
    print(f"[1] IP Detectado (Original): {ip_original}")

    # 3. CONFIGURAÇÃO DO PROXY (PREENCHA AQUI)
    # Importante: O proxy deve ser HTTP e não exigir autenticação via pop-up
    MEU_PROXY_IP = "SEU_IP_AQUI"     # Ex: "185.123.44.12"
    MINHA_PORTA = "SUA_PORTA_AQUI"  # Ex: "8080"
    
    print(f"[*] Aplicando Proxy: {MEU_PROXY_IP}:{MINHA_PORTA}...")
    proxy.set_proxy(MEU_PROXY_IP, MINHA_PORTA)

    # 4. Verificação de Propagação
    print("[*] Aguardando 8s para o Android processar a nova rota de rede...")
    time.sleep(8)
    
    # 5. Captura o novo IP
    ip_novo = proxy.get_current_ip()
    print(f"[2] IP Detectado (Após Proxy): {ip_novo}")

    # 6. Veredito
    if ip_original != ip_novo and ip_novo != "Erro ao obter IP":
        print("\n✅ SUCESSO: O tráfego está sendo mascarado corretamente!")
    else:
        print("\n❌ FALHA: O IP permanece o mesmo ou o serviço está inacessível.")
        print("Dica: Verifique se o proxy está online ou se o firewall do Windows bloqueia o ADB.")

if __name__ == "__main__":
    test_proxy_validation()