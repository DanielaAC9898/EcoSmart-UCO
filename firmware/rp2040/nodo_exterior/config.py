# ─────────────────────────────────────────
# Configuración del nodo exterior (RP2040)
# ─────────────────────────────────────────

# Identificador de este nodo (cambiar por ubicación real)
NODE_ID = "ECO-01"

# Sensor JSN-SR04T — Modo 2 UART (R27 = 47K)
UART_ID  = 1   # Bus UART1 del RP2040
TX_PIN   = 5   # GP5 → RX del sensor
RX_PIN   = 4   # GP4 ← TX del sensor
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
