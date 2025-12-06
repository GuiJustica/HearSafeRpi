import pandas as pd
import matplotlib.pyplot as plt
import os
os.makedirs("graficos", exist_ok=True)
# Lê os dados salvos
df = pd.read_csv("detection_results.csv")

# Exibe estatísticas gerais
print("\nResumo das detecções:")
print(df.groupby("grupo")["score"].agg(["count", "mean", "max", "min"]).sort_values(by="count", ascending=False))

# ---------- GRÁFICO 1: Frequência de cada grupo ----------
plt.figure(figsize=(8,5))
df["grupo"].value_counts().plot(kind="bar")
plt.title("Quantidade de detecções por tipo de som")
plt.xlabel("Grupo de som")
plt.ylabel("Número de detecções")
plt.tight_layout()
plt.savefig("graficos/deteccoes_por_grupo.png")
plt.close()

# ---------- GRÁFICO 2: Confiabilidade média ----------
plt.figure(figsize=(8,5))
df.groupby("grupo")["score"].mean().sort_values().plot(kind="barh", color="skyblue")
plt.title("Confiabilidade média (score) por grupo")
plt.xlabel("Score médio")
plt.ylabel("Grupo")
plt.tight_layout()
plt.savefig("graficos/confiabilidade_media.png")
plt.close()

# ---------- GRÁFICO 3: Evolução temporal ----------
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

plt.figure(figsize=(10,5))
plt.plot(df["timestamp"], df["score"], marker='o', linestyle='-', alpha=0.6)
plt.title("Detecções ao longo do tempo")
plt.xlabel("Tempo")
plt.ylabel("Score")
plt.tight_layout()
plt.savefig("graficos/deteccoes_tempo.png")
plt.close()

print("\nGráficos salvos em 'graficos/'")
