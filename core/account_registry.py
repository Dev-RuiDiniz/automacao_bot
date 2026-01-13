import json
import os
from datetime import datetime

class AccountRegistry:
    """Gerencia o registro de contas prontas para uso/venda em formato JSON."""
    def __init__(self, file_path="database/accounts.json"):
        self.file_path = file_path
        # Cria a pasta e o arquivo se não existirem
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)

    def register_account(self, nickname, instance_id, status="Pronta"):
        """Adiciona uma conta finalizada ao registro."""
        data = {
            "nickname": nickname,
            "instance_origin": instance_id,
            "status": status,
            "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "maturada": True
        }

        with open(self.file_path, 'r+') as f:
            accounts = json.load(f)
            accounts.append(data)
            f.seek(0)
            json.dump(accounts, f, indent=4)
        
        return True