import asyncio
from bleak import BleakGATTCharacteristic
from bleak.backends.bluezdbus.advertisement import Advertisement
from bleak.backends.bluezdbus.service import Service, Characteristic, Descriptor
from bleak.backends.bluezdbus import BleakGATTServiceProvider


# UUIDs (define um serviço e característica únicos)
SERVICE_UUID = "-"
CHAR_UUID_WIFI_INFO = "-"


class WifiCharacteristic(Characteristic):
    def __init__(self, service):
        super().__init__(CHAR_UUID_WIFI_INFO, ["write"], service)
        self.value = None

    async def WriteValue(self, value, options):
        # Recebe bytes enviados pelo app (SSID e senha)
        self.value = bytes(value).decode("utf-8")
        print(f"📶 Dados recebidos via BLE: {self.value}")
        # Exemplo de formato esperado: "SSID:MinhaRede;PWD:minhasenha"
        ssid, senha = self._parse_wifi_data(self.value)
        print(f"➡️ SSID = {ssid}\n➡️ Senha = {senha}")

    def _parse_wifi_data(self, data):
        try:
            ssid = data.split("SSID:")[1].split(";")[0]
            senha = data.split("PWD:")[1]
            return ssid, senha
        except Exception:
            return None, None


async def main():
    print("🔵 Inicializando BLE Server...")

    # Cria provedor de serviço BLE
    service_provider = await BleakGATTServiceProvider.create(SERVICE_UUID)

    # Cria o serviço e característica
    service = Service(SERVICE_UUID, True)
    wifi_char = WifiCharacteristic(service)

    service.add_characteristic(wifi_char)
    service_provider.add_service(service)

    # Inicia o serviço BLE
    await service_provider.start_advertising(
        name="HearSafePi",
        appearance=0,
        manufacturer_data={0xFFFF: b"RPI-BLE"},
    )

    print("🚀 Raspberry Pi anunciando como 'HearSafePi'")
    print("📱 Agora o app Flutter deve encontrar esse nome e conectar...")

    try:
        await asyncio.Event().wait()  # Mantém o servidor rodando
    except KeyboardInterrupt:
        print("\n🛑 Encerrando servidor BLE...")
        await service_provider.stop_advertising()


if __name__ == "__main__":
    asyncio.run(main())
