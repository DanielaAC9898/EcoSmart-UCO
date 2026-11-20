"""
TEST 05 -- LoRa + Sensor + LEDs + JSON (Transmisor en RP2040)
Extiende tests/04_leds empaquetando la lectura como JSON en vez de
un texto plano, para que el receptor (y más adelante el broker MQTT)
puedan parsearlo como datos estructurados. Cargar junto con lora_lib.py.

Nota (2026-09-22): el JSON de este mensaje no incluye todavía un campo
de identificador de nodo (nodo_id / NODE_ID) -- a diferencia del nodo
ESP32 interior (firmware/esp32/nodo_interior/), que sí lo incluye.
Antes de integrar esto a firmware/rp2040/nodo_exterior/ conviene
agregarlo, para poder distinguir de qué punto ecológico viene cada
lectura una vez haya más de un nodo publicando.
"""
from machine import Pin, SPI, UART
from lora_lib import LoRa
import time
import json  # Módulo nativo para manejo de JSON en MicroPython

# 1. Configuración de LEDs
led_verde = Pin(2, Pin.OUT)
led_amarillo = Pin(3, Pin.OUT)
led_rojo = Pin(6, Pin.OUT)

# 2. Configuración SPI0 para módulo LoRa (SX1278)
spi = SPI(0, baudrate=1000000, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
lora = LoRa(spi, cs=17, reset=15, dio0=14)
lora.set_bandwidth(125000)

# 3. Configuración UART1 para AJ-SR04M (Modo 4 - 47k)
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

def read_raw_distance():
    if uart.any():
        uart.read()

    uart.write(b'\x01')
    time.sleep_ms(100)

    if uart.any():
        raw_bytes = uart.read()
        for i in range(len(raw_bytes) - 3):
            if raw_bytes[i] == 0xFF:
                high, low, checksum = raw_bytes[i+1], raw_bytes[i+2], raw_bytes[i+3]
                if (0xFF + high + low) & 0xFF == checksum:
                    return ((high << 8) + low) / 10.0
    return None

def process_trash_level():
    raw_dist = read_raw_distance()

    led_verde.value(0)
    led_amarillo.value(0)
    led_rojo.value(0)

    # Tratamiento de zona ciega o error
    if raw_dist is None or raw_dist < 20.0 or raw_dist > 500.0:
        led_rojo.value(1)
        return 0.0, "LLENO_UMBRAL"
    elif raw_dist <= 30.0:
        led_rojo.value(1)
        return raw_dist, "LLENO"
    elif 30.0 < raw_dist <= 60.0:
        led_amarillo.value(1)
        return raw_dist, "MEDIO"
    else:
        led_verde.value(1)
        return raw_dist, "DISPONIBLE"

print("--- TRANSMISOR PICO (JSON) + LORA INICIADO ---")
i = 0

while True:
    dist, estado = process_trash_level()

    # Creación del diccionario con los datos
    data = {
        "msg_id": i,
        "estado": estado,
        "distancia_cm": round(dist, 1)
    }

    # Convertir diccionario a cadena JSON
    mensaje = json.dumps(data)

    print("Enviando JSON:", mensaje)

    if lora.send_with_ack(mensaje):
        print("Confirmado por receptor")
    else:
        print("Sin respuesta de receptor LoRa")

    time.sleep(5)
    i += 1
