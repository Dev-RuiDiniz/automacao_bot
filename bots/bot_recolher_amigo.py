import threading
import time
import os
from core.emulator_manager import EmulatorManager
from actions.image_recognition import ImageRecognition
from actions.click_actions import ClickActions
from actions.ui_cleaner import UICleaner
from core.instance_manager import InstanceManager

class BotOrquestradorMestre:
    """
    Orquestrador unificado para execução do fluxo de automação completo.
    Segue rigorosamente as 10 etapas descritas no PDF técnico.
    """
    def __init__(self, instance_id):
        self.emu = EmulatorManager(instance_id=instance_id)
        self.vision = ImageRecognition(self.emu, instance_id=instance_id)
        self.click = ClickActions(self.emu, instance_id=instance_id)
        self.log = self.emu.log
        self.cleaner = UICleaner(self.emu, instance_id=instance_id)
        
        # Paths de assets e pacote
        self.img_path = "buttons/bot_recolher_amigo/"
        self.package = "com.playshoo.texaspoker.romania"

    def run(self):
        """Executa o ciclo de vida completo da instância."""
        self.log.info(f"[INSTÂNCIA {self.emu.instance_id}] Iniciando fluxo completo.")

        try:
            # 1. ABERTURA DO JOGO E TRATAMENTO DE ERROS
            self.emu.launch_app(self.package)
            if not self.vision.wait_for_element("/05_tela_inical.PNG", timeout=30):
                self.log.warning("⚠️ Tela home não detectada. Iniciando limpeza de UI...")
                self.cleaner.clean_ui(iterations=3) # 3. CONFIRMAÇÃO DA TELA INICIAL

            # 2. ROLETAS INICIAIS (SE DISPONÍVEL)
            if self.vision.exists("/02_roda_fortuna.PNG"):
                self.log.info(" Roleta inicial detectada.")
                self.vision.wait_for_element("/03_roleta.PNG", click_on_find=True)
                time.sleep(12) # Tempo para animação

            # 4. MÓDULO AMIGOS (EXECUTADO 3 VEZES)
            for ciclo in range(1, 4):
                self.log.info(f" Módulo Amigos: Ciclo {ciclo}/3")
                if self.vision.wait_for_element(f"{self.img_path}07_amigos.PNG", timeout=10, click_on_find=True): #
                    if self.vision.wait_for_element(f"{self.img_path}08_meus_amigos.PNG", timeout=10): #
                        self.process_gifts() # 4.2 Coleta e Envio
                        self.vision.wait_for_element(f"{self.img_path}09_retorna.PNG", timeout=10, click_on_find=True) #
                time.sleep(2)

            # 5. ROLETAS PRINCIPAIS
            if self.vision.wait_for_element("10_jogar_roleta.PNG", timeout=10, click_on_find=True):
                for giro in range(2): # 5.2 Execução de 2 giros
                    self.log.info(f"Giro de roleta {giro + 1}/2")
                    self.vision.wait_for_element("12_rolar_roleta.PNG", timeout=10, click_on_find=True)
                    time.sleep(8) # Aguarda resultado
                self.vision.wait_for_element("12_sair_roleta.PNG", timeout=10, click_on_find=True) #

            # ======================================================================
            # 6. NOKO BOX (REVISADO: ALTERNÂNCIA DE ABA/APP)
            # ======================================================================
            self.log.info("Iniciando transição para Módulo Noko Box...")

            # Segundo o fluxo, o bot deve acessar a Noko Box. 
            # Para garantir que estamos na "Página Inicial" do emulador/app:
            self.emu.shell("input keyevent 3") # Comando ADB para pressionar HOME (Página Inicial do MEmu)
            time.sleep(2)

            # Localiza e abre o ícone do Nekobox na tela inicial do emulador
            if self.vision.wait_for_element(f"{self.img_path}icone_nekobox.png", timeout=15, click_on_find=True):
                self.log.info("[+] Aplicativo Nekobox aberto.")
                
                # Aguarda a tela interna do Nekobox carregar [cite: 41, 42]
                if self.vision.wait_for_element(f"{self.img_path}tela_noko_box.png", timeout=15):
                    
                    # Verifica se a Noko Box contém itens (não está vazia) [cite: 43]
                    if not self.vision.exists(f"{self.img_path}noko_vazia.png"):
                        self.log.info("[+] Itens detectados! Realizando abertura da Noko Box.")
                        # Executa o clique de abertura conforme a posição da tela validada [cite: 43]
                        self.click.click_at_element(f"{self.img_path}tela_noko_box.png")
                        time.sleep(5) # Aguarda animação de abertura
                    else:
                        self.log.info("[-] Noko Box identificada como vazia. Pulando coleta.")

                    # Sai do módulo Noko Box para retornar ao fluxo principal 
                    if self.vision.wait_for_element(f"{self.img_path}botao_sair_noko.png", timeout=10, click_on_find=True):
                        self.log.info("[+] Saindo do Nekobox e retornando à Home do jogo.")
                        # Confirma retorno à tela inicial do jogo para o próximo módulo 
                        self.vision.wait_for_element("home/tela_home.png", timeout=15)
            else:
                self.log.error("❌ Falha ao localizar o ícone do Nekobox na Página Inicial.")

            # 7. CONEXÃO VPN (ETAPA CRÍTICA)
            if self.vision.exists("vpn/vpn_desconectada.png"):
                self.vision.wait_for_element("vpn/botao_conectar_vpn.png", click_on_find=True)
                if not self.vision.wait_for_element("vpn/vpn_conectada.png", timeout=30):
                    self.log.error("FALHA CRÍTICA: VPN não conectou.")
                    return "FAILED_CRITICAL"

            # 8. ABERTURA DO CHROME E ACESSO AO BÔNUS
            os.system("am start -n com.android.chrome/com.google.android.apps.chrome.Main")
            time.sleep(5)
            if self.vision.exists("chrome/captcha_detectado.png"):
                self.log.error("Captcha detectado no Chrome. Encerrando instância.")
                return "FAILED_CAPTCHA"

            # 9. COLETA DO BÔNUS NO JOGO
            self.emu.launch_app(self.package) # Retorna ao jogo
            if self.vision.wait_for_element("bonus/botao_bonus_disponivel.png", timeout=15, click_on_find=True):
                self.log.info("Bônus coletado com sucesso.")

            # 10. FINALIZAÇÃO
            self.log.info(f"Instância {self.emu.instance_id} finalizada com sucesso.")
            self.emu.stop_app(self.package)
            return "SUCCESS"

        except Exception as e:
            self.log.error(f"Erro inesperado na instância {self.emu.instance_id}: {e}")
            return "ERROR"

    def process_gifts(self):
        """Lógica de loop para recolher e enviar presentes."""
        max_interacoes = 30 # Limite para evitar loop infinito
        for _ in range(max_interacoes):
            if self.vision.exists(f"{self.img_path}sem_presentes.png"):
                break
            
            recolheu = self.vision.wait_for_element(f"{self.img_path}botao_recolher_presente.png", timeout=2, click_on_find=True)
            enviou_01 = self.vision.wait_for_element(f"{self.img_path}botao_enviar_presente.png", timeout=2, click_on_find=True)
            enviou_02 = self.vision.wait_for_element(f"{self.img_path}botao_enviar_presente_2.png", timeout=2, click_on_find=True)
            
            if not recolheu and not enviou_01 and not enviou_02:
                break
            time.sleep(1)

