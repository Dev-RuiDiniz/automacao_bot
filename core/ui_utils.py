class UIUtils:
    def __init__(self, current_width, current_height, base_width=1280, base_height=720):
        """
        Calcula a escala entre a resolução mapeada e a resolução atual.
        """
        self.scale_x = current_width / base_width
        self.scale_y = current_height / base_height

    def normalize(self, x, y):
        """Converte coordenadas base para as coordenadas reais do emulador."""
        real_x = int(x * self.scale_x)
        real_y = int(y * self.scale_y)
        return real_x, real_y