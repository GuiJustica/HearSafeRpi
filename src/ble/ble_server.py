# ble_server.py
from bluezero import peripheral, adapter
import json
import threading
import subprocess
import traceback
import os
import sys
import time

import firebase_admin
from firebase_admin import credentials, db as admin_db

# --- CONFIGURAÇÃO ---
SERVICE_UUID = "-"
CHAR_UUID    = "-"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "wifi.json")  # salva no diretório do usuário
FIREBASE_KEY_PATH = os.path.join(os.path.dirname(__file__), "../cloud/firebase_key.json")
DATABASE_URL = "-"

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})

# --- helpers ---
def log(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

def try_connect_wifi(ssid, password):
    try:
        log(f"📡 Tentando conectar à rede '{ssid}' via nmcli (sudo)...")

        cmd = ["sudo", "nmcli", "dev", "wifi", "connect", ssid, "password", password]
        proc = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        log(f"🔍 Código de retorno: {proc.returncode}")
        log(f"📜 STDOUT:\n{stdout}")
        log(f"⚠️ STDERR:\n{stderr}")

        if proc.returncode == 0:
            log("✅ Conexão Wi-Fi bem-sucedida!")
            with open("/home/rpi/tcc/teste.wav/src/dispositivo_conectado.flag", "w") as f:
                f.write("ok")
            return True, stdout
        else:
            log("⚠️ nmcli retornou erro, mas pode ter conectado mesmo assim.")
            if "successfully activated" in stdout.lower():
                log("⚠️ Detectada mensagem de sucesso no STDOUT — tratando como sucesso.")
                return True, stdout
            return False, stderr

    except subprocess.TimeoutExpired:
        log("⚠️ nmcli timeout expirado")
        return False, "timeout"
    except Exception as e:
        log("⚠️ Erro inesperado ao executar nmcli:", e)
        return False, str(e)

# --- callback de escrita ---
def write_callback(value, options):
    try:
        # value pode ser bytearray, bytes ou lista de ints
        if isinstance(value, (list, tuple)):
            b = bytes(value)
        elif isinstance(value, (bytes, bytearray)):
            b = bytes(value)   # converte bytearray para bytes
        else:
            b = str(value).encode()

        data_str = b.decode('utf-8').strip()  # decodifica corretamente
        log("📥 Dados recebidos:", data_str)

        data = json.loads(data_str)           # agora deve funcionar
        ssid = data.get("wifi")
        password = data.get("senha")

        if not ssid or not password:
            log("❌ Falta 'wifi' ou 'senha' no JSON.")
            return

        # grava no arquivo
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump({"wifi": ssid, "senha": password}, f)
        log(f"💾 Credenciais salvas em {OUTPUT_PATH}")

        try_connect_wifi(ssid, password)
        push_device_confirmation("dummy_user_id", "-", "HearSafePi", ssid)


    except Exception:
        log("❌ Erro no write_callback:")
        traceback.print_exc()

def push_device_confirmation(user_id, device_mac, device_name, wifi):
    try:
        ref_path = f'usuarios/{user_id}/dispositivos'
        ref = admin_db.reference(ref_path)
        device_obj = {
            'nome': device_name or 'HearSafePi',
            'id': device_mac or 'unknown_mac',
            'wifi': wifi,
            'criado_em': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
        ref.push(device_obj)
        log(f'✅ Confirmação enviada ao DB: {ref_path} -> {device_obj}')
    except Exception as e:
        log('❌ Erro ao enviar confirmação ao DB:', e)
# --- Main ---
def main():
    log("Iniciando BLE server (Bluezero)...")

    # adaptador
    bt_adapter = adapter.Adapter()
    log("Adaptador BLE detectado:", bt_adapter.address)

    # periférico
    pi_ble = peripheral.Peripheral(adapter_address=bt_adapter.address, local_name="HearSafePi")

    # serviço
    srv_id = 0
    pi_ble.add_service(srv_id, SERVICE_UUID, True)
    log(f"Serviço criado srv_id={srv_id} uuid={SERVICE_UUID}")

    # característica
    chr_id = 0
    pi_ble.add_characteristic(srv_id, chr_id, CHAR_UUID, [], False, ['write','write-without-response'],['encrypt-write'], write_callback)
    log(f"Característica criada chr_id={chr_id} uuid={CHAR_UUID}")

    # publica
    log("🔵 Publicando BLE...")
    pi_ble.publish()
    log("📡 Servidor BLE publicado. Aguardando conexão e escrita...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("⏹ Interrompido pelo usuário. Parando BLE...")
        pi_ble.stop()
        log("Finalizado.")

if __name__ == "__main__":
    main()
