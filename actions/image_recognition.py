import cv2
import numpy as np
import os
import time

class ImageRecognition:
    def __init__(self, emulator_manager, instance_id=0):
        """
        Classe para reconhecimento de imagem via OpenCV.
        :param emulator_manager: Instância do gerenciador para usar comandos ADB.
        :param instance_id: ID da instância do MEmu a ser monitorada.
        """
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log
        
        # Pasta temporária para screenshots
        self.temp_dir = "logs/screenshots"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def _take_screenshot(self):
        """Captura a tela atual do emulador e salva localmente."""
        save_path = os.path.join(self.temp_dir, f"screen_{self.instance_id}.png")
        remote_path = f"/sdcard/screen_{self.instance_id}.png"
        
        # 1. Tira o print dentro do Android
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'screencap', '-p', remote_path])
        # 2. Puxa o arquivo para o PC
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'pull', remote_path, save_path])
        
        return save_path

    def find_element(self, template_name, threshold=0.8, click=False):
        """
        Localiza um elemento na tela.
        :param template_name: Nome do arquivo em assets/buttons/ (ex: 'jogar.png')
        :param threshold: Precisão da busca (0.0 a 1.0)
        :param click: Se True, executa o clique se encontrar
        :return: (x, y) se encontrado, None caso contrário
        """
        template_path = os.path.join("assets/buttons", template_name)
        
        if not os.path.exists(template_path):
            self.log.error(f"Template não encontrado: {template_path}")
            return None

        # Captura e carrega as imagens
        screen_path = self._take_screenshot()
        img_rgb = cv2.imread(screen_path)
        template = cv2.imread(template_path)
        
        # Converte para tons de cinza para aumentar a performance
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        w, h = template_gray.shape[::-1]

        # Executa o matchTemplate
        res = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            # Calcula o centro do elemento
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            
            self.log.info(f"Elemento {template_name} encontrado com {max_val:.2f} de precisão em ({center_x}, {center_y})")
            
            if click:
                from actions.click_actions import ClickActions
                ca = ClickActions(self.emu, self.instance_id)
                ca.tap(center_x, center_y)
                
            return (center_x, center_y)
        
        return None

    def wait_for_element(self, template_name, timeout=30, interval=2):
        """Aguarda um elemento aparecer na tela por um determinado tempo."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            pos = self.find_element(template_name)
            if pos:
                return pos
            time.sleep(interval)
        
        self.log.warning(f"Timeout aguardando elemento: {template_name}")
        return None