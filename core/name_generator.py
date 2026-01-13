import random
import string

class NameGenerator:
    """
    Utilitário para geração de nicknames únicos para evitar detecção de padrões.
    """

    def __init__(self):
        # Listas para simular nomes "humanos"
        self.prefixes = ["Luck", "King", "Vip", "Pro", "Player", "Star", "Mega", "Win"]
        self.suffixes = ["BR", "Alpha", "Zero", "99", "XP", "Master", "Gold"]

    def generate_human_like(self):
        """Gera nomes como 'LuckAlpha_42' ou 'StarPlayer88'."""
        pre = random.choice(self.prefixes)
        suf = random.choice(self.suffixes)
        num = random.randint(10, 999)
        separator = random.choice(["", "_", ""])
        return f"{pre}{separator}{suf}{num}"

    def generate_alphanumeric(self, length=10):
        """Gera uma string aleatória pura, ex: 'a7B2kL91pQ'."""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_custom(self, base_name):
        """Adiciona sufixo aleatório a um nome base."""
        return f"{base_name}{random.randint(100, 999)}"