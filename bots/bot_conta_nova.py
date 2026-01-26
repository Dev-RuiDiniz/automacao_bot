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
    Orquestrador Master: Unifica o Fluxo Operacional Completo em 5 Grandes Blocos.
    Responsável por levar a conta da criação até a maturação completa (20 min).
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

    def run(self, watchdog_callback=None):
        """
        Execução unificada do Fluxo Operacional.
        """
        self.log.info(f"🚀 [BOT] Iniciando Fluxo Operacional - Instância {self.emu.instance_id}")

        # ======================================================================
        # 1. PREPARAÇÃO DAS INSTÂNCIAS
        # ======================================================================
        # (Clonagem e Proxy são validados no main.py antes deste método)
        if not self.emu.launch_instance():
            self.log.error("❌ Erro ao ligar emulador.")
            return "FAILED"

        # ======================================================================
        # 2. INICIALIZAÇÃO DO JOGO
        # ======================================================================
        self.emu.launch_app(self.package)
        
        # Sequência de Login: Aceitar -> Visitante -> Poker Brasil -> Jogar
        login_sequence = ["aceitar.png", "visitante.png", "poker_brasil.png", "jogar.png"]
        for btn in login_sequence:
            if self.vision.wait_for_element(btn, timeout=20, click_on_find=True):
                self.log.info(f"[+] Botão {btn} clicado.")
                time.sleep(3)
        
        # Roleta Inicial
        if self.vision.wait_for_element("roleta_center.PNG", timeout=30, click_on_find=True):
            self.log.info("[+] Girando roleta inicial.")
            time.sleep(12) 

        # Limpeza de Promoções Pós-Roleta
        self.cleaner.clean_ui(iterations=3)

        # ======================================================================
        # 3. ACESSO À MESA (QUICK EXIT)
        # ======================================================================
        # Entra em "Jogar Já", espera 10s e sai
        if not self.maturation.quick_table_exit():
            self.log.warning("[!] Falha no Quick Exit, tentando seguir fluxo...")

        # Limpa promoções restantes após sair da mesa
        self.cleaner.clean_ui(iterations=2)

        # ======================================================================
        # 4. SLOT CLÁSSICO
        # ======================================================================
        # Troca o Nickname antes da maturação
        nome_gerado = self.nick.change_nickname()
        
        self.log.info("🎰 Entrando no Slot Clássico...")
        # Executa por 20 min com monitoramento de saldo e watchdog
        slot_sucesso = self.slot.setup_and_run(watchdog_callback=watchdog_callback)

        if not slot_sucesso:
            self.log.error("❌ Ciclo de maturação interrompido (Saldo ou Erro).")
            return "FAILED"

        # ======================================================================
        # 5. FINALIZAÇÃO
        # ======================================================================
        self.log.info("💾 Gravando estado final e encerrando...")
        
        # Marca como MATURADA_COMPLETA no banco de dados
        self.registry.update_status(self.emu.instance_id, "MATURADA_COMPLETA")
        
        # Encerra o App e a Instância
        self.emu.stop_app(self.package)
        # self.emu.close_instance() # Opcional dependendo da gestão de lotes
        
        return "SUCCESS"