import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import csv
import matplotlib.pyplot as plt
import sounddevice as sd
from scipy import signal
from cloud.evento import push_event_to_db, load_config
from scipy.signal import butter, lfilter
from scipy.io.wavfile import write
from datetime import datetime
import os
from datetime import datetime
import time


RESULTS_FILE = "results/detection_results.csv"
if not os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "grupo", "score", "classe_principal", "probabilidade"])


# ---------- FILTROS ----------
def lowpass_filter(data, cutoff=8000, fs=16000, order=4):
    nyq = 0.5 * fs
    if cutoff >= nyq:
        cutoff = nyq - 1
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low')
    return lfilter(b, a, data)

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    if highcut >= nyq:
        highcut = nyq - 1
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def apply_bandpass_filter(data, lowcut=300, highcut=6000, fs=16000, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    return lfilter(b, a, data)

def normalize_audio(audio):
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak
    return audio


# Modifique a função class_names_from_csv para retornar também os índices
def class_names_from_csv(class_map_csv_text):
    """Retorna uma lista de nomes de classes e seus índices correspondentes."""
    class_names = []
    class_indices = []
    with tf.io.gfile.GFile(class_map_csv_text) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            class_names.append(row['display_name'])
            # NÃO subtrair 1: o CSV já usa índices 0-based
            class_indices.append(int(row['index']))
    return class_names, class_indices

# Função para garantir a taxa de amostragem desejada
def ensure_sample_rate(original_sample_rate, waveform, desired_sample_rate=16000):
    """Reamostra o áudio se necessário."""
    if original_sample_rate != desired_sample_rate:
        desired_length = int(round(float(len(waveform)) / original_sample_rate * desired_sample_rate))
        waveform = signal.resample(waveform, desired_length)
    return desired_sample_rate, waveform


DURATION = 2
SAMPLE_RATE = 48000
DEVICE_INDEX = 1  # Índice do dispositivo de áudio (microfone)


# Função para gravar áudio usando o microfone da Raspberry Pi
def record_audio(duration, sample_rate, device_index) -> np.ndarray:
    """Captura áudio do microfone por 'duration' segundos"""
    print(f"🎤 Gravando com o dispositivo: {sd.query_devices(device_index)['name']}")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32',
        device=DEVICE_INDEX   # força usar o microfone certo
    )
    sd.wait()
    audio = np.squeeze(audio)  # removes extra dimensions
    return audio



config = load_config()
USER_ID = config["user_id"]
DEVICE_ID = config["device_id"]

# Carrega o modelo YAMNet
print("Carregando o modelo YAMNet...")
model = hub.load('https://tfhub.dev/google/yamnet/1')

# Carrega as classes permitidas do CSV local
class_map_path = "detection/yamnet_class_map.csv"
allowed_class_names, allowed_class_indices = class_names_from_csv(class_map_path)

# Mapeamento do índice do modelo (0-based) -> nome da classe permitida
# Converta chaves para int explícito e crie um conjunto para checagem rápida
allowed_index_to_name = {int(idx): name for idx, name in zip(allowed_class_indices, allowed_class_names)}
allowed_index_set = set(allowed_index_to_name.keys())


while True:
    # Grava o áudio
    timestamp_envio = datetime.utcnow().isoformat()

    audio = record_audio(DURATION, SAMPLE_RATE, DEVICE_INDEX)
    print("Reamostrando o áudio para 16 kHz...")
    if np.max(np.abs(audio)) > 0:
        audio = normalize_audio(audio)

    # Aplica filtro bandpass
    audio = apply_bandpass_filter(audio, lowcut=300, highcut=6000, fs=SAMPLE_RATE, order=6)

    # Reamostra para 16 kHz
    sample_rate, audio = ensure_sample_rate(SAMPLE_RATE, audio)
    waveform = normalize_audio(audio).astype(np.float32).reshape(-1)

    # Executa o modelo
    print("Executando o modelo...")
    scores, embeddings, spectrogram = model(waveform)
    scores_np = scores.numpy()
    spectrogram_np = spectrogram.numpy()

    # Filtra classes permitidas
    mean_scores = np.mean(scores_np, axis=0)
    filtered_scores = np.zeros_like(mean_scores)
    filtered_scores[allowed_class_indices] = mean_scores[allowed_class_indices]

    # Top N
    top_n = min(5, len(allowed_class_indices))
    top_class_indices = np.argsort(filtered_scores)[::-1]
    top_class_indices = [int(idx) for idx in top_class_indices if filtered_scores[idx] > 0 and idx in allowed_index_set][:top_n]
    top_scores = [filtered_scores[idx] for idx in top_class_indices]
    sum_top_scores = sum(top_scores)
    top_scores_pct = [s / sum_top_scores for s in top_scores] if sum_top_scores > 0 else [0 for _ in top_scores]
    top_class_names = [allowed_index_to_name[idx] for idx in top_class_indices]

    # -------------------
    # DETECÇÃO POR GRUPO
    sound_groups = {
        "Sirene": ["siren", "police car", "ambulance", "fire alarm", "fire truck", "emergency vehicle", "alarm"],
        "Campainha": ["doorbell", "ding-dong", "jingle bell","beep, bleep","ding","bell","buzzer"],
        "Telefone": ["telephone", "ringtone", "telephone bell","buzzer"],
        "Animal": ["dog", "cat", "bark","domestic animals, pets"],
        "Eletrodoméstico": ["microwave", "vacuum", "hair dryer", "toothbrush", "electric toothbrush", "blender","beep, bleep"],
        "Choro": ["cry", "crying", "baby cry", "infant cry"]
    }

    detected_groups = {}
    THRESHOLD = 0.5
    for group_name, keywords in sound_groups.items():
            # pega índices do Top N que pertencem ao grupo
            indices_in_group = [
                i for i, name in enumerate(top_class_names)
                if any(keyword in name.lower() for keyword in keywords)
            ]

            if indices_in_group:
                # soma os percentuais das classes que pertencem ao grupo
                group_pct = sum(top_scores_pct[i] for i in indices_in_group)
                group_score = sum(filtered_scores[top_class_indices[i]] for i in indices_in_group)

                print(f"🔎 Verificando grupo '{group_name}': {group_pct*100:.2f}% ({len(indices_in_group)} classes relacionadas)")

                # envia apenas se a soma das porcentagens for alta o suficiente
                if group_pct >= THRESHOLD:
                    detected_groups[group_name] = group_score

    # -------------------
    # EXIBE CLASSES PRINCIPAIS
    print("\n🔝 Classes principais detectadas:")
    for i, idx in enumerate(top_class_indices):
        print(f"{i+1}. {top_class_names[i]} (score: {filtered_scores[idx]:.4f}, pct_top5: {top_scores_pct[i]*100:.2f}%)")

    # -------------------
    # SOM PRINCIPAL E GRUPOS
    if top_class_indices:
        infered_class = top_class_names[0]
        top_probability = top_scores_pct[0]
        safe_name = infered_class.replace(" ", "_").replace(",", "")

        print(f"\n🔊 Som principal detectado: {infered_class} (probabilidade Top5: {top_probability*100:.2f}%)")

        if detected_groups:
            print(f"\n🔔 Grupos de som detectados: ")
            for group, group_pct in detected_groups.items():
                print(f"- {group}: {group_pct*100:.2f}%")

                # Salva áudio
                #os.makedirs("detected_sounds", exist_ok=True)
                #timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                #safe_group_name = group.replace(" ", "_")
                #filename = f"detected_sounds/{timestamp}_{safe_group_name}.wav"
                #write(filename, int(sample_rate), (audio*32767).astype(np.int16))
                #print(f"💾 Áudio salvo: {filename}")

                # Envia para o banco de dados
                push_event_to_db(USER_ID, DEVICE_ID, group, group_pct, timestamp_envio)

                with open(RESULTS_FILE, mode="a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp_envio,
                        group,
                        group_pct,
                        infered_class,
                        top_probability
                ])
    else:
        print("\n❌ Nenhum som reconhecido das classes permitidas")
        safe_name = "nenhum_som"

    # -------------------
    # PLOTAGEM
    plt.figure(figsize=(10, 6))
    plt.subplot(3, 1, 1)
    plt.plot(waveform)
    plt.xlim([0, len(waveform)])
    plt.title("Forma de Wav")

    plt.subplot(3, 1, 2)
    plt.imshow(spectrogram_np.T, aspect='auto', interpolation='nearest', origin='lower')
    plt.title("Espectrograma Log-Mel")

    plt.subplot(3, 1, 3)
    if len(top_class_indices) > 0:
        plt.imshow(scores_np[:, top_class_indices].T, aspect='auto', interpolation='nearest', cmap='gray_r')
    else:
        plt.imshow(np.zeros((1, scores_np.shape[0])), aspect='auto', interpolation='nearest', cmap='gray_r')
    patch_padding = (0.025 / 2) / 0.01
    plt.xlim([-patch_padding - 0.5, scores_np.shape[0] + patch_padding - 0.5])
    n_display = len(top_class_indices)
    yticks = range(n_display)
    plt.yticks(yticks, top_class_names if n_display > 0 else ["(nenhuma)"])
    plt.ylim(-0.5 + np.array([n_display, 0]))
    plt.title("Pontuações das Classes Principais")

    plt.tight_layout()
    plt.savefig("graficos/yamnet_results_microphone.png")
    plt.close()
    print("Resultados salvos como 'yamnet_results_microphone.png'\n")
