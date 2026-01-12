import time

class ClickActions:
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id

    def tap(self, x, y):
        """Executa um clique (tap) em coordenadas X, Y"""
        # Comando: memuc adb -i <index> shell input tap <x> <y>
        return self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'tap', str(x), str(y)])

    def home_button(self):
        """Simula o botão Home do Android"""
        return self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'keyevent', '3'])

    def back_button(self):
        """Simula o botão Voltar"""
        return self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'keyevent', '4'])