"""
TEST 03 -- LoRa + Sensor AJ-SR04M (Transmisor en RP2040)
Objetivo: integración completa antes de agregar LEDs y JSON (ver tests/04 y 05).
Cargar en el RP2040 junto con lora_lib.py.

Nota (2026-09-22): esta versión REEMPLAZA el borrador anterior de este
mismo test, que usaba la clase compartida JSNSR04T y pines de SPI1
(sck=10, mosi=11, miso=12, cs=13, reset=28, dio0=27) sin validar en
hardware real. Esta es la versión que Dani probó físicamente y confirmó
que funciona -- por eso el sensor se lee directo por UART (sin la clase
compartida) y los pines de SPI/LoRa cambiaron a SPI0
(sck=18, mosi=19, miso=16, cs=17, reset=15, dio0=14). Si vas a retomar
`firmware/rp2040/nodo_exterior/`, revisa que sus pines coincidan con
estos antes de darlo por bueno -- probablemente también tenga los pines
viejos sin validar.
"""
from machine import Pin, SPI, UART
from lora_lib import LoRa
import time

# 1. Configuración SPI0 para módulo LoRa (SX1278)
spi = SPI(0, baudrate=1000000, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
lora = LoRa(spi, cs=17, reset=15, dio0=14)
lora.set_bandwidth(125000)

# 2. Configuración UART1 para AJ-SR04M (GP4 = TX Pico, GP5 = RX Pico vía divisor 1k/2k)
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

def read_aj_sr04m_mode4():
    """
    Lee la distancia en Modo 4 (R19 = 47k):
    Requiere enviar el byte de disparo 0x01 por UART.
    """
    if uart.any():
        uart.read()

    uart.write(b'\x01')
    time.sleep_ms(100)

    if uart.any():
        raw_bytes = uart.read()
        for i in range(len(raw_bytes) - 3):
            if raw_bytes[i] == 0xFF:
                high = raw_bytes[i + 1]
                low = raw_bytes[i + 2]
                checksum = raw_bytes[i + 3]
                if (0xFF + high + low) & 0xFF == checksum:
                    distance_mm = (high << 8) + low
                    return distance_mm / 10.0
    return None

print("--- TEST 03 (AJ-SR04M 47K MODO 4) + LORA ---")
i = 0

while True:
    distancia = read_aj_sr04m_mode4()

    if distancia is not None:
        mensaje = f"Distancia: {distancia:.1f} cm | Msg #{i}"
    else:
        mensaje = f"Sin respuesta del sensor | Msg #{i}"

    print("Enviando:", mensaje)

    if lora.send_with_ack(mensaje):
        print("Confirmado por receptor")
    else:
        print("Sin respuesta de receptor LoRa")

    time.sleep(5)
    i += 1