# ==============================================================================
# GESTOR DE MULTITHREADING (DISTRIBUIDOR)
# ==============================================================================

def executar_instancia(instance_id):
    """Worker para a thread da instância."""
    bot = BotOrquestradorMestre(instance_id)
    bot.run()

if __name__ == "__main__":
    inst_manager = InstanceManager()
    lista_instancias = inst_manager.get_all_instance_ids()
    
    LIMIT_SIMULTANEO = 15 # Conforme solicitado
    DELAY_ABERTURA = 20    # Segundos entre cada abertura
    threads_ativas = []

    print(f"🔥 Iniciando Orquestrador para {len(lista_instancias)} instâncias.")

    for i_id in lista_instancias:
        # Limpa referências de threads mortas
        threads_ativas = [t for t in threads_ativas if t.is_alive()]

        # Gerenciamento de limite simultâneo
        while len(threads_ativas) >= LIMIT_SIMULTANEO:
            time.sleep(5)
            threads_ativas = [t for t in threads_ativas if t.is_alive()]

        # Dispara nova instância
        t = threading.Thread(target=executar_instancia, args=(i_id,))
        t.daemon = True # Morre se o script principal parar
        t.start()
        threads_ativas.append(t)

        print(f"📡 Instância {i_id} lançada. Aguardando {DELAY_ABERTURA}s para a próxima...")
        time.sleep(DELAY_ABERTURA)

    # Aguarda o término de todas as threads antes de fechar o terminal
    for t in threads_ativas:
        t.join()

    print("Todas as instâncias foram processadas.")