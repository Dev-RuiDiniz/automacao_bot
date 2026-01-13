from core.emulator_manager import EmulatorManager
from core.proxy_manager import ProxyManager
import time

def test_proxy_validation():
    print("\n=== TESTE DE VALIDAÇÃO DE PROXY ===")
    instance_id = 0
    emu = EmulatorManager(instance_id=instance_id)
    proxy = ProxyManager(emu, instance_id=instance_id)

    if not emu.start_instance(): return

    # 1. Verifica IP Real (Sem Proxy)
    ip_original = proxy.get_current_ip()
    print(f"[1] IP Atual (Sem Proxy): {ip_original}")

    # 2. Aplica Proxy (Substitua pelos dados do seu proxy pago/residencial)
    # Exemplo: proxy.set_proxy("192.168.1.100", "8080")
    # proxy.set_proxy("SU_IP", "SUA_PORTA")

    # 3. Verifica novo IP
    print("[*] Aguardando 5s para propagação da rede...")
    time.sleep(5)
    
    ip_novo = proxy.get_current_ip()
    print(f"[2] IP Após Configuração: {ip_novo}")

    if ip_original != ip_novo and ip_novo != "Erro ao obter IP":
        print("[SUCESSO] O Proxy está ativo e funcional!")
    else:
        print("[ALERTA] O IP não mudou. Verifique as credenciais do Proxy ou se o ADB tem permissão.")

if __name__ == "__main__":
    test_proxy_validation()