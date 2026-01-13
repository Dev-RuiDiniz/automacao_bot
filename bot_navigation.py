from core.emulator_manager import EmulatorManager
from actions.image_recognition import ImageRecognition
from actions.click_actions import ClickActions
from actions.ui_cleaner import UICleaner
from core.block_handler import BlockHandler
from core.instance_manager import InstanceManager # Nova integração: Reciclagem
from actions.daily_bonus import DailyBonus
from actions.maturation_manager import MaturationManager
from actions.slot_manager import SlotManager
from actions.nickname_manager import NicknameManager
import time

class AccountCreatorBot:
    """
    Controlador Mestre do Ciclo de Vida da Conta.
    Responsável por: Login, Identidade, Coleta de Bônus, Maturação e Auto-Reciclagem.
    """
    def __init__(self, instance_id):
        # Inicialização da infraestrutura básica
        self.emu = EmulatorManager(instance_id=instance_id)
        self.vision = ImageRecognition(self.emu, instance_id=instance_id)
        self.click = ClickActions(self.emu, instance_id=instance_id)
        self.log = self.emu.log
        
        # Inicialização dos módulos de lógica e segurança
        self.block_handler = BlockHandler(self.emu, instance_id=instance_id)
        self.inst_manager = InstanceManager(self.emu) # Gerenciador para deletar/clonar
        self.cleaner = UICleaner(self.emu, instance_id=instance_id)
        self.bonus = DailyBonus(self.emu, instance_id=instance_id)
        self.slot = SlotManager(self.emu, instance_id=instance_id)
        self.nick = NicknameManager(self.emu, instance_id=instance_id)
        self.maturation = MaturationManager(self.emu, instance_id=instance_id)

    def run_initial_navigation(self):
        """Workflow robusto com detecção de falhas e reciclagem de instâncias."""
        self.log.info(f"=== INICIANDO WORKFLOW ROBUSTO: INSTÂNCIA {self.emu.instance_id} ===")

        # --- 1. CHECKPOINT INICIAL DE SEGURANÇA (Tarefa 8) ---
        # Verificação preventiva: Se a tela de bloqueio já está visível no boot
        if self.block_handler.is_account_blocked():
            self.log.critical(f"[🚫] BLOQUEIO DETECTADO na Instância {self.emu.instance_id}!")
            self.inst_manager.delete_instance(self.emu.instance_id)
            self.log.info("[♻️] Instância deletada. O controlador deverá criar uma nova.")
            return "RECYCLE" # Sinaliza que a instância foi descartada

        # --- 2. PREPARAÇÃO E TERMOS ---
        if self.vision.wait_for_element("aceitar.png", timeout=15, click_on_find=True):
            self.log.info("[1/8] Termos de uso aceitos.")
            time.sleep(2)

        # --- 3. LOGIN DE VISITANTE (CRIAÇÃO DE CONTA) ---
        if self.vision.wait_for_element("visitante.png", timeout=15, click_on_find=True):
            self.log.info("[2/8] Criando conta de visitante...")
            time.sleep(12) 
        else:
            self.log.error("[-] Falha: Botão 'Visitante' não encontrado.")
            return False

        # --- 4. SEGUNDO CHECKPOINT (PÓS-LOGIN) ---
        # Muitos banimentos ocorrem exatamente no momento da criação da conta
        if self.block_handler.is_account_blocked():
            self.log.critical("[🚫] Banimento imediato detectado após login.")
            self.inst_manager.delete_instance(self.emu.instance_id)
            return "RECYCLE"

        # --- 5. CONFIGURAÇÃO DE IDENTIDADE ---
        self.log.info("[3/8] Gerando nickname único para evitar detecção de padrão...")
        novo_nick = self.nick.change_nickname()
        
        # --- 6. BÔNUS E LIMPEZA DE UI ---
        self.log.info("[4/8] Coletando bônus diário e limpando pop-ups...")
        self.bonus.check_and_spin()
        self.cleaner.clean_ui(iterations=3)

        # --- 7. MATURAÇÃO PARTE 1: SLOTS (Aposta 2, 9 Linhas) ---
        self.log.info("[5/8] Iniciando maturação em Slots (10 min) para ganho de XP...")
        self.slot.setup_and_run(duration_minutes=10)

        # --- 8. NAVEGAÇÃO PARA MESA DE POKER ---
        self.log.info("[6/8] Transicionando para mesas de Poker Brasil...")
        if self.vision.wait_for_element("poker_brasil.png", timeout=20, click_on_find=True):
            time.sleep(5)
            if self.vision.wait_for_element("jogar_agora.png", timeout=15, click_on_find=True):
                self.log.info("[7/8] Bot posicionado na mesa.")

                # --- 9. MATURAÇÃO PARTE 2: ANTI-AFK ---
                self.log.info("[8/8] Iniciando aquecimento final em mesa (10 min)...")
                if self.maturation.stay_on_table(duration_minutes=10):
                    self.log.info("✅ SUCESSO ABSOLUTO: Conta pronta para uso.")
                    return "SUCCESS"

        self.log.error("[-] Falha no workflow: Elemento visual não encontrado.")
        return "FAILED"

if __name__ == "__main__":
    # Teste unitário na Instância 0
    bot = AccountCreatorBot(instance_id=0)
    resultado = bot.run_initial_navigation()
    
    if resultado == "SUCCESS":
        print("\n[OK] Ciclo completo!")
    elif resultado == "RECYCLE":
        print("\n[♻️] Instância limpa devido a bloqueio.")
    else:
        print("\n[!] Falha técnica no script.")