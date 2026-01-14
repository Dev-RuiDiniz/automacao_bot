import time
import random

class SlotManager:
    """
    Automatiza o comportamento em máquinas de Slot para ganho de XP e maturação.
    Configuração: 9 Linhas | Aposta: 2 | Tempo: 10 min.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.vision = None
        self.click = None
        self.log = emulator_manager.log

    def setup_and_run(self, duration_minutes=10):
        """Configura as apostas e inicia o ciclo de giros."""
        from actions.image_recognition import ImageRecognition
        from actions.click_actions import ClickActions
        
        if not self.vision: self.vision = ImageRecognition(self.emu, self.instance_id)
        if not self.click: self.click = ClickActions(self.emu, self.instance_id)

        self.log.info(f"[*] Configurando Slot na Instância {self.instance_id}...")

        # 1. Configurar 9 Linhas
        if not self.vision.wait_for_element("slots/slot_9_linhas.PNG", timeout=15, click_on_find=True):
            self.log.warning("[-] Não foi possível configurar 9 linhas (talvez já esteja padrão).")

        # 2. Configurar Aposta Valor 2
        # Clica repetidamente ou seleciona o valor 2
        if not self.vision.wait_for_element("slots/aposta_valor_2.PNG", timeout=10, click_on_find=True):
            self.log.warning("[-] Valor de aposta 2 não encontrado.")

        # 3. Iniciar Ciclo de Giros
        self.log.info(f"[!] Iniciando ciclo de 10 minutos de giros...")
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        while time.time() < end_time:
            # Tenta clicar no botão de girar (ou manter pressionado para Auto Spin)
            self.vision.find_element("slots/btn_girar_auto.PNG", threshold=0.7, click=True)
            
            # Anti-travamento: Fecha pop-ups de "Big Win" ou "Level Up"
            self.vision.find_element("ui/fechar_ganho.PNG", threshold=0.7, click=True)
            
            time.sleep(random.randint(5, 12)) # Intervalo entre giros para parecer humano
            
            elapsed = int((time.time() - start_time) / 60)
            if elapsed % 2 == 0:
                self.log.info(f"[Slot] Progresso: {elapsed}/{duration_minutes} min.")

        self.log.info(f"[✅] Maturação via Slot concluída na instância {self.instance_id}.")
        return True