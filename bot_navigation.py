from core.emulator_manager import EmulatorManager
from actions.image_recognition import ImageRecognition
from actions.click_actions import ClickActions
from actions.ui_cleaner import UICleaner       
from core.block_handler import BlockHandler
from actions.daily_bonus import DailyBonus
from actions.maturation_manager import MaturationManager # Importado módulo de maturação
import time

class AccountCreatorBot:
    """
    Controlador central para o Bot de Criação de Contas Novas.
    Gerencia o ciclo de vida desde o login até a maturação na mesa.
    """
    def __init__(self, instance_id):
        # Inicialização dos módulos principais vinculados ao ID da instância
        self.emu = EmulatorManager(instance_id=instance_id)
        self.vision = ImageRecognition(self.emu, instance_id=instance_id)
        self.click = ClickActions(self.emu, instance_id=instance_id)
        self.block_handler = BlockHandler(self.emu, instance_id=instance_id)
        self.cleaner = UICleaner(self.emu, instance_id=instance_id)
        self.bonus = DailyBonus(self.emu, instance_id=instance_id)
        self.maturation = MaturationManager(self.emu, instance_id=instance_id)
        self.log = self.emu.log

    def run_initial_navigation(self):
        """Executa a sequência lógica de cliques para levar a conta até a mesa."""
        self.log.info(f"=== Iniciando Ciclo de Vida: Instância {self.emu.instance_id} ===")

        # --- PASSO 1: TERMOS DE USO ---
        # Verifica se a tela de termos aparece (comum em clones novos)
        if self.vision.wait_for_element("aceitar.png", timeout=20, click_on_find=True):
            self.log.info("[1/6] Termos aceitos.")
            time.sleep(2)
        
        # --- PASSO 2: CHECKPOINT DE SEGURANÇA ---
        # Valida se o IP ou dispositivo já está marcado/banido antes de tentar o login
        if self.block_handler.is_account_blocked():
            self.log.warning("[!] Conta ou IP bloqueado detectado. Abortando.")
            self.block_handler.handle_blocked_account()
            return False

        # --- PASSO 3: LOGIN COMO VISITANTE ---
        # Inicia a criação da conta no banco de dados do jogo
        if self.vision.wait_for_element("visitante.png", timeout=15, click_on_find=True):
            self.log.info("[2/6] Login 'Visitante' solicitado. Aguardando Lobby...")
            time.sleep(10) # Delay maior para estabilização pós-login
        else:
            self.log.error("[-] Falha ao localizar botão Visitante.")
            return False
        
        # --- PASSO 4: BÔNUS DIÁRIO (ROLETA) ---
        # Garante que a conta nova tenha saldo inicial para jogar
        self.log.info("[*] Verificando bônus de boas-vindas/roleta...")
        self.bonus.check_and_spin()

        # --- PASSO 5: LIMPEZA DE UI (ANTI-POPUP) ---
        # Fecha propagandas e ofertas que surgem logo após o login
        self.log.info("[*] Limpando interface de promoções...")
        self.cleaner.clean_ui(iterations=3)

        # --- PASSO 6: SELEÇÃO DE MODO DE JOGO ---
        # Direciona o bot para a seção correta (Ex: Poker Brasil)
        if self.vision.wait_for_element("poker_brasil.png", timeout=20, click_on_find=True):
            self.log.info("[3/6] Entrou no modo Poker Brasil.")
            time.sleep(3)
        else:
            # Re-tentativa de limpeza caso um popup tenha surgido no meio do caminho
            self.cleaner.clean_ui(iterations=1)
            if self.vision.wait_for_element("poker_brasil.png", timeout=5, click_on_find=True):
                self.log.info("[3/6] Entrou no modo Poker Brasil (2ª tentativa).")
            else:
                self.log.error("[-] Falha ao encontrar setor de jogo.")
                return False

        # --- PASSO 7: ENTRADA NA MESA E MATURAÇÃO ---
        # Aqui o bot entra no jogo e executa a lógica de simulação humana
        if self.vision.wait_for_element("jogar_agora.png", timeout=15, click_on_find=True):
            self.log.info("[4/6] Bot entrou na mesa. Iniciando maturação (10 min)...")
            
            # Chama o módulo de maturação para simular cliques e evitar o AFK kick
            # Isso é vital para "aquecer" a conta e evitar banimentos por inatividade
            sucesso_maturacao = self.maturation.stay_on_table(duration_minutes=10)
            
            if sucesso_maturacao:
                self.log.info("[5/6] Maturação concluída com sucesso.")
                return True
            else:
                self.log.warning("[!] Maturação interrompida (possível desconexão).")
                return False

        self.log.error("[6/6] Falha crítica: O bot não conseguiu chegar à mesa de jogo.")
        return False

if __name__ == "__main__":
    # Teste de execução individual na Instância 0
    # Em produção, este script será chamado pelo MultiInstanceController
    bot = AccountCreatorBot(instance_id=0)
    resultado = bot.run_initial_navigation()
    
    if resultado:
        print("\n✅ Fluxo Completo: Conta criada, bônus coletado e maturação finalizada.")
    else:
        print("\n❌ Erro no Fluxo: Verifique os logs detalhados acima.")