class ProxyManager:
    def __init__(self, emulator_manager, instance_id=0):
        self.emu = emulator_manager
        self.instance_id = instance_id
        self.log = emulator_manager.log

    def set_proxy(self, ip, port):
        """Configura o proxy HTTP no sistema Android via ADB."""
        self.log.info(f"Configurando Proxy na Instância {self.instance_id}: {ip}:{port}")
        
        # Comando para injetar o proxy nas configurações globais do Android
        cmd = f"settings put global http_proxy {ip}:{port}"
        return self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', cmd])

    def clear_proxy(self):
        """Remove as configurações de proxy da instância."""
        self.log.warning(f"Limpando configurações de proxy da Instância {self.instance_id}")
        return self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'settings', 'put', 'global', 'http_proxy', ':0'])

    def get_current_ip(self):
        """
        Verifica o IP externo que a instância está expondo.
        Usa o comando curl (nativo na maioria das versões recentes do Android).
        """
        # Tenta via curl para um serviço de verificação de IP
        res = self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'curl', '-s', 'https://ifconfig.me'])
        
        if not res or "not found" in res:
            # Fallback caso o curl não esteja instalado na ROM
            res = self.emu._execute_memuc(['adb', '-i', str(self.instance_id), 'shell', 'wget', '-qO-', 'https://ifconfig.me'])
            
        return res.strip() if res else "Erro ao obter IP"