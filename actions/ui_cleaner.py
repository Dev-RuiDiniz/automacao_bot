import os
import time

class UICleaner:
    """
    Módulo responsável por detetar e fechar pop-ups, anúncios e janelas inesperadas.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.vision = None # Será inicializado para evitar import circular
        self.log = emulator_manager.log
        
        # Lista de elementos que representam "Fechar" ou "Sair"
        self.pop_up_elements = [
            "close_x.png", 
            "close_red.png", 
            "recolher.png", 
            "entendi.png",
            "cancelar.png"
        ]

    def clean_ui(self, iterations=3):
        """
        Tenta localizar e clicar em botões de fechar. 
        Executa várias vezes pois um pop-up pode estar atrás de outro.
        """
        from actions.image_recognition import ImageRecognition
        if not self.vision:
            self.vision = ImageRecognition(self.emu, self.instance_id)

        self.log.info(f"[*] Iniciando limpeza de UI na Instância {self.instance_id}...")
        
        found_any = False
        for i in range(iterations):
            current_found = False
            for element in self.pop_up_elements:
                # Usamos um threshold ligeiramente menor (0.7) para garantir que pegamos o 'X'
                pos = self.vision.find_element(f"ui/{element}", threshold=0.7, click=True)
                
                if pos:
                    self.log.info(f"[!] Pop-up detectado e fechado: {element}")
                    time.sleep(1.5) # Espera a animação de fechar
                    current_found = True
                    found_any = True
            
            # Se não encontrou nada nesta iteração, a tela provavelmente está limpa
            if not current_found:
                break
                
        return found_any