import os
import subprocess
import traceback
import time
CONFIG_PATH = '/home/rpi/tcc/teste.wav/src/ble/config_test_real.txt'

def is_device_linked():
    return os.path.exists(CONFIG_PATH)

def enter_pairing_mode():
    """Inicia o BLE server para pareamento e conexão Wi-Fi"""
    print("Dispositivo não vinculado. Iniciando o modo de pareamento (BLE/Wi-Fi)...")
    ble_server_path = '/home/rpi/tcc/teste.wav/src/ble/ble_server.py'
    try:
        # Aqui ele roda e espera finalizar
        result = subprocess.run(["python3", ble_server_path], capture_output=True, text=True)
        print("BLE server finalizou com código:", result.returncode)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    except Exception as e:
        print("Erro ao rodar BLE server:", e)
        traceback.print_exc()

def mark_device_as_linked():
    with open(CONFIG_PATH, 'w') as f:
        f.write('dispositivo_vinculado=True')
    print("Dispositivo vinculado com sucesso!")

def main():
    print("Checando arquivo:", CONFIG_PATH)
    if is_device_linked():
        print("Dispositivo já vinculado. Arquivo detectado, não entra no BLE server.")
        return
    else:
        enter_pairing_mode()
        mark_device_as_linked()

if __name__ == "__main__":
    main()
