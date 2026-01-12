import cv2
import pytesseract
import numpy as np
import os

class OCRManager:
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log
        
        # AJUSTE AQUI: Caminho do executável no novo PC
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def _preprocess_for_ocr(self, img_array):
        """
        Transforma a imagem para facilitar a leitura do Tesseract.
        Converte para cinza, aumenta escala e aplica Threshold de Otsu.
        """
        # 1. Escala de cinza
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        
        # 2. Redimensiona (Dobrar o tamanho ajuda o OCR a ler fontes pequenas)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # 3. Threshold (Deixa o fundo branco e texto preto)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        return thresh

    def get_text_from_region(self, region_name):
        """
        Lê texto de uma região definida no config/timings.json.
        Ex de região no JSON: "regiao_nickname": {"x": 100, "y": 20, "w": 200, "h": 50}
        """
        # 1. Pega as coordenadas do JSON
        reg = self.emu.config.timings.get("ui_regions", {}).get(region_name)
        if not reg:
            self.log.error(f"Região {region_name} não definida no timings.json")
            return ""

        # 2. Tira o print e carrega
        from actions.image_recognition import ImageRecognition
        ir = ImageRecognition(self.emu, self.instance_id)
        screen_path = ir._take_screenshot()
        img = cv2.imread(screen_path)

        # 3. Recorta a imagem (Crop) [y:y+h, x:x+w]
        crop_img = img[reg['y']:reg['y']+reg['h'], reg['x']:reg['x']+reg['w']]
        
        # 4. Pré-processa
        processed = self._preprocess_for_ocr(crop_img)
        
        # 5. OCR - PSM 6 (Assume um único bloco de texto) ou PSM 7 (Uma única linha)
        custom_config = r'--oem 3 --psm 7'
        text = pytesseract.image_to_string(processed, config=custom_config)
        
        result = text.strip()
        self.log.info(f"OCR ({region_name}): {result}")
        return result