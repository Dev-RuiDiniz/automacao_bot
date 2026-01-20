import time
import os

class InstanceManager:
    """
    [Copiloto] Gerencia o ciclo de vida das instâncias do MEmu.
    Responsável por: Clonagem, Remoção, Reciclagem e Listagem de Status.
    """
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
        
        if res and "SUCCESS" in res:
            try:
                # Extrai o novo ID usando split
                new_id = res.split("instance")[-1].strip()
                self.log.info(f"[✅] Nova instância criada com ID: {new_id}")
                
                # Renomeia para facilitar a organização visual no MEmu Console
                timestamp = time.strftime("%d%m_%H%M")
                new_name = f"Bot_Conta_{timestamp}"
                self.emu._execute_memuc(['rename', '-i', new_id, new_name])
                
                return int(new_id)
            except Exception as e:
                self.log.error(f"[-] Erro ao processar ID da nova instância: {e}")
                return None
        else:
            self.log.error(f"[-] Falha ao clonar instância: {res}")
            return None

    def delete_instance(self, instance_id):
        """
        Remove instâncias do sistema (limpeza de disco).
        Geralmente usado para contas bloqueadas ou após maturação bem-sucedida.
        """
        self.log.warning(f"[*] Removendo instância {instance_id} do sistema...")
        # Certifica-se de que a instância está parada antes de remover
        self.emu._execute_memuc(['stop', '-i', str(instance_id)])
        time.sleep(1)
        return self.emu._execute_memuc(['remove', '-i', str(instance_id)])
    
    def recycle_instance(self, instance_id, base_id=0):
        """
        [♻️] Deleta a instância atual e cria uma nova 'limpa' a partir da base.
        Ideal para contornar bloqueios de IP/ID sem intervenção manual.
        """
        self.log.warning(f"[♻️] Reciclando instância {instance_id}...")
        
        # 1. Deleta a instância ruim
        self.delete_instance(instance_id)
        time.sleep(2) # Pequena pausa para o sistema de arquivos liberar o vmdk
        
        # 2. Cria uma nova a partir da base
        new_id = self.create_new_account_instance(base_id)
        return new_id

    def list_all_instances(self):
        """
        [NOVO] Consulta o MEmu e retorna uma lista formatada de todas as instâncias.
        Pode ser chamada pelo Menu Principal para diagnóstico.
        """
        raw_list = self.emu._execute_memuc(['list', '-l'])
        instances = []

        if raw_list:
            lines = raw_list.splitlines()
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 4:
                    status_code = parts[3]
                    # Tradução técnica do status code do MEmu
                    status_text = "Rodando" if status_code != "-1" else "Desligada"
                    if status_code == "0": status_text = "Iniciando..."
                    
                    instances.append({
                        "id": parts[0],
                        "name": parts[1],
                        "status": status_text
                    })
        return instances

    def get_instance_info(self, instance_id):
        """Retorna os detalhes de uma instância específica."""
        all_inst = self.list_all_instances()
        for inst in all_inst:
            if str(inst["id"]) == str(instance_id):
                return inst
        return None