import firebase_admin
from firebase_admin import credentials, db, messaging
import json
from datetime import datetime
import os

class FirebaseManager:
    def __init__(self, config_path="config.json", cred_path="cloud/firebase_key.json"):
        # Caminhos absolutos
        base_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(base_dir, config_path)
        cred_path = os.path.join(base_dir, cred_path)

        # Carrega config local (user_id, device_id, etc)
        with open(config_path, "r") as f:
            self.config = json.load(f)

        # Inicializa Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                "databaseURL": "-"
            })

    def send_sound_event(self, label: str, confidence: float):
        """Envia evento detectado para o Realtime Database + FCM"""
        user_id = self.config["user_id"]
        device_id = self.config["device_id"]

        data = {
            "sound": label,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }

        # 🔹 Grava no Realtime Database
        ref_path = f"users/{user_id}/devices/{device_id}/events"
        ref = db.reference(ref_path)
        ref.push(data)

        print(f"✅ Evento enviado para {ref_path}: {label} ({confidence:.2f})")

        # 🔹 Envia notificação push
        self._send_notification(user_id, label)

    def _send_notification(self, user_id: str, label: str):
        """Dispara notificação push via Firebase Cloud Messaging"""
        message = messaging.Message(
            notification=messaging.Notification(
                title="Som detectado!",
                body=f"O dispositivo identificou: {label}"
            ),
            topic=user_id  # o app assina esse tópico
        )

        try:
            response = messaging.send(message)
            print(f"📨 Notificação enviada com sucesso: {response}")
        except Exception as e:
            print(f"⚠️ Erro ao enviar notificação: {e}")
