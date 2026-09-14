"""
TEST 02 — LoRa Ping-Pong (Transmisor en RP2040)
Objetivo: verificar que el enlace LoRa funciona, sin sensor.
Cargar en el RP2040.
"""
from machine import Pin, SPI
from lora_lib import LoRa
import time

spi  = SPI(1, baudrate=1_000_000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
lora = LoRa(spi, cs=13, reset=28, dio0=27, frequency=433e6)

print("Transmisor LoRa RP2040 iniciado")
i = 0
while True:
    msg = f"PING {i}"
    print(f"Enviando: {msg}")
    if lora.send_with_ack(msg):
        print("  ACK recibido ✓")
    else:
        print("  Sin respuesta ✗")
    i += 1
    time.sleep(3)
