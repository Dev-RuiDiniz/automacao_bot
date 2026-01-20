import time
import random

class MaturationManager:
    """
    Responsável por manter a conta ativa na mesa para simular comportamento humano
    e evitar detecção de bots de criação em massa.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.vision = None
        self.click = None
        self.log = emulator_manager.log
        # Carrega configurações do settings.yaml
        self.config = getattr(self.emu, 'settings', {})

    def _ensure_tools(self):
        """Garante que as ferramentas de visão e clique estejam inicializadas."""
        from actions.image_recognition import ImageRecognition
        from actions.click_actions import ClickActions
        
        if not self.vision: self.vision = ImageRecognition(self.emu, self.instance_id)
        if not self.click: self.click = ClickActions(self.emu, self.instance_id)

    def quick_table_exit(self):
        """
        Entra em uma mesa via 'Jogar Já', aguarda 10 segundos e sai.
        Útil para gerar atividade rápida na conta.
        """
        self._ensure_tools()
        self.log.info(f"[*] Executando Quick Table Exit na instância {self.instance_id}...")

        # 1. Clicar em 'Jogar Já' (Assumindo que o botão está no lobby)
        if self.vision.wait_for_element("btn_jogar_ja.png", timeout=15, click_on_find=True):
            self.log.info("[+] Entrou na mesa. Aguardando 10 segundos...")
            
            # 2. Espera de 10 segundos (simulando observação)
            time.sleep(10)

            # 3. Sair da mesa
            # Tenta clicar no botão de menu/sair e confirmar a saída
            if self.vision.find_element("btn_menu_mesa.png", click=True):
                time.sleep(1)
                if self.vision.find_element("btn_sair_confirmar.png", click=True):
                    self.log.info("[✅] Saída da mesa realizada com sucesso.")
                    return True
        
        self.log.error("[-] Falha ao executar Quick Table Exit.")
        return False

    def stay_on_table(self, duration_minutes=None):
        """
        Mantém o bot na mesa pelo tempo determinado, realizando cliques aleatórios.
        """
        self._ensure_tools()
        
        # Usa o valor do settings ou o padrão de 10 min
        if duration_minutes is None:
            duration_minutes = self.config.get('maturation', {}).get('duration', 10)

        self.log.info(f"[*] Iniciando maturação ({duration_minutes} min) na mesa...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            # Verifica se ainda está na mesa
            if not self.vision.find_element("ui/mesa_ativa.png", threshold=0.7):
                self.log.warning("[!] Bot saiu da mesa prematuramente.")
                break

            # Simula interação humana
            x = random.randint(100, 1000)
            y = random.randint(100, 500)
            self.click.tap(x, y, normalize=False)

            wait_time = random.randint(30, 90)
            time.sleep(wait_time)

        return True