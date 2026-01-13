from core.emulator_manager import EmulatorManager
from actions.image_recognition import ImageRecognition
from actions.click_actions import ClickActions
from core.block_handler import BlockHandler
import time

class AccountCreatorBot:
    def __init__(self, instance_id):
        self.emu = EmulatorManager(instance_id=instance_id)
        self.vision = ImageRecognition(self.emu, instance_id=instance_id)
        self.click = ClickActions(self.emu, instance_id=instance_id)
        self.block_handler = BlockHandler(self.emu, instance_id=instance_id)

    def run_initial_navigation(self):
        """Executa a sequência de cliques para entrar no jogo."""
        self.log = self.emu.log
        self.log.info(f"=== Iniciando Navegação Inicial - Instância {self.emu.instance_id} ===")

        # 1. Aguardar e clicar em 'Aceitar' (Termos de Uso)
        if self.vision.wait_for_element("aceitar.png", timeout=20, click_on_find=True):
            self.log.info("[1/4] Termos aceitos.")
            time.sleep(2)
        
        # 2. Verificar se a conta está bloqueada antes de prosseguir
        if self.block_handler.is_account_blocked():
            self.block_handler.handle_blocked_account()
            return False

        # 3. Clicar em 'Visitante'
        if self.vision.wait_for_element("visitante.png", timeout=15, click_on_find=True):
            self.log.info("[2/4] Login como Visitante realizado.")
            time.sleep(5) # Espera o lobby carregar

        # 4. Selecionar 'Poker Brasil'
        if self.vision.wait_for_element("poker_brasil.png", timeout=20, click_on_find=True):
            self.log.info("[3/4] Modo Poker Brasil selecionado.")
            time.sleep(2)

        # 5. Clicar em 'Jogar Agora'
        if self.vision.wait_for_element("jogar_agora.png", timeout=15, click_on_find=True):
            self.log.info("[4/4] Bot entrou na fila de jogo!")
            return True

        self.log.error("Falha na navegação: Algum elemento não foi encontrado.")
        return False

if __name__ == "__main__":
    # Teste rápido na Instância 0
    bot = AccountCreatorBot(instance_id=0)
    bot.run_initial_navigation()