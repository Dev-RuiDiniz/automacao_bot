def start_bot_process(instance_id):
    bot = AccountCreatorBot(instance_id)
    status = bot.run_initial_navigation()
    
    if status == "RECYCLE":
        print(f"[*] Instância {instance_id} foi descartada. Criando substituta...")
        # Lógica para chamar o InstanceManager e criar uma nova conta