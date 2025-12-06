# 🦻 Detecção e Identificação de som ambiente para auxílio de pessoas surdas 

# 🍓 Sistema Embarcado – Raspberry Pi  

Este repositório contém todo o código responsável pela execução do sistema embarcado na Raspberry Pi.  

O dispositivo opera de forma autônoma, capturando áudio em tempo real, classificando sons relevantes e enviando notificações ao banco de dados.

O projeto foi desenvolvido para auxiliar pessoas com deficiência auditiva, permitindo que alertas importantes do ambiente doméstico sejam detectados e notificados automaticamente.

---

## 🔊 Funcionalidades da Raspberry

- 🎤 **Captura contínua de áudio** via microfone I2S MEMS  
- 🧠 **Classificação de sons usando YAMNet (TensorFlow Lite)**  
- 🗂️ Geração de espectrogramas Mel para inferência  
- 📡 **Envio de eventos ao Firebase Firestore**  
- 📶 **Configuração automática via Bluetooth Low Energy (BLE)**  
  - Recebe do app:
    - SSID (Wi-Fi)  
    - Senha do Wi-Fi    
- 🔄 Reconexão automática ao Wi-Fi configurado  
- ⚙️ Execução contínua como serviço systemd  
- ⚡ Baixa latência entre detecção → notificação

---

## 🖥️ Requisitos

- Raspberry Pi com conectividade à internet 
- Microfone I2S MEMS   
- Python 3.9+  
- Dependências:
  - `bluezero`
  - `sounddevice`
  - `numpy`
  - `scipy`
  - `tensorflow-lite`
  - `firebase-admin`
  - `libatlas-base-dev` (para otimização)
  - 
---

## 📦 Instalação

### 1. Clone o repositório
  ```sh
  git clone https://github.com//GuiJustica/TccCompletoRpi
  
  Crie um vevn
  
  sudo apt update
  sudo apt install python3-pip libatlas-base-dev -y
  pip3 install -r requirements.txt
  
  É necessário um arquivo .json para configuração da chave de serviço do Firebase
   - ServiceAccountKey.json```
  ```

## ▶️ Como Executar

- python ble/ble_server.py
    - Recebe do aplciativo o nome e senha do Wi-fi -

- python yammm.py
    - Carrega o modelo e inicia o fluxo de detecção e identificação -

👨‍💻 Desenvolvedor

 - Guilherme Marcato Mendes Justiça

Centro Universitário FEI – Ciência da Computação
2025
