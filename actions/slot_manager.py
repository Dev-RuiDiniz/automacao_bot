import time
import random
from actions.click_actions import ClickActions

class SlotManager:
    """
    Automatiza o comportamento em máquinas de Slot com verificação de segurança.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log
        
        # Carregando configurações do settings.yaml
        self.config = getattr(self.emu, 'settings', {}).get('slot_machine', {})
        
        from actions.image_recognition import ImageRecognition
        self.vision = ImageRecognition(self.emu, self.instance_id)
        self.click = ClickActions(self.emu, self.instance_id)

    def _get_balance(self):
        """Usa OCR para ler o saldo atual na tela."""
        # Define a região da tela onde o saldo aparece para otimizar o OCR
        # Exemplo: x, y, largura, altura
        roi_saldo = (800, 10, 150, 40) 
        
        try:
            raw_text = self.vision.get_text_from_region(roi_saldo)
            # Limpa o texto (remove símbolos de moeda, pontos e espaços)
            clean_text = ''.join(filter(str.isdigit, raw_text))
            return int(clean_text) if clean_text else 0
        except Exception as e:
            self.log.error(f"[-] Erro ao ler saldo via OCR: {e}")
            return None

    def setup_and_run(self):
        """Inicia o ciclo de giros com monitoramento de saldo a cada 5 min."""
        
        duration = self.config.get('default_duration_minutes', 20)
        lines = self.config.get('lines', 9)
        min_balance = 1500 # Limite de segurança

        self.log.info(f"[*] Slot na Instância {self.instance_id} | Segurança: Saldo Mínimo {min_balance}")

        # 1. Verificar Linhas
        img_lines = f"slot_{lines}_linhas.PNG"
        self.vision.wait_for_element(img_lines, timeout=10, click_on_find=True)

        # 2. Ciclo de Giros com Verificação Periódica
        start_time = time.time()
        end_time = start_time + (duration * 60)
        last_balance_check = 0

        while time.time() < end_time:
            current_minute = int((time.time() - start_time) / 60)

            # Executa OCR a cada 5 minutos
            if current_minute % 5 == 0 and current_minute != last_balance_check:
                saldo = self._get_balance()
                if saldo is not None:
                    self.log.info(f"[💰] Verificação de Saldo: {saldo}")
                    if saldo < min_balance:
                        self.log.error(f"[🚨] SALDO INSUFICIENTE ({saldo}). Abortando maturação!")
                        return False
                last_balance_check = current_minute

            # Mantém o giro ativo
            self.vision.find_element("btn_girar_auto.PNG", threshold=0.7, click=True)
            
            # Fecha pop-ups de ganho
            self.vision.find_element("fechar_ganho.PNG", threshold=0.7, click=True)
            
            time.sleep(random.randint(5, 10))

        self.log.info(f"[✅] Maturação concluída com saldo protegido na instância {self.instance_id}.")
        return True