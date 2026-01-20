import time
import random
from actions.click_actions import ClickActions
# Importação hipotética do seu módulo de registro
# Caso o nome do arquivo seja diferente, ajuste aqui
from core.account_registry import AccountRegistry 

class SlotManager:
    """
    [Copiloto] Gerencia o ciclo de maturação em slots.
    Responsável por: OCR de saldo, Watchdog de freeze e Registro final de status.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log
        
        # Carrega configurações do settings.yaml (via emulator_manager)
        self.config = getattr(self.emu, 'settings', {}).get('slot_machine', {})
        
        from actions.image_recognition import ImageRecognition
        self.vision = ImageRecognition(self.emu, self.instance_id)
        self.click = ClickActions(self.emu, self.instance_id)
        
        # Inicializa o registrador de contas
        self.registry = AccountRegistry()

    def _get_balance(self):
        """Lê o saldo atual via OCR para segurança financeira."""
        roi_saldo = (800, 10, 150, 40) # Ajustar conforme a resolução
        try:
            raw_text = self.vision.get_text_from_region(roi_saldo)
            clean_text = ''.join(filter(str.isdigit, raw_text))
            return int(clean_text) if clean_text else None
        except Exception as e:
            self.log.error(f"[-] Erro OCR: {e}")
            return None

    def setup_and_run(self, watchdog_callback=None):
        """
        Executa o fluxo de 20 minutos e marca a conta como maturada ao fim.
        """
        duration = self.config.get('default_duration_minutes', 20)
        lines = self.config.get('lines', 9)
        min_balance = 2000 

        self.log.info(f"[*] Workflow Slot Iniciado - Instância {self.instance_id}")

        # 1. Configuração Inicial (Linhas)
        img_lines = f"slot_{lines}_linhas.PNG"
        self.vision.wait_for_element(img_lines, timeout=10, click_on_find=True)

        # 2. Ciclo de Maturação (20 minutos)
        start_time = time.time()
        end_time = start_time + (duration * 60)
        last_balance_check = -1

        while time.time() < end_time:
            current_minute = int((time.time() - start_time) / 60)

            # Check de Saldo (OCR) a cada 5 min
            if current_minute % 5 == 0 and current_minute != last_balance_check:
                saldo = self._get_balance()
                if saldo is not None and saldo < min_balance:
                    self.log.error(f"[🚨] Saldo Crítico: {saldo}. Abortando para preservar conta.")
                    return False
                last_balance_check = current_minute

            # Check de Congelamento (Watchdog)
            if watchdog_callback and not watchdog_callback():
                self.log.warning("[!] Freeze detectado pelo Watchdog. Recuperando...")
                time.sleep(10)

            # Execução do Giro e Limpeza de UI
            self.vision.find_element("btn_girar_auto.PNG", threshold=0.7, click=True)
            self.vision.find_element("fechar_ganho.PNG", threshold=0.7, click=True)
            
            time.sleep(random.randint(5, 10))

        # --- STEP 6: FINALIZAÇÃO LIMPA ---
        self.log.info(f"[⭐] TEMPO DE MATURAÇÃO ATINGIDO ({duration} min).")
        
        try:
            # Atualiza o status no banco de dados/registro
            # O 'account_id' deve ser recuperado do seu gerenciador de instâncias
            account_id = getattr(self.emu, 'current_account_id', self.instance_id)
            self.registry.update_status(account_id, "MATURADA_COMPLETA")
            
            self.log.info(f"[✅] Status da conta {account_id} atualizado para: MATURADA_COMPLETA")
            return True
        except Exception as e:
            self.log.error(f"[❌] Falha ao registrar finalização: {e}")
            return False