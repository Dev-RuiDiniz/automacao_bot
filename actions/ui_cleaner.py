import os
import time

class UICleaner:
    """
    Módulo responsável por detetar e fechar pop-ups, anúncios e janelas inesperadas.
    Atualizado para lidar com promoções pós-roleta.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.vision = None 
        self.log = emulator_manager.log
        
        # Lista expandida com assets de promoções específicas
        self.pop_up_elements = [
            "promo_roleta_close.png", # Promoção que surge logo após a roleta
            "promo_diaria.png",       # Oferta do dia
            "pacote_moedas_x.png",    # Venda de pacotes
            "close_x.png",            # X padrão
            "close_red.png",          # X vermelho
            "recolher.png",           # Botão de recolher prêmio
            "entendi.png",            # Confirmação de aviso
            "cancelar.png"            # Cancelar oferta
        ]

    def clean_ui(self, iterations=5):
        """
        Tenta localizar e clicar em botões de fechar. 
        Aumentamos as iterações para lidar com o empilhamento de promoções.
        """
        from actions.image_recognition import ImageRecognition
        if not self.vision:
            self.vision = ImageRecognition(self.emu, self.instance_id)

        self.log.info(f"[*] Iniciando limpeza de UI na Instância {self.instance_id}...")
        
        found_any = False
        for i in range(iterations):
            current_found = False
            for element in self.pop_up_elements:
                # Busca na subpasta ui/ conforme padrão do projeto
                pos = self.vision.find_element(f"ui/{element}", threshold=0.7, click=True)
                
                if pos:
                    self.log.info(f"[!] Promoção/Pop-up detectado: {element}")
                    time.sleep(2.0) # Tempo aumentado para animações pesadas de promoções
                    current_found = True
                    found_any = True
            
            if not current_found:
                break
                
        return found_any