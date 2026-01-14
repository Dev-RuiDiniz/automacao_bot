import time
import os
from core.name_generator import NameGenerator
from actions.click_actions import ClickActions

class NicknameManager:
    """
    Gerencia a alteração do Nickname com suporte a limpeza profunda, 
    confirmação de pop-ups e tratamento de erro de '15 dias'.
    """
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log
        self.name_gen = NameGenerator()
        self.click = ClickActions(self.emu, self.instance_id)
        
        from actions.image_recognition import ImageRecognition
        self.vision = ImageRecognition(self.emu, self.instance_id)

    def change_nickname(self):
        """Fluxo completo com tratamento de erro de nome já alterado."""
        self.log.info(f"[*] Iniciando alteração de Nickname na Instância {self.instance_id}...")

        # 1. Abrir Perfil
        if not self.vision.wait_for_element("icone_perfil.PNG", timeout=15, click_on_find=True):
            self.log.error("[-] Não foi possível abrir o perfil.")
            return False
        time.sleep(3)

        # 2. Clicar em Editar
        if not self.vision.wait_for_element("btn_editar_nome.PNG", timeout=10, click_on_find=True):
            # Verifica se aparece a mensagem que já mudou o nome (bloqueio de 15 dias)
            if self.vision.find_element("menssagem_nome.PNG"):
                self.log.warning("[!] Nome já foi alterado recentemente. Encerrando fluxo.")
                self.vision.find_element("Capturar.PNG", click=True) # Clica no OK azul da mensagem
                time.sleep(2)
                self._back_to_lobby()
                return "ALREADY_CHANGED"
            return False
        
        time.sleep(2)

        # 3. Limpeza do campo e Digitação
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'tap', '640', '330'])
        time.sleep(1)
        
        # Limpeza agressiva
        for _ in range(30):
            self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'keyevent', '67'])
        
        novo_nome = self.name_gen.generate_human_like()
        nome_adb = "".join(c for c in novo_nome if c.isalnum() or c == ' ').replace(" ", "%s")
        
        self.log.info(f"[+] Digitando novo nome: {novo_nome}")
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'text', nome_adb])
        time.sleep(1)
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'keyevent', '66']) # Enter
        time.sleep(2)

        # 4. Confirmar na Interface
        if not self.vision.wait_for_element("btn_confirmar_nome.PNG", timeout=8, click_on_find=True):
            self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'keyevent', '66'])

        # 5. Lidar com Pop-ups de Sucesso ou Erro após confirmar
        time.sleep(3)
        
        # Caso A: Pop-up de Aviso/Confirmação (Sucesso - perguntando se tem certeza)
        if self.vision.find_element("confirma_nome_ok.PNG", click=True):
            self.log.info("✅ Nome confirmado no pop-up de sucesso.")
            time.sleep(2)
        
        # Caso B: Mensagem de erro (Você não pode mudar o seu nome...)
        elif self.vision.find_element("menssagem_nome.PNG"):
            self.log.warning("[!] Erro: O sistema recusou a mudança (limite de 15 dias).")
            self.vision.find_element("confirmar_popup_nome.PNG", click=True) # Clica no OK azul
            time.sleep(2)

        # 6. Finalização: Voltar ao Lobby
        self._back_to_lobby()
        return novo_nome

    def _back_to_lobby(self):
        """Garante a saída de qualquer tela de perfil para o lobby."""
        self.log.info("[*] Retornando ao Lobby...")
        # Tenta fechar pelo 'X'
        if not self.vision.find_element("encerra_nome.PNG", click=True):
            # Se não achar o X, usa o botão voltar do Android
            self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'input', 'keyevent', '4'])
        
        time.sleep(2)