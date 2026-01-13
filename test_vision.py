from core.emulator_manager import EmulatorManager
from actions.image_recognition import ImageRecognition
from actions.click_actions import ClickActions
import time

def test_visao_jogo():
    print("\n=== INICIANDO TESTE DE VISÃO COMPUTACIONAL ===")
    
    # 1. Inicializa o Manager
    emu = EmulatorManager(instance_id=0)
    vision = ImageRecognition(emu, instance_id=0)
    click = ClickActions(emu, instance_id=0)

    # 2. Garante que o emulador está online
    if not emu.start_instance():
        print("[ERRO] Falha ao iniciar o emulador.")
        return

    print("[*] Emulador pronto. Aguardando 10s para estabilização do app...")
    time.sleep(10)

    # 3. Tenta localizar o botão "Visitante"
    # Usamos o wait_for_element para dar tempo do jogo carregar o menu
    print("[*] Procurando botão 'Visitante' na tela...")
    posicao = vision.wait_for_element(
        "visitante.png", 
        timeout=45, 
        interval=3, 
        threshold=0.7, 
        click_on_find=False
    )

    if posicao:
        print(f"[SUCESSO] Botão encontrado em: {posicao}")
        
        # 4. Teste de Interação: Clique no botão encontrado
        print("[*] Testando clique no botão localizado...")
        click.tap(posicao[0], posicao[1], normalize=False) 
        # normalize=False porque o vision já retorna a coord real da tela
        
        print("[TESTE CONCLUÍDO] O bot 'enxergou' e interagiu com o elemento.")
    else:
        print("[FALHA] O bot não conseguiu encontrar o botão.")
        print("[DICA] Verifique se o arquivo assets/buttons/visitante.png é idêntico ao que aparece na tela.")

if __name__ == "__main__":
    test_visao_jogo()