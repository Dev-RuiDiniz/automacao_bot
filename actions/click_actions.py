from core.ui_utils import UIUtils

class ClickActions:
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        
        # Obtém resolução atual e prepara o normalizador
        w, h = self.emu.get_screen_resolution(instance_id)
        self.utils = UIUtils(current_width=w, current_height=h)

    def tap(self, x, y, normalize=True):
        """Executa o clique, aplicando normalização se necessário."""
        if normalize:
            final_x, final_y = self.utils.normalize(x, y)
        else:
            final_x, final_y = x, y
            
        return self.emu._execute_memuc([
            'adb', '-i', str(self.instance_id), 
            'shell', 'input', 'tap', str(final_x), str(final_y)
        ])