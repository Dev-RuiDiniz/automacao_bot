import time
import random
from actions.click_actions import ClickActions

class SlotManager:
    """
    Automatiza o comportamento em máquinas de Slot.
    Configuração simplificada: Foca no tempo de maturação e giros automáticos.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log
        
        # Carregando configurações (default: 20 min)
        self.config = getattr(self.emu, 'settings', {}).get('slot_machine', {})
        
        from actions.image_recognition import ImageRecognition
        self.vision = ImageRecognition(self.emu, self.instance_id)
        self.click = ClickActions(self.emu, self.instance_id)

    def setup_and_run(self):
        """Inicia o ciclo de giros ignorando a configuração de aposta (automática)."""
        
        duration = self.config.get('default_duration_minutes', 20)
        lines = self.config.get('lines', 9)

        self.log.info(f"[*] Iniciando Slot na Instância {self.instance_id}...")
        self.log.info(f"[*] Configuração: {lines} Linhas | Tempo: {duration} min.")

        # 1. Verificar Linhas (Apenas se não for padrão)
        img_lines = f"slot_{lines}_linhas.PNG"
        if not self.vision.wait_for_element(img_lines, timeout=10, click_on_find=True):
            self.log.info("[-] Linhas já configuradas ou imagem não detectada.")

        # 2. Ciclo de Giros (Fixado em 20 min via settings)
        start_time = time.time()
        end_time = start_time + (duration * 60)

        while time.time() < end_time:
            # Tenta manter o giro ativo
            self.vision.find_element("btn_girar_auto.PNG", threshold=0.7, click=True)
            
            # Anti-travamento para Pop-ups de ganho
            if self.vision.find_element("fechar_ganho.PNG", threshold=0.7, click=True):
                self.log.info("[Slot] Popup fechado.")
            
            time.sleep(random.randint(5, 10))
            
            elapsed = int((time.time() - start_time) / 60)
            if elapsed > 0 and elapsed % 5 == 0:
                self.log.info(f"[Slot] Progresso: {elapsed}/{duration} min.")

        self.log.info(f"[✅] Maturação concluída na instância {self.instance_id}.")
        return True