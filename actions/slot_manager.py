import time
import random
from actions.click_actions import ClickActions

class SlotManager:
    """
    Automatiza o comportamento em máquinas de Slot para ganho de XP e maturação.
    Configuração: 9 Linhas | Aposta: 2 | Tempo: 10 min.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log
        
        # Inicialização otimizada
        from actions.image_recognition import ImageRecognition
        self.vision = ImageRecognition(self.emu, self.instance_id)
        self.click = ClickActions(self.emu, self.instance_id)

    def setup_and_run(self, duration_minutes=10):
        """Configura as apostas e inicia o ciclo de giros."""
        self.log.info(f"[*] Configurando Slot na Instância {self.instance_id}...")

        # 1. Configurar 9 Linhas (Nomes de arquivos simplificados para evitar erros de pasta)
        if not self.vision.wait_for_element("slot_9_linhas.PNG", timeout=15, click_on_find=True):
            self.log.warning("[-] Não foi possível configurar 9 linhas (talvez já esteja padrão).")

        # 2. Configurar Aposta Valor 2
        if not self.vision.wait_for_element("aposta_valor_2.PNG", timeout=10, click_on_find=True):
            self.log.warning("[-] Valor de aposta 2 não encontrado.")

        # 3. Iniciar Ciclo de Giros
        self.log.info(f"[!] Iniciando ciclo de {duration_minutes} minutos de giros...")
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        while time.time() < end_time:
            # Tenta clicar no botão de girar
            # Usamos find_element (sem wait longo) para o loop ser fluido
            self.vision.find_element("btn_girar_auto.PNG", threshold=0.7, click=True)
            
            # Anti-travamento: Fecha pop-ups de "Big Win" ou "Level Up"
            # IMPORTANTE: Garanta que 'fechar_ganho.PNG' esteja na pasta assets/buttons/
            if self.vision.find_element("fechar_ganho.PNG", threshold=0.7, click=True):
                self.log.info("[Slot] Popup de ganho/recompensa fechado.")
            
            # Espera humana entre giros
            time.sleep(random.randint(5, 10))
            
            elapsed = int((time.time() - start_time) / 60)
            if elapsed > 0 and elapsed % 2 == 0:
                self.log.info(f"[Slot] Progresso: {elapsed}/{duration_minutes} min.")

        self.log.info(f"[✅] Maturação via Slot concluída na instância {self.instance_id}.")
        return True