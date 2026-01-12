from core.emulator_manager import EmulatorManager
from actions.click_actions import ClickActions
import time

def test_completo():
    emu = EmulatorManager(instance_id=0)
    click = ClickActions(emu, instance_id=0)
    
    if emu.start_instance(index=0):
        print("[SUCESSO] Emulador pronto! Testando comando Home...")
        time.sleep(2)
        click.home_button() # Se funcionar, o Android reagirá
        print("[TESTE] Comando enviado. Verifique a tela do MEmu.")
        time.sleep(5)
        # emu.stop_instance(0) # Comentei para você ver o resultado na tela
    else:
        print("[FALHA] Não foi possível estabilizar o emulador.")

if __name__ == "__main__":
    test_completo()