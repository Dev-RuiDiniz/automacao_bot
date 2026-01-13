from core.emulator_manager import EmulatorManager
from actions.image_recognition import ImageRecognition
from actions.click_actions import ClickActions
from actions.ui_cleaner import UICleaner
from core.block_handler import BlockHandler
from core.instance_manager import InstanceManager 
from core.account_registry import AccountRegistry
from actions.daily_bonus import DailyBonus
from actions.maturation_manager import MaturationManager
from actions.slot_manager import SlotManager
from actions.nickname_manager import NicknameManager
import time

class NewAccountOrchestrator:
    """
    Orquestrador Final: Une todos os módulos para criar, maturar 
    e registrar contas de forma autônoma.
    """
    def __init__(self, instance_id):
        # Inicializa a infraestrutura da instância
        self.emu = EmulatorManager(instance_id=instance_id)
        self.vision = ImageRecognition(self.emu, instance_id=instance_id)
        self.click = ClickActions(self.emu, instance_id=instance_id)
        self.log = self.emu.log
        
        # Módulos de Lógica, Segurança e Persistência
        self.block_handler = BlockHandler(self.emu, instance_id=instance_id)
        self.inst_manager = InstanceManager(self.emu) 
        self.registry = AccountRegistry()
        self.cleaner = UICleaner(self.emu, instance_id=instance_id)
        self.bonus = DailyBonus(self.emu, instance_id=instance_id)
        self.slot = SlotManager(self.emu, instance_id=instance_id)
        self.nick = NicknameManager(self.emu, instance_id=instance_id)
        self.maturation = MaturationManager(self.emu, instance_id=instance_id)

    def run(self):
        """
        Executa o pipeline completo de criação de conta.
        Retornos: 'SUCCESS', 'RECYCLE' (bloqueio), ou 'FAILED' (erro técnico).
        """
        self.log.info(f"🚀 [INÍCIO] Orquestrando Instância {self.emu.instance_id}")

        # --- ETAPA 1: SEGURANÇA E HIGIENE (Tarefa 8) ---
        # Verifica se o ambiente está limpo ou se o IP está marcado
        if self.block_handler.is_account_blocked():
            self.log.critical(f"🚫 Bloqueio detectado no startup da Instância {self.emu.instance_id}")
            self.inst_manager.delete_instance(self.emu.instance_id)
            return "RECYCLE"

        # --- ETAPA 2: NAVEGAÇÃO E LOGIN (Tarefas 1 e 2) ---
        if self.vision.wait_for_element("aceitar.png", timeout=20, click_on_find=True):
            self.log.info("✅ Termos aceitos.")
            time.sleep(2)

        if not self.vision.wait_for_element("visitante.png", timeout=15, click_on_find=True):
            self.log.error("❌ Botão 'Visitante' não encontrado. Abortando.")
            return "FAILED"
        
        self.log.info("⏳ Aguardando criação da conta no servidor...")
        time.sleep(15) # Delay necessário para estabilização do lobby

        # --- ETAPA 3: IDENTIDADE E RECOMPENSAS (Tarefas 4 e 7) ---
        self.log.info("👤 Configurando perfil e coletando bônus...")
        nome_gerado = self.nick.change_nickname()
        self.bonus.check_and_spin()
        
        # --- ETAPA 4: LIMPEZA DE INTERFACE (Tarefa 3) ---
        # Remove pop-ups de boas-vindas e promoções agressivas
        self.cleaner.clean_ui(iterations=3)

        # --- ETAPA 5: MATURAÇÃO 1 - SLOTS (Tarefa 6) ---
        # Gera volume de apostas rápido: 9 linhas, aposta 2, 10 minutos.
        self.log.info("🎰 Iniciando Maturação via Slots (Aquecimento de XP)...")
        self.slot.setup_and_run(duration_minutes=10)
        
        self.cleaner.clean_ui(iterations=2) # Limpa pop-ups de ganho ou level up

        # --- ETAPA 6: MATURAÇÃO 2 - MESA POKER (Tarefa 5) ---
        # Simula presença humana em mesas reais por 10 minutos (Anti-AFK)
        self.log.info("🃏 Transicionando para mesas de Poker (Simulação Humana)...")
        if self.vision.wait_for_element("poker_brasil.png", timeout=20, click_on_find=True):
            time.sleep(5)
            if self.vision.wait_for_element("jogar_agora.png", timeout=15, click_on_find=True):
                if self.maturation.stay_on_table(duration_minutes=10):
                    
                    # --- ETAPA 7: FINALIZAÇÃO E REGISTRO (Tarefa 9) ---
                    # Salva os dados no banco JSON e encerra o emulador
                    self.log.info("💾 Ciclo finalizado. Registrando conta...")
                    self.registry.register_account(nome_gerado, self.emu.instance_id)
                    
                    # Força o fechamento para liberar RAM para as próximas instâncias
                    self.emu._execute_memuc(['adb', '-i', str(self.emu.instance_id), 'shell', 'am', 'force-stop', 'com.poker.package'])
                    
                    self.log.info(f"🏆 [SUCESSO] Instância {self.emu.instance_id} concluiu o ciclo!")
                    return "SUCCESS"

        self.log.error("❌ Falha na etapa de maturação final.")
        return "FAILED"

if __name__ == "__main__":
    # Teste de execução individual
    orchestrator = NewAccountOrchestrator(instance_id=0)
    status = orchestrator.run()
    print(f"\nResultado da Orquestração: {status}")