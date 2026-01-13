from core.emulator_manager import EmulatorManager
from actions.image_recognition import ImageRecognition
from actions.click_actions import ClickActions
from actions.ui_cleaner import UICleaner       # Novo: Zelador de interface
from core.block_handler import BlockHandler
from actions.daily_bonus import DailyBonus
import time

class AccountCreatorBot:
    def __init__(self, instance_id):
        # Inicializa todos os módulos necessários para a instância específica
        self.emu = EmulatorManager(instance_id=instance_id)
        self.vision = ImageRecognition(self.emu, instance_id=instance_id)
        self.click = ClickActions(self.emu, instance_id=instance_id)
        self.block_handler = BlockHandler(self.emu, instance_id=instance_id)
        self.cleaner = UICleaner(self.emu, instance_id=instance_id) # Inicializa o limpador
        self.log = self.emu.log

    def run_initial_navigation(self):
        """Executa a sequência lógica de cliques para levar a conta até a mesa."""
        self.log.info(f"=== Iniciando Navegação Inicial - Instância {self.emu.instance_id} ===")

        # --- PASSO 1: TERMOS DE USO ---
        # Muitos jogos resetam os termos ao clonar ou limpar cache.
        if self.vision.wait_for_element("aceitar.png", timeout=20, click_on_find=True):
            self.log.info("[1/4] Termos aceitos com sucesso.")
            time.sleep(2)
        
        # --- PASSO 2: SEGURANÇA (CHECKPOINT DE BAN) ---
        # Verifica se o IP ou a conta base já foi marcada pelo servidor.
        if self.block_handler.is_account_blocked():
            self.log.warning("[!] Detectada tela de bloqueio. Abortando navegação.")
            self.block_handler.handle_blocked_account()
            return False

        # --- PASSO 3: LOGIN ---
        # Tenta entrar como Visitante para criar uma conta nova.
        if self.vision.wait_for_element("visitante.png", timeout=15, click_on_find=True):
            self.log.info("[2/4] Botão Visitante clicado. Aguardando carregamento do Lobby...")
            time.sleep(8) # Tempo maior para o servidor processar a criação da conta
        else:
            self.log.error("[-] Botão Visitante não apareceu.")
            return False
        
        self.log.info("[*] Iniciando verificação de Bônus Diário...")
        bonus = DailyBonus(self.emu, self.instance_id)
        bonus.check_and_spin()

        # --- PASSO 4: LIMPEZA DE UI (PROMOÇÕES) ---
        # Após o login, o jogo costuma disparar janelas de 'Bônus Diário' e 'Ofertas'.
        # Chamamos o UICleaner para garantir que o menu principal esteja visível.
        self.log.info("[*] Executando limpeza de pop-ups e promoções...")
        self.cleaner.clean_ui(iterations=3) # Tenta fechar até 3 janelas sobrepostas

        # --- PASSO 5: SELEÇÃO DE MODO ---
        # Tenta localizar a região do Poker Brasil.
        if self.vision.wait_for_element("poker_brasil.png", timeout=20, click_on_find=True):
            self.log.info("[3/4] Entrou no setor Poker Brasil.")
            time.sleep(3)
        else:
            # Caso uma promoção tenha surgido exatamente agora, tentamos limpar de novo
            self.cleaner.clean_ui(iterations=1)
            if self.vision.wait_for_element("poker_brasil.png", timeout=5, click_on_find=True):
                self.log.info("[3/4] Entrou no setor Poker Brasil (após segunda limpeza).")
            else:
                return False

        # --- PASSO 6: ENTRAR NA MESA ---
        # Clique final para iniciar a partida ou a maturação.
        if self.vision.wait_for_element("jogar_agora.png", timeout=15, click_on_find=True):
            self.log.info("[4/4] Bot entrou na fila de jogo com sucesso!")
            return True

        self.log.error("[-] Falha crítica: O fluxo foi interrompido por elemento ausente.")
        return False

if __name__ == "__main__":
    # Teste de execução individual na Instância 0
    bot = AccountCreatorBot(instance_id=0)
    sucesso = bot.run_initial_navigation()
    
    if sucesso:
        print("Teste concluído: Bot chegou ao destino final.")
    else:
        print("Teste falhou: Verifique os logs e screenshots em logs/errors/.")