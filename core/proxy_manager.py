import re

class ProxyManager:
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log

    def set_proxy(self, ip, port):
        """Configura o proxy e força o Android a reconhecer a mudança."""
        self.log.info(f"Configurando Proxy na Instância {self.instance_id}: {ip}:{port}")
        
        # Comando 1: Define o Host
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'settings', 'put', 'global', 'http_proxy', f"{ip}:{port}"])
        # Comando 2: Define o Host global (redundância para versões diferentes de Android)
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'settings', 'put', 'global', 'global_http_proxy_host', ip])
        self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'settings', 'put', 'global', 'global_http_proxy_port', str(port)])
        
        return True

    def get_current_ip(self):
        """Obtém o IP e remove mensagens de conexão do ADB."""
        res = self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'curl', '-s', 'https://ifconfig.me'])
        
        if not res or "not found" in res:
            res = self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'wget', '-qO-', 'https://ifconfig.me'])
        
        if res:
            # Remove mensagens como "already connected to..." usando Regex
            # Pega apenas o formato de IP (ex: 187.2.212.120)
            ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', res)
            if ip_match:
                return ip_match.group(0)
                
        return "Erro ao obter IP"