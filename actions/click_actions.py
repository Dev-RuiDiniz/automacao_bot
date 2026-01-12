import time
from core.ui_utils import UIUtils

class ClickActions:
    def __init__(self, emulator_manager, instance_id=0, base_res=(1280, 720)):
        """
        Gerencia ações de entrada (touch) no emulador.
        :param base_res: Resolução em que os pontos de UI foram mapeados (padrão 720p).
        """
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log
        
        # Detecta resolução real para normalização
        curr_w, curr_h = self.emu.get_screen_resolution(instance_id)
        self.utils = UIUtils(current_width=curr_w, current_height=curr_h, 
                             base_width=base_res[0], base_height=base_res[1])
        
        self.log.info(f"ClickActions configurado: Escala base {base_res} -> Real {curr_w}x{curr_h}")

    def tap(self, x, y, normalize=True):
        """Executa um clique simples (tap)."""
        if normalize:
            x, y = self.utils.normalize(x, y)
        
        self.log.info(f"Executando TAP em ({x}, {y})")
        return self.emu._execute_memuc([
            'adb', '-i', str(self.instance_id), 
            'shell', 'input', 'tap', str(x), str(y)
        ])

    def double_tap(self, x, y, interval=0.2, normalize=True):
        """Executa dois cliques rápidos no mesmo local."""
        self.tap(x, y, normalize)
        time.sleep(interval)
        return self.tap(x, y, normalize)

    def long_press(self, x, y, duration_ms=1500, normalize=True):
        """
        Simula um clique longo usando o comando swipe no mesmo ponto.
        No Android ADB, um swipe com a mesma origem e destino funciona como long press.
        """
        if normalize:
            x, y = self.utils.normalize(x, y)
            
        self.log.info(f"Executando LONG PRESS em ({x}, {y}) por {duration_ms}ms")
        return self.emu._execute_memuc([
            'adb', '-i', str(self.instance_id), 
            'shell', 'input', 'swipe', 
            str(x), str(y), str(x), str(y), str(duration_ms)
        ])

    def swipe(self, x1, y1, x2, y2, duration_ms=500, normalize=True):
        """Executa um deslize (swipe) entre dois pontos."""
        if normalize:
            x1, y1 = self.utils.normalize(x1, y1)
            x2, y2 = self.utils.normalize(x2, y2)
            
        return self.emu._execute_memuc([
            'adb', '-i', str(self.instance_id), 
            'shell', 'input', 'swipe', 
            str(x1), str(y1), str(x2), str(y2), str(duration_ms)
        ])