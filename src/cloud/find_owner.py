# cloud/find_owner.py
import firebase_admin
from firebase_admin import credentials, db
import os
import json
from bluezero import adapter  # usa o mesmo adapter do BLE
import time

def init_firebase(cred_path, database_url):
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {"databaseURL": database_url})

def find_owner_for_device(local_device_id):
    """
    Percorre /usuarios/<uid>/dispositivos e busca um device com id == local_device_id
    Retorna (user_id, device_key) ou (None, None)
    """
    root = db.reference("usuarios")
    users = root.get() or {}
    for uid, udata in users.items():
        dispositivos = udata.get("dispositivos") or {}
        for key, dev in dispositivos.items():
            if dev.get("id") == local_device_id:
                return uid, key
    return None, None


def main():
    print("🔍 Buscando dono da Raspberry no Firebase...")

    BASE_DIR = os.path.dirname(__file__)
    CRED_PATH = os.path.join(BASE_DIR, "firebase_key.json")
    DATABASE_URL = "-"

    # inicializa o Firebase
    init_firebase(CRED_PATH, DATABASE_URL)

    # pega o endereço BLE da Raspberry
    bt_adapter = adapter.Adapter()
    local_id = bt_adapter.address  # ex: D8:3A:DD:E9:09:F1
    print("📡 ID local do dispositivo:", local_id)

    # tenta encontrar o dono
    uid, devkey = find_owner_for_device(local_id)

    if uid and devkey:
        config = {"user_id": uid, "device_id": devkey}
        with open(os.path.join(BASE_DIR, "config.json"), "w") as f:
            json.dump(config, f)
        print("✅ Dono encontrado e salvo em config.json:")
        print(json.dumps(config, indent=2))
    else:
        print("⚠️ Nenhum dono encontrado para este dispositivo.")
        print("Verifique se o app já salvou o 'id' (MAC/UUID) no Realtime DB.")

if __name__ == "__main__":
    main()
