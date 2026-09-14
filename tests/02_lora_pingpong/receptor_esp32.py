"""
TEST 02 — LoRa Ping-Pong (Receptor en ESP32)
Objetivo: verificar que el enlace LoRa funciona, sin sensor.
Cargar en el ESP32.
"""
from machine import Pin, SPI
from lora_lib import LoRa
import time

def al_recibir(datos):
    print(f"Recibido: {datos}")

spi  = SPI(1, baudrate=1_000_000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
lora = LoRa(spi, cs=27, reset=26, dio0=25, frequency=433e6, callback=al_recibir)
lora.receive()

print("Receptor LoRa ESP32 listo...")
while True:
    time.sleep(1)
