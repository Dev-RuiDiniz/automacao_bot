import time

class DailyBonus:
    """
    Gerencia o bônus diário e giros de roleta para ganho de fichas iniciais.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.vision = None # Inicializado via Lazy Loading
        self.log = emulator_manager.log

    def check_and_spin(self):
        """
        Detecta se a roleta está na tela e realiza o giro.
        """
        from actions.image_recognition import ImageRecognition
        if not self.vision:
            self.vision = ImageRecognition(self.emu, self.instance_id)

        self.log.info(f"[*] Verificando presença de Roleta Diária na Instância {self.instance_id}...")

        # 1. Tenta localizar o botão de Girar
        # Usamos threshold 0.7 pois roletas costumam ter brilhos e animações
        pos_spin = self.vision.wait_for_element("ui/roleta_center.png", timeout=10, threshold=0.7)

        if pos_spin:
            self.log.info("[+] Roleta detectada! Girando...")
            # Clica no centro da roleta
            from actions.click_actions import ClickActions
            ca = ClickActions(self.emu, self.instance_id)
            ca.tap(pos_spin[0], pos_spin[1], normalize=False)
            
            # 2. Aguarda a animação da roleta parar (geralmente 5 a 8 segundos)
            self.log.info("[*] Aguardando sorteio das fichas...")
            time.sleep(10)

            # 3. Tenta coletar o prêmio
            pos_collect = self.vision.find_element("ui/coletar_roleta.png", threshold=0.7, click=True)
            if pos_collect:
                self.log.info("[SUCESSO] Fichas da roleta coletadas!")
                time.sleep(2)
                return True
            else:
                self.log.warning("[!] Botão coletar não encontrado, talvez tenha coletado automático.")
                return True
        
        self.log.info("[-] Nenhuma roleta detectada no momento.")
        return False