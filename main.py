from core.emulator_manager import EmulatorManager
from actions.click_actions import ClickActions

def testar_mapeamento():
    emu = EmulatorManager(instance_id=0)
    click = ClickActions(emu, instance_id=0)
    
    # Busca coordenadas do JSON via ConfigManager
    ponto = emu.config.get_ui_point("botao_jogar")
    
    print(f"[*] Testando clique no Botão Jogar em: X={ponto['x']}, Y={ponto['y']}")
    click.tap(ponto['x'], ponto['y'])

if __name__ == "__main__":
    testar_mapeamento()