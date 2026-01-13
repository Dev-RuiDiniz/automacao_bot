from core.emulator_manager import EmulatorManager
from actions.image_recognition import ImageRecognition
from actions.click_actions import ClickActions
from actions.ui_cleaner import UICleaner
from core.block_handler import BlockHandler
from actions.daily_bonus import DailyBonus
from actions.maturation_manager import MaturationManager
from actions.slot_manager import SlotManager
from actions.nickname_manager import NicknameManager # Tarefa 7 integrada
import time

class AccountCreatorBot:
    """
    Controlador centralizado para criação e maturação de contas.
    Integra visão computacional, gerenciamento de rede e simulação humana.
    """
    def __init__(self, instance_id):
        # Inicializa a infraestrutura de controle da instância
        self.emu = EmulatorManager(instance_id=instance_id)
        self.vision = ImageRecognition(self.emu, instance_id=instance_id)
        self.click = ClickActions(self.emu, instance_id=instance_id)
        self.log = self.emu.log
        
        # Inicializa os módulos de ação e lógica
        self.block_handler = BlockHandler(self.emu, instance_id=instance_id)
        self.cleaner = UICleaner(self.emu, instance_id=instance_id)
        self.bonus = DailyBonus(self.emu, instance_id=instance_id)
        self.slot = SlotManager(self.emu, instance_id=instance_id)
        self.nick = NicknameManager(self.emu, instance_id=instance_id)
        self.maturation = MaturationManager(self.emu, instance_id=instance_id)

    def run_initial_navigation(self):
        """Executa o workflow completo: Login -> Identidade -> Bônus -> Maturação."""
        self.log.info(f"=== INICIANDO WORKFLOW COMPLETO: INSTÂNCIA {self.emu.instance_id} ===")

        # --- 1. PREPARAÇÃO E TERMOS ---
        if self.vision.wait_for_element("aceitar.png", timeout=15, click_on_find=True):
            self.log.info("[1/8] Termos de uso aceitos.")
            time.sleep(2)
        
        # --- 2. SEGURANÇA (BLOQUEIO DE IP/DEVICE) ---
        if self.block_handler.is_account_blocked():
            self.log.critical("[!] Instância bloqueada pelo sistema anti-fraude. Encerrando.")
            self.block_handler.handle_blocked_account()
            return False

        # --- 3. LOGIN DE VISITANTE ---
        if self.vision.wait_for_element("visitante.png", timeout=15, click_on_find=True):
            self.log.info("[2/8] Login solicitado. Aguardando processamento do servidor...")
            time.sleep(12) # Delay de segurança para criação da conta no DB
        else:
            self.log.error("[-] Falha no login: Botão 'Visitante' não encontrado.")
            return False

        # --- 4. ALTERAÇÃO DE IDENTIDADE (NICKNAME) ---
        # Troca o nome genérico por um nome humano aleatório (Tarefa 7)
        self.log.info("[*] Configurando identidade única (Nickname)...")
        novo_nick = self.nick.change_nickname()
        if novo_nick:
            self.log.info(f"[3/8] Identidade definida: {novo_nick}")
        
        # --- 5. COLETA DE BÔNUS (ROLETA) ---
        self.log.info("[4/8] Coletando bônus diário...")
        self.bonus.check_and_spin()

        # --- 6. LIMPEZA DE INTERFACE (ANTI-POPUP) ---
        # Essencial para remover banners de ofertas antes de navegar nos menus
        self.log.info("[*] Limpando pop-ups e ofertas de login...")
        self.cleaner.clean_ui(iterations=3)

        # --- 7. MATURAÇÃO EM SLOTS (AQUECIMENTO DE CONTA) ---
        # Executa giros de Slot para gerar volume de jogo (Tarefa 6)
        # Configurado para 9 linhas, aposta 2, por 10 minutos
        self.log.info("[5/8] Iniciando maturação via Slots (10 minutos)...")
        self.slot.setup_and_run(duration_minutes=10)

        # --- 8. NAVEGAÇÃO PARA POKER BRASIL ---
        self.log.info("[*] Transicionando para mesas de Poker...")
        if self.vision.wait_for_element("poker_brasil.png", timeout=20, click_on_find=True):
            self.log.info("[6/8] Modo Poker Brasil selecionado.")
            time.sleep(5)
            
            if self.vision.wait_for_element("jogar_agora.png", timeout=15, click_on_find=True):
                self.log.info("[7/8] Bot sentado na mesa de Hold'em.")
                
                # --- 9. MATURAÇÃO FINAL EM MESA (ANTI-AFK) ---
                # Permanece na mesa simulando jogo real por mais 10 minutos (Tarefa 5)
                self.log.info("[8/8] Iniciando maturação final em mesa...")
                if self.maturation.stay_on_table(duration_minutes=10):
                    self.log.info("✅ CICLO COMPLETO CONCLUÍDO COM SUCESSO!")
                    return True

        self.log.error("[-] Ciclo interrompido: Falha na navegação final.")
        return False

if __name__ == "__main__":
    # Teste unitário na Instância 0
    bot = AccountCreatorBot(instance_id=0)
    if bot.run_initial_navigation():
        print("\n[OK] A instância finalizou todas as tarefas com sucesso.")
    else:
        print("\n[ERRO] A instância falhou em algum ponto do workflow.")