import json
import yaml
import os

class ConfigManager:
    def __init__(self):
        self.config_path = "config"
        self.settings = self.load_yaml("settings.yaml")
        self.proxies = self.load_json("proxies.json")
        self.accounts = self.load_json("accounts.json")
        self.timings = self.load_json("timings.json")

    def load_json(self, file_name):
        path = os.path.join(self.config_path, file_name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def load_yaml(self, file_name):
        path = os.path.join(self.config_path, file_name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def get_proxy_for_instance(self, instance_id):
        """Retorna o proxy configurado para uma instância específica [cite: 10, 134]"""
        return self.proxies.get(str(instance_id))

    def get_timing(self, key, default=1.5):
        """Retorna tempos de espera configurados [cite: 49, 132]"""
        return self.timings.get(key, default)