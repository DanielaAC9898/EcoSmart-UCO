# ─────────────────────────────────────────────────────
# Configuración del gateway ESP32 (receptor LoRa + MQTT)
# ─────────────────────────────────────────────────────

# WiFi
WIFI_SSID     = "nombre_red"
WIFI_PASSWORD = "contraseña"

# Broker MQTT (IP de la Raspberry Pi o PC con Mosquitto)
MQTT_BROKER   = "192.168.1.100"   # Cambiar a IP real del broker
MQTT_PORT     = 1883
MQTT_CLIENT_ID = "esp32-gateway-01"
MQTT_TOPIC    = b"ecosmart/puntos"

# Módulo LoRa SX1278 — pines HSPI del ESP32
LORA_SPI_ID  = 1
LORA_SCK     = 14
LORA_MOSI    = 13
LORA_MISO    = 12
LORA_CS      = 27
LORA_RESET   = 26
LORA_DIO0    = 25
LORA_FREQ    = 433e6   # Debe coincidir con el transmisor
