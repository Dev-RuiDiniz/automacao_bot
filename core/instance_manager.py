import time

class InstanceManager:
    def __init__(self, emulator_manager):
        self.emu = emulator_manager
        self.log = emulator_manager.log

    def create_new_account_instance(self, base_id=0):
        """
        Clona a instância base e retorna o ID da nova instância criada.
        """
        self.log.info(f"[*] Iniciando clonagem da Instância Base (ID: {base_id})...")
        
        # O comando 'clone' do memuc retorna o índice da nova instância no console
        # Exemplo de saída: "SUCCESS: clone instance 1"
        res = self.emu._execute_memuc(['clone', '-i', str(base_id)])
        
        if "SUCCESS" in res:
            # Extrai o novo ID usando split
            new_id = res.split("instance")[-1].strip()
            self.log.info(f"[+] Nova instância criada com ID: {new_id}")
            
            # Renomeia para facilitar a organização
            timestamp = time.strftime("%d%m_%H%M")
            self.emu._execute_memuc(['rename', '-i', new_id, f"Bot_Conta_{timestamp}"])
            
            return int(new_id)
        else:
            self.log.error(f"[-] Falha ao clonar instância: {res}")
            return None

    def delete_instance(self, instance_id):
        """Remove instâncias que foram bloqueadas (limpeza de disco)."""
        self.log.warning(f"[*] Removendo instância {instance_id} do sistema...")
        return self.emu._execute_memuc(['remove', '-i', str(instance_id)])