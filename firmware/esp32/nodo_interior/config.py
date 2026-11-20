# ─────────────────────────────────────────
# Configuración del nodo interior (ESP32, sin LoRa)
# ─────────────────────────────────────────

# Identificador de este nodo (cambiar por ubicación real, ver hilo-conductor)
NODE_ID = "ECO-02"

# Sensor AJ-SR04M -- modo serial (jumper/resistencia soldada, protocolo
# igual al JSN-SR04T-2.0). Trama: 0xFF + H_DATA + L_DATA + SUM, mm.
UART_ID = 2     # UART2 del ESP32
TX_PIN  = 17    # ESP32 TX2 -> RX del sensor
RX_PIN  = 16    # ESP32 RX2 <- TX del sensor

# Umbrales del semáforo en CENTÍMETROS CRUDOS (decisión 2026-09-21/22).
# Heredados del nodo de prueba -- CONFIRMAR con la altura real del
# recipiente antes de instalar en el punto ecológico definitivo.
UMBRAL_LLENO_CM = 30.0
UMBRAL_MEDIO_CM = 60.0

# Límites físicos del sensor (datasheet JSN-SR04T-2.0: rango 20-600 cm)
ZONA_CIEGA_CM    = 20.0
DISTANCIA_MAX_CM = 600.0

# Pines de los LEDs del semáforo local
LED_VERDE_PIN    = 25
LED_AMARILLO_PIN = 26
LED_ROJO_PIN     = 27

# Intervalo de muestreo (segundos)
INTERVALO_S = 5

# WiFi -- misma red que usa el gateway LoRa mientras se prueba todo
# junto contra el mismo Mosquitto en un computador.
from secrets import WIFI_SSID, WIFI_PASSWORD  # ver secrets_ejemplo.py

# Broker MQTT (IP del computador con Mosquitto -- el mismo del gateway
# mientras dure esta fase de pruebas; en producción sería la Raspberry Pi)
MQTT_BROKER    = "192.168.1.100"
MQTT_PORT      = 1883
MQTT_CLIENT_ID = "esp32-interior-01"
# Mismo esquema que "ecosmart/rp2040" (visto en la rama feature_josepavas):
# un tópico por tipo de nodo, mientras se define el esquema definitivo
# ecosmart/puntos/{id_punto}/nivel del plan de implementación.
MQTT_TOPIC     = b"ecosmart/esp32"
