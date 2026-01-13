from core.emulator_manager import EmulatorManager
from actions.image_recognition import ImageRecognition
from actions.click_actions import ClickActions
from actions.ui_cleaner import UICleaner
from core.block_handler import BlockHandler
from core.instance_manager import InstanceManager 
from core.account_registry import AccountRegistry
from actions.daily_bonus import DailyBonus
from actions.maturation_manager import MaturationManager
from actions.slot_manager import SlotManager
from actions.nickname_manager import NicknameManager
import time

class NewAccountOrchestrator:
    """
    Orquestrador Final: Controla o ciclo de vida completo, desde o 
    boot do emulador até o registro final da conta maturada.
    """
    def __init__(self, instance_id):
        self.emu = EmulatorManager(instance_id=instance_id)
        self.vision = ImageRecognition(self.emu, instance_id=instance_id)
        self.click = ClickActions(self.emu, instance_id=instance_id)
        self.log = self.emu.log
        
        # Módulos de Lógica e Persistência
        self.block_handler = BlockHandler(self.emu, instance_id=instance_id)
        self.inst_manager = InstanceManager(self.emu) 
        self.registry = AccountRegistry()
        self.cleaner = UICleaner(self.emu, instance_id=instance_id)
        self.bonus = DailyBonus(self.emu, instance_id=instance_id)
        self.slot = SlotManager(self.emu, instance_id=instance_id)
        self.nick = NicknameManager(self.emu, instance_id=instance_id)
        self.maturation = MaturationManager(self.emu, instance_id=instance_id)

    def run(self):
        """Pipeline completo: Boot -> App -> Maturação -> Registro."""
        self.log.info(f"🚀 [INÍCIO] Orquestrando Instância {self.emu.instance_id}")

        # --- ETAPA 0: INICIALIZAÇÃO DE AMBIENTE (Crucial para evitar falhas de ADB) ---
        if not self.emu.launch_instance():
            self.log.error("❌ Falha crítica ao iniciar o emulador.")
            return "FAILED"

        self.emu.launch_app("com.poker.package") # Substitua pelo seu Package real
        time.sleep(15) # Espera o app carregar a tela de Splash/Termos

        # --- ETAPA 1: SEGURANÇA E HIGIENE ---
        if self.block_handler.is_account_blocked():
            self.log.critical(f"🚫 Bloqueio detectado no startup da Instância {self.emu.instance_id}")
            self.inst_manager.delete_instance(self.emu.instance_id)
            return "RECYCLE"

        # --- ETAPA 2: NAVEGAÇÃO E LOGIN ---
        if self.vision.wait_for_element("aceitar.png", timeout=30, click_on_find=True):
            self.log.info("✅ Termos aceitos.")
            time.sleep(3)

        if not self.vision.wait_for_element("visitante.png", timeout=20, click_on_find=True):
            self.log.error("❌ Botão 'Visitante' não encontrado. Abortando.")
            return "FAILED"
        
        self.log.info("⏳ Aguardando criação da conta no servidor...")
        time.sleep(20) 

        # --- ETAPA 3: IDENTIDADE E RECOMPENSAS ---
        self.log.info("👤 Configurando perfil e coletando bônus...")
        nome_gerado = self.nick.change_nickname()
        self.bonus.check_and_spin()
        
        # --- ETAPA 4: LIMPEZA DE INTERFACE ---
        self.cleaner.clean_ui(iterations=4)

        # --- ETAPA 5: MATURAÇÃO 1 - SLOTS ---
        self.log.info("🎰 Iniciando Maturação via Slots (10 min)...")
        self.slot.setup_and_run(duration_minutes=10)
        self.cleaner.clean_ui(iterations=2) 

        # --- ETAPA 6: MATURAÇÃO 2 - POKER MESA ---
        self.log.info("🃏 Transicionando para mesas de Poker...")
        if self.vision.wait_for_element("poker_brasil.png", timeout=25, click_on_find=True):
            time.sleep(10)
            if self.vision.wait_for_element("jogar_agora.png", timeout=20, click_on_find=True):
                if self.maturation.stay_on_table(duration_minutes=10):
                    
                    # --- ETAPA 7: FINALIZAÇÃO E REGISTRO ---
                    self.log.info("💾 Ciclo finalizado. Registrando conta...")
                    self.registry.register_account(nome_gerado, self.emu.instance_id)
                    
                    # Fecha o app para economizar recursos para o próximo bot
                    self.emu.stop_app("com.poker.package")
                    
                    self.log.info(f"🏆 [SUCESSO] Instância {self.emu.instance_id} finalizada!")
                    return "SUCCESS"

        self.log.error("❌ Falha na etapa final de navegação.")
        return "FAILED"

if __name__ == "__main__":
    orchestrator = NewAccountOrchestrator(instance_id=0)
    status = orchestrator.run()