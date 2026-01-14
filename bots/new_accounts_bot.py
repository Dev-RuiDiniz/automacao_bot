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
import os

class NewAccountOrchestrator:
    """
    Orquestrador Master: Gerencia o ciclo de vida completo da conta.
    Fluxo: Boot -> App -> Login -> Roleta -> Coleta Bônus -> Lobby -> Maturação.
    """
    def __init__(self, instance_id):
        self.emu = EmulatorManager(instance_id=instance_id)
        self.vision = ImageRecognition(self.emu, instance_id=instance_id)
        self.click = ClickActions(self.emu, instance_id=instance_id)
        self.log = self.emu.log
        
        self.block_handler = BlockHandler(self.emu, instance_id=instance_id)
        self.inst_manager = InstanceManager(self.emu) 
        self.registry = AccountRegistry()
        self.cleaner = UICleaner(self.emu, instance_id=instance_id)
        self.bonus = DailyBonus(self.emu, instance_id=instance_id)
        self.slot = SlotManager(self.emu, instance_id=instance_id)
        self.nick = NicknameManager(self.emu, instance_id=instance_id)
        self.maturation = MaturationManager(self.emu, instance_id=instance_id)

        self.package = "com.playshoo.texaspoker.romania"

    def _cleanup_environment(self):
        """Limpa logs locais e imagens residuais no Android/PC antes de iniciar."""
        self.log.info("🧹 [CLEANUP] Limpando erros e capturas anteriores...")
        
        # 1. Limpeza no Android via ADB (Imagens temporárias no sdcard)
        try:
            self.emu.run_command("shell rm -rf /sdcard/*.png")
            self.emu.run_command("shell rm -rf /sdcard/Download/*.png")
        except Exception as e:
            self.log.warning(f"⚠️ Aviso: Falha ao limpar Android: {e}")

        # 2. Limpeza no Windows (Pasta de logs de erro)
        error_dir = os.path.join("logs", "errors")
        if os.path.exists(error_dir):
            try:
                for file in os.listdir(error_dir):
                    file_path = os.path.join(error_dir, file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                self.log.info("✅ Pasta de erros local limpa.")
            except Exception as e:
                self.log.warning(f"⚠️ Aviso: Falha ao limpar pasta local: {e}")

    def run(self):
        self.log.info(f"🚀 [INÍCIO] Orquestrando Instância {self.emu.instance_id}")

        # --- ETAPA PREVENTIVA: LIMPEZA ---
        self._cleanup_environment()

        # --- ETAPA 0: PREPARAÇÃO ---
        if not self.emu.launch_instance():
            self.log.error("❌ Erro ao ligar emulador.")
            return "FAILED"

        self.emu.launch_app(self.package)
        time.sleep(20) 

        # --- ETAPA 1: SEGURANÇA ---
        if self.block_handler.is_account_blocked():
            self.log.critical(f"🚫 Bloqueio detectado na Instância {self.emu.instance_id}")
            self.inst_manager.delete_instance(self.emu.instance_id)
            return "RECYCLE"

        # --- ETAPA 2: LOGIN ---
        if self.vision.wait_for_element("aceitar.png", timeout=15, click_on_find=True):
            time.sleep(3)

        if self.vision.wait_for_element("visitante.png", timeout=15, click_on_find=True):
            self.log.info("✅ Login como visitante iniciado.")
            time.sleep(15) 

        # --- ETAPA 3: ROLETA E BÔNUS INICIAL ---
        self.log.info("🎰 Aguardando Roleta...")
        if self.vision.wait_for_element("roleta_center.PNG", timeout=20, click_on_find=True):
            time.sleep(12) 
            self.cleaner.clean_ui(iterations=1)

        # INTERAÇÃO COM "FORTUNA DOS INICIANTES"
        self.log.info("🎁 Verificando tela 'Fortuna dos Iniciantes'...")
        if self.vision.wait_for_element("coletar_01.PNG", timeout=15, click_on_find=True):
            self.log.info("✅ Bônus diário coletado com sucesso.")
            time.sleep(5)
            self.cleaner.clean_ui(iterations=2)

        # --- ETAPA 4: CONFIRMAÇÃO DO LOBBY ---
        self.log.info("🏁 Confirmando presença no Lobby...")
        lobby_confirmado = False
        for _ in range(3):
            if self.vision.wait_for_element("jogar_ja.PNG", timeout=10) or \
               self.vision.wait_for_element("mesas.PNG", timeout=5):
                lobby_confirmado = True
                break
            self.cleaner.clean_ui(iterations=1)
            time.sleep(2)

        if not lobby_confirmado:
            self.log.error("❌ Falha ao confirmar Lobby após roleta e bônus.")
            return "FAILED"
        
        self.log.info("✨ Lobby detectado com sucesso!")

        # --- ETAPA 5: MATURAÇÃO ---
        nome_gerado = self.nick.change_nickname()
        self.log.info("🎰 Iniciando Slots...")
        self.slot.setup_and_run(duration_minutes=10)
        
        self.log.info("🃏 Transicionando para mesas de Poker...")
        if self.vision.wait_for_element("mesas.PNG", timeout=20, click_on_find=True):
            time.sleep(10)
            if self.vision.wait_for_element("jogar_ja.PNG", timeout=20, click_on_find=True):
                if self.maturation.stay_on_table(duration_minutes=10):
                    self.log.info("💾 Ciclo finalizado. Registrando conta...")
                    self.registry.register_account(nome_gerado, self.emu.instance_id)
                    self.emu.stop_app(self.package)
                    return "SUCCESS"

        return "FAILED"

if __name__ == "__main__":
    orchestrator = NewAccountOrchestrator(instance_id=0)
    orchestrator.run()