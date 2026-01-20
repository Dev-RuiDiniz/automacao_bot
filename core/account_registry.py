import json
import os
from datetime import datetime

class AccountRegistry:
    """
    [Copiloto] Gerencia o registro de contas prontas para uso/venda em formato JSON.
    Centraliza o status de maturação e metadados das contas criadas.
    """
    def __init__(self, file_path="database/accounts.json"):
        self.file_path = file_path
        # [BOA PRÁTICA] Garante a existência da estrutura de pastas e arquivo
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)

    def register_account(self, nickname, instance_id, status="Pronta"):
        """Adiciona uma conta recém-criada ao registro inicial."""
        data = {
            "nickname": nickname,
            "instance_origin": instance_id,
            "status": status,
            "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "maturada": False # Inicia como False até completar o ciclo de slot
        }

        try:
            with open(self.file_path, 'r+') as f:
                accounts = json.load(f)
                accounts.append(data)
                f.seek(0)
                json.dump(accounts, f, indent=4)
                f.truncate() # Garante que o arquivo seja limpo após o novo dump
            return True
        except Exception as e:
            print(f"[-] Erro ao registrar conta: {e}")
            return False

    def update_status(self, instance_id, new_status):
        """
        [NOVO] Localiza a conta pela instância de origem e atualiza seu status.
        Essencial para o Step 6: Finalização Limpa.
        """
        updated = False
        try:
            with open(self.file_path, 'r+') as f:
                accounts = json.load(f)
                
                for account in accounts:
                    # Busca pela instância que está rodando o processo
                    if account.get("instance_origin") == instance_id:
                        account["status"] = new_status
                        # Se o status for MATURADA_COMPLETA, marca a flag definitiva
                        if new_status == "MATURADA_COMPLETA":
                            account["maturada"] = True
                            account["data_maturacao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        updated = True
                        break
                
                if updated:
                    f.seek(0)
                    json.dump(accounts, f, indent=4)
                    f.truncate()
                    return True
                
            print(f"[!] Conta na instância {instance_id} não encontrada para atualização.")
            return False
        except Exception as e:
            print(f"[-] Erro ao atualizar status no JSON: {e}")
            return False

    def get_account_status(self, instance_id):
        """Retorna o status atual de uma conta vinculada a uma instância."""
        try:
            with open(self.file_path, 'r') as f:
                accounts = json.load(f)
                for acc in accounts:
                    if acc.get("instance_origin") == instance_id:
                        return acc.get("status")
        except:
            pass
        return None