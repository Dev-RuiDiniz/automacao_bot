from core.emulator_manager import EmulatorManager
from actions.image_recognition import ImageRecognition
from actions.click_actions import ClickActions
from actions.ui_cleaner import UICleaner
from core.block_handler import BlockHandler
from core.instance_manager import InstanceManager 
from core.account_registry import AccountRegistry # Tarefa 9: Registro JSON
from actions.daily_bonus import DailyBonus
from actions.maturation_manager import MaturationManager
from actions.slot_manager import SlotManager
from actions.nickname_manager import NicknameManager
import time

class AccountCreatorBot:
    """
    Controlador Mestre do Ciclo de Vida da Conta.
    Responsável por: Login, Identidade, Coleta de Bônus, Maturação e Persistência.
    """
    def __init__(self, instance_id):
        # 1. Inicialização da infraestrutura e logs
        self.emu = EmulatorManager(instance_id=instance_id)
        self.vision = ImageRecognition(self.emu, instance_id=instance_id)
        self.click = ClickActions(self.emu, instance_id=instance_id)
        self.log = self.emu.log
        
        # 2. Inicialização dos módulos de lógica de negócio
        self.block_handler = BlockHandler(self.emu, instance_id=instance_id)
        self.inst_manager = InstanceManager(self.emu) 
        self.registry = AccountRegistry() # Banco de dados JSON
        self.cleaner = UICleaner(self.emu, instance_id=instance_id)
        self.bonus = DailyBonus(self.emu, instance_id=instance_id)
        self.slot = SlotManager(self.emu, instance_id=instance_id)
        self.nick = NicknameManager(self.emu, instance_id=instance_id)
        self.maturation = MaturationManager(self.emu, instance_id=instance_id)

    def run_initial_navigation(self):
        """Workflow completo com segurança, maturação e finalização."""
        self.log.info(f"=== INICIANDO WORKFLOW COMPLETO: INSTÂNCIA {self.emu.instance_id} ===")

        # --- PASSO 1: CHECKPOINT DE SEGURANÇA (Tarefa 8) ---
        # Se detectar bloqueio logo no início, deleta a instância e sinaliza reciclagem
        if self.block_handler.is_account_blocked():
            self.log.critical(f"[🚫] BLOQUEIO DETECTADO na Instância {self.emu.instance_id}!")
            self.inst_manager.delete_instance(self.emu.instance_id)
            return "RECYCLE"

        # --- PASSO 2: TERMOS DE USO ---
        if self.vision.wait_for_element("aceitar.png", timeout=15, click_on_find=True):
            self.log.info("[1/9] Termos de uso aceitos.")
            time.sleep(2)

        # --- PASSO 3: LOGIN DE VISITANTE ---
        if self.vision.wait_for_element("visitante.png", timeout=15, click_on_find=True):
            self.log.info("[2/9] Criando conta de visitante...")
            time.sleep(12) # Tempo para o servidor registrar a nova conta
        else:
            self.log.error("[-] Falha: Botão 'Visitante' não encontrado.")
            return "FAILED"

        # --- PASSO 4: TROCA DE NICKNAME (Tarefa 7) ---
        # Altera o nome padrão para um nome humano aleatório do NameGenerator
        self.log.info("[3/9] Configurando identidade única...")
        novo_nick = self.nick.change_nickname()
        if not novo_nick:
            novo_nick = f"Guest_{self.emu.instance_id}" # Fallback
        
        # --- PASSO 5: COLETA DE BÔNUS/ROLETA (Tarefa 4) ---
        self.log.info("[4/9] Coletando bônus diário (Roleta)...")
        self.bonus.check_and_spin()

        # --- PASSO 6: LIMPEZA DE UI (Tarefa 3) ---
        # Fecha pop-ups de ofertas que travam a navegação
        self.log.info("[5/9] Limpando interface de pop-ups...")
        self.cleaner.clean_ui(iterations=3)

        # --- PASSO 7: MATURAÇÃO EM SLOTS (Tarefa 6) ---
        # Roda Slot por 10 minutos (9 linhas, aposta 2) para aquecer a conta
        self.log.info("[6/9] Iniciando maturação em Slots (10 min)...")
        self.slot.setup_and_run(duration_minutes=10)

        # --- PASSO 8: NAVEGAÇÃO PARA POKER ---
        self.log.info("[7/9] Transicionando para mesas de Poker Brasil...")
        if self.vision.wait_for_element("poker_brasil.png", timeout=20, click_on_find=True):
            time.sleep(5)
            if self.vision.wait_for_element("jogar_agora.png", timeout=15, click_on_find=True):
                
                # --- PASSO 9: MATURAÇÃO EM MESA (Tarefa 5) ---
                # Permanece ativo na mesa por 10 min (Anti-AFK)
                self.log.info("[8/9] Iniciando maturação final em mesa (10 min)...")
                if self.maturation.stay_on_table(duration_minutes=10):
                    
                    # --- PASSO 10: FINALIZAÇÃO E REGISTRO (Tarefa 9) ---
                    # Retorna ao lobby, fecha o app e salva no JSON
                    self.log.info("[9/9] Finalizando e registrando conta no banco de dados...")
                    self.registry.register_account(novo_nick, self.emu.instance_id)
                    
                    # Comando ADB para fechar o jogo e poupar CPU
                    self.emu._execute_memuc(['adb', '-i', str(self.emu.instance_id), 'shell', 'am', 'force-stop', 'com.poker.package'])
                    
                    self.log.info(f"✅ CONTA {novo_nick} PRONTA E REGISTRADA!")
                    return "SUCCESS"

        self.log.error("[-] Ciclo incompleto por falha de navegação.")
        return "FAILED"

if __name__ == "__main__":
    # Teste unitário manual na Instância 0
    bot = AccountCreatorBot(instance_id=0)
    resultado = bot.run_initial_navigation()
    
    print(f"\nResultado Final: {resultado}")