# ─────────────────────────────────────────
# Configuración del nodo exterior (RP2040)
# ─────────────────────────────────────────

# Identificador de este nodo (cambiar por ubicación real)
NODE_ID = "ECO-01"

# Sensor JSN-SR04T
TRIG_PIN = 2   # Ajustar según cableado real
ECHO_PIN = 3   # Ajustar según cableado real
ALTURA_CANECA_CM = 60   # Altura interior de la caneca en cm

# Umbral de alerta (%)
UMBRAL_LLENADO = 80

# Módulo LoRa SX1278 — pines SPI1 del RP2040
LORA_SPI_ID  = 1
LORA_SCK     = 10
LORA_MOSI    = 11
LORA_MISO    = 12
LORA_CS      = 13
LORA_RESET   = 28
LORA_DIO0    = 27
LORA_FREQ    = 433e6   # 433 MHz

# Intervalo de muestreo (segundos)
INTERVALO_S = 10
