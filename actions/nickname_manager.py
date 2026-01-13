import time
from core.name_generator import NameGenerator
from actions.click_actions import ClickActions

class NicknameManager:
    """
    Gerencia a alteração do Nickname padrão para um nome único gerado aleatoriamente.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.vision = None
        self.log = emulator_manager.log
        self.name_gen = NameGenerator() # Gerador do Dia 2
        self.click = ClickActions(self.emu, self.instance_id)

    def change_nickname(self):
        """Abre o perfil e altera o nome da conta."""
        from actions.image_recognition import ImageRecognition
        if not self.vision: self.vision = ImageRecognition(self.emu, self.instance_id)

        self.log.info(f"[*] Iniciando alteração de Nickname na Instância {self.instance_id}...")

        # 1. Clicar no Ícone de Perfil/Avatar
        if not self.vision.wait_for_element("profile/icone_perfil.png", timeout=15, click_on_find=True):
            self.log.error("[-] Não foi possível abrir o perfil.")
            return False
        time.sleep(2)

        # 2. Clicar no botão de Editar Nome
        if not self.vision.wait_for_element("profile/btn_editar_nome.png", timeout=10, click_on_find=True):
            self.log.warning("[-] Botão de editar nome não encontrado.")
            return False

        # 3. Gerar novo nome e digitar via ADB
        novo_nome = self.name_gen.generate_human_like()
        self.log.info(f"[+] Novo nome gerado: {novo_nome}")

        # Clica no campo de input para focar o teclado
        self.vision.find_element("profile/campo_input_nome.png", click=True)
        time.sleep(1)

        # Comando ADB para apagar o nome antigo (vários backspaces) e digitar o novo
        # Simulamos 15 backspaces para limpar o campo
        for _ in range(15):
            self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'keyevent', '67'])
        
        # Digita o novo nome
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'text', novo_nome])
        time.sleep(1)

        # 4. Confirmar alteração
        if self.vision.find_element("profile/btn_confirmar_nome.png", click=True):
            self.log.info(f"[✅] Nickname alterado com sucesso para: {novo_nome}")
            time.sleep(2)
            # Fecha a tela de perfil (usando o limpador de UI ou um clique no X)
            self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'keyevent', '4']) # Tecla 'Back' do Android
            return novo_nome
        
        return False