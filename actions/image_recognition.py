import cv2
import numpy as np
import os
import time

class ImageRecognition:
    """
    Sistema de Visão Computacional para automação de instâncias Android.
    Utiliza OpenCV (Template Matching) para localizar elementos de UI através de comandos ADB.
    """

    def __init__(self, emulator_manager, instance_id=0):
        """
        Inicializa o sistema de reconhecimento para uma instância específica.
        
        :param emulator_manager: Objeto de controle do ciclo de vida do emulador.
        :param instance_id: ID numérico da instância no MEmu.
        """
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log
        
        # Diretórios de saída
        self.temp_dir = "logs/screenshots"
        self.error_dir = "logs/errors"
        
        for directory in [self.temp_dir, self.error_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def _take_screenshot(self, custom_path=None):
        """Captura a tela com verificação de integridade."""
        save_path = custom_path if custom_path else os.path.join(self.temp_dir, f"screen_{self.instance_id}.png")
        remote_path = f"/sdcard/screen_{self.instance_id}.png"
        
        # 1. Tira o print
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'screencap', '-p', remote_path])
        
        # 2. Puxa para o PC
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'pull', remote_path, save_path])
        
        # 3. VERIFICAÇÃO REAL
        if os.path.exists(save_path):
            return save_path
        else:
            self.log.error(f"FATAL: ADB Pull falhou. Verifique se a instância {self.instance_id} tem espaço no /sdcard/.")
            # Fallback para o comando interno do MEmu se o ADB falhar
            self.emu._execute_memuc(['screencap', '-i', str(self.instance_id), '-f', save_path])
            return save_path

    def _save_error_snapshot(self, element_name):
        """
        Registra uma evidência visual em caso de falha crítica (Timeout).
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"ERR_{self.instance_id}_{element_name}_{timestamp}.png"
        path = os.path.join(self.error_dir, filename)
        self._take_screenshot(custom_path=path)
        self.log.critical(f"📸 Screenshot de erro gerado: {path}")

    def find_element(self, template_name, threshold=0.8, click=False):
        """
        Executa a busca por um padrão de imagem (template) na tela atual.
        
        :param template_name: Nome da imagem em assets/buttons/.
        :param threshold: Nível de confiança (0.0 a 1.0).
        :param click: Se True, executa o TAP no centro do elemento encontrado.
        :return: Tupla (x, y) das coordenadas reais ou None.
        """
        template_path = os.path.join("assets/buttons", template_name)
        
        if not os.path.exists(template_path):
            self.log.error(f"Arquivo de template ausente: {template_path}")
            return None

        # Processamento de Imagem
        screen_path = self._take_screenshot()
        img_rgb = cv2.imread(screen_path)
        template = cv2.imread(template_path)
        
        # Conversão para escala de cinza (otimização de performance)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        w, h = template_gray.shape[::-1]

        # Template Matching
        res = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            
            self.log.info(f"Elemento '{template_name}' localizado (Confiança: {max_val:.2f})")
            
            if click:
                from actions.click_actions import ClickActions
                ca = ClickActions(self.emu, self.instance_id)
                ca.tap(center_x, center_y, normalize=False) # Coordenada já é real
                
            return (center_x, center_y)
        
        return None

    def wait_for_element(self, template_name, timeout=30, interval=2, threshold=0.8, click_on_find=False):
        """
        Pausa o fluxo de trabalho até que a condição visual seja satisfeita.
        Implementa fallback de erro com salvamento de imagem.
        """
        self.log.info(f"[*] Aguardando visual de '{template_name}' (Limite: {timeout}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            pos = self.find_element(template_name, threshold=threshold)
            
            if pos:
                if click_on_find:
                    from actions.click_actions import ClickActions
                    ca = ClickActions(self.emu, self.instance_id)
                    ca.tap(pos[0], pos[1], normalize=False)
                return pos
            
            time.sleep(interval)
            
        # Tratamento de Timeout
        self.log.error(f"[!] Falha: '{template_name}' não encontrado no tempo estipulado.")
        self._save_error_snapshot(template_name.split('.')[0])
        return None