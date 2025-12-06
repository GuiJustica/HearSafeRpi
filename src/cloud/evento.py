# sound_event.py
import json
import os
from datetime import datetime,timezone
import numpy as np

# Firebase
import firebase_admin
from firebase_admin import credentials, db, messaging


# --- CONFIGURAÇÕES ---
BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
FIREBASE_KEY_PATH = os.path.join(BASE_DIR, "firebase_key.json")
DATABASE_URL = "-"  # coloque seu database_url aqui

# --- Inicialização do Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        "databaseURL": DATABASE_URL
    })

# --- Funções auxiliares ---
def load_config():
    """Lê user_id e device_id do config.json"""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def push_event_to_db(user_id, device_id, label, confidence,timestamp_envio):
    """Salva evento no Realtime Database"""
    ref_path = f"usuarios/{user_id}/eventos_sons/{device_id}"
    ref = db.reference(ref_path)

    event_data = {
        "label": label,
        "confidence": float(confidence),
        "timestamp": timestamp_envio
    }

    ref.push(event_data)
    print(f"💾 Evento enviado para DB: {event_data}")
    return event_data

def send_fcm_notification(user_fcm_token, label, confidence):
    """Envia notificação via FCM"""
    message = messaging.Message(
        data={
            "label": label,
            "confidence": str(confidence)
        },
        token=user_fcm_token
    )
    try:
        response = messaging.send(message)
        print(f"📲 Notificação enviada com sucesso: {response}")
    except Exception as e:
        print(f"❌ Falha ao enviar notificação: {e}")

# --- Função principal ---
def process_sound(log_mel_spec: np.ndarray, fcm_token: str = None, threshold: float = 0.6):
    """
    Recebe log_mel_spec do áudio detectado.
    Se passar threshold, envia para Firebase e opcionalmente FCM.
    """
    config = load_config()
    user_id = config["user_id"]
    device_id = config["device_id"]

    classifier = AudioClassifier()
    label, confidence, ok = classifier.classify(log_mel_spec, threshold)

    if ok:
        # Envia evento para DB
        event = push_event_to_db(user_id, device_id, label, confidence)

        # Envia notificação se token disponível
        if fcm_token:
            send_fcm_notification(fcm_token, label, confidence)

        return event
    else:
        print(f"🔕 Som detectado abaixo do threshold ({confidence:.2f})")
        return None

# --- Exemplo de uso ---
if __name__ == "__main__":
    # Simulando log_mel_spec (substituir pelo real do microfone)
    log_mel_spec = np.random.rand(96, 64).astype(np.float32)

    # Se você tiver o token do usuário:
    user_fcm_token = "<TOKEN_DO_USUARIO>"

    process_sound(log_mel_spec, fcm_token=user_fcm_token)
