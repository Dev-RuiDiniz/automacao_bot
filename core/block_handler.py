from actions.image_recognition import ImageRecognition
from actions.ocr_manager import OCRManager
import time

class BlockHandler:
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log
        self.img_rec = ImageRecognition(self.emu, self.instance_id)
        self.ocr = OCRManager(self.emu, self.instance_id)

    def is_account_blocked(self):
        """
        Verifica se a tela atual contém indícios de bloqueio.
        """
        # 1. Busca por imagem (ex: ícone de cadeado ou exclamação vermelha)
        if self.img_rec.find_element("popup_bloqueio.png", threshold=0.9):
            self.log.error(f"Instância {self.instance_id}: Janela de bloqueio detectada por imagem.")
            return True

        # 2. Busca por texto (OCR) - Palavras-chave de banimento
        try:
            texto_erro = self.ocr.get_text_from_region("aviso_bloqueio").lower()
            palavras_chave = ["suspenso", "bloqueada", "banido", "restringida", "violacao", "blocked"]
            
            if any(palavra in texto_erro for palavra in palavras_chave):
                self.log.error(f"Instância {self.instance_id}: Bloqueio confirmado via OCR: '{texto_erro}'")
                return True
        except Exception as e:
            self.log.warning(f"Falha ao processar OCR de bloqueio: {e}")

        return False

    def handle_blocked_account(self):
        """
        Ação a ser tomada se bloqueado: Fecha, remove e marca no log.
        """
        self.log.critical(f"Iniciando descarte da instância {self.instance_id} por bloqueio.")
        
        # 1. Tira print da prova do bloqueio
        self.img_rec._take_screenshot() 
        
        # 2. Fecha o emulador
        self.emu.stop_instance()
        
        # 3. Futuro: Chamar AccountManager para marcar como 'banned' no accounts.json
        self.log.info(f"Instância {self.instance_id} marcada para revisão/exclusão.")