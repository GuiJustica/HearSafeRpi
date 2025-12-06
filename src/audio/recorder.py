#recorder.py
import sounddevice as sd
import numpy as np


# Função para gravar áudio usando o microfone da Raspberry Pi
def record_audio(duration, sample_rate, device_index) -> np.ndarray:
    """Captura áudio do microfone por 'duration' segundos"""

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32',
        device=device_index   # força usar o microfone certo
    )
    sd.wait()
    audio = np.squeeze(audio)  # removes extra dimensions
    return audio
