import csv
import tensorflow as tf
from scipy import signal


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
