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

    def stay_on_table(self, duration_minutes=10):
        """
        Mantém o bot na mesa pelo tempo determinado, realizando cliques aleatórios.
        """
        from actions.image_recognition import ImageRecognition
        from actions.click_actions import ClickActions
        
        if not self.vision: self.vision = ImageRecognition(self.emu, self.instance_id)
        if not self.click: self.click = ClickActions(self.emu, self.instance_id)

        self.log.info(f"[*] Iniciando maturação da conta ({duration_minutes} min) na mesa...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            elapsed = int((time.time() - start_time) / 60)
            self.log.info(f"[Maturação] Tempo decorrido: {elapsed}/{duration_minutes} min.")

            # 1. Verifica se ainda está na mesa (evita ter caído da conexão)
            if not self.vision.find_element("ui/mesa_ativa.png", threshold=0.7):
                self.log.warning("[!] Bot parece ter saído da mesa. Tentando reentrar...")
                # Aqui você poderia chamar o run_initial_navigation novamente
                break

            # 2. Simula interação humana (cliques em áreas vazias ou emotes)
            # Isso evita que o Android ou o Jogo entrem em modo ocioso
            x = random.randint(100, 1000)
            y = random.randint(100, 500)
            self.log.info(f"[*] Movimento anti-afk em ({x}, {y})")
            self.click.tap(x, y, normalize=False)

            # 3. Espera entre 30 a 90 segundos para a próxima interação
            wait_time = random.randint(30, 90)
            time.sleep(wait_time)

        self.log.info(f"[✅] Maturação concluída para a instância {self.instance_id}.")
        return True