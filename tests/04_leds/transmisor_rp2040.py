"""
TEST 04 -- LoRa + Sensor + Semáforo de LEDs (Transmisor en RP2040)
Extiende tests/03_lora_con_sensor agregando el semáforo visual local
(rojo/amarillo/verde) según la distancia leída. Cargar junto con lora_lib.py.
"""
from machine import Pin, SPI, UART
from lora_lib import LoRa
import time

# 1. Configuración de LEDs para estado del bote
led_verde = Pin(2, Pin.OUT)     # Bote con espacio
led_amarillo = Pin(3, Pin.OUT)  # Bote a nivel medio
led_rojo = Pin(6, Pin.OUT)      # Bote lleno / Umbral superado

# 2. Configuración SPI0 para módulo LoRa
spi = SPI(0, baudrate=1000000, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
lora = LoRa(spi, cs=17, reset=15, dio0=14)
lora.set_bandwidth(125000)

# 3. Configuración UART1 para AJ-SR04M (Modo 4 - 47k)
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# Parámetros mecánicos de tu bote (Ajusta según la altura real de tu caneca en cm)
ALTURA_BOTE_CM = 100.0  # Distancia de la tapa al fondo limpio

def read_raw_distance():
    """Solicita y lee la trama serial del AJ-SR04M (Modo 4)."""
    if uart.any():
        uart.read()

    uart.write(b'\x01')  # Disparo
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
    """
    Filtra la lectura y clasifica el nivel del bote gestionando
    los errores de la zona ciega (<20cm).
    """
    raw_dist = read_raw_distance()

    led_verde.value(0)
    led_amarillo.value(0)
    led_rojo.value(0)

    if raw_dist is None or raw_dist < 20.0 or raw_dist > 500.0:
        led_rojo.value(1)
        return 0.0, "LLENO (Umbral Superado)"
    elif raw_dist <= 30.0:
        led_rojo.value(1)
        return raw_dist, "LLENO"
    elif 30.0 < raw_dist <= 60.0:
        led_amarillo.value(1)
        return raw_dist, "MEDIO"
    else:
        led_verde.value(1)
        return raw_dist, "DISPONIBLE"

print("--- SISTEMA DE MONITOREO DE BASURA LORA INICIADO ---")
i = 0

while True:
    dist, estado = process_trash_level()

    mensaje = f"Estado: {estado} | Dist: {dist:.1f}cm | Msg #{i}"
    print("Enviando:", mensaje)

    if lora.send_with_ack(mensaje):
        print("Confirmado por receptor")
    else:
        print("Sin respuesta de receptor")

    time.sleep(5)
    i += 1
