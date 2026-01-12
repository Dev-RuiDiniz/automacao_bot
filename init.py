from ppadb.client import Client as AdbClient
import cv2
import numpy as np

def connect_device():
    # O MEmu geralmente usa a porta 21503 para o primeiro dispositivo
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()

    if len(devices) == 0:
        print("❌ Nenhum dispositivo encontrado. Verifique se o ADB está rodando.")
        return None

    device = devices[0]
    print(f"✅ Conectado ao dispositivo: {device.serial}")
    return device

if __name__ == "__main__":
    device = connect_device()