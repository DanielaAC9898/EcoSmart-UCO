"""
TEST 03 — LoRa + Sensor JSN-SR04T (Transmisor en RP2040)
Objetivo: integración completa antes de agregar MQTT.
Cargar en el RP2040 junto con jsn_sr04t.py y lora_lib.py.
"""
from machine import Pin, SPI
from jsn_sr04t import JSNSR04T
from lora_lib import LoRa
import time

TRIG_PIN = 2         # Ajustar
ECHO_PIN = 3         # Ajustar
ALTURA_CANECA_CM = 60
NODE_ID = "ECO-01"

sensor = JSNSR04T(TRIG_PIN, ECHO_PIN)
spi    = SPI(1, baudrate=1_000_000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
lora   = LoRa(spi, cs=13, reset=28, dio0=27, frequency=433e6)

print("Test 03 iniciado — LoRa + Sensor")
while True:
    distancia = sensor.distancia_cm()
    nivel     = sensor.nivel_llenado(ALTURA_CANECA_CM)
    alerta    = 1 if nivel and nivel >= 80 else 0

    nivel_str = str(nivel) if nivel is not None else "ERR"
    dist_str  = str(distancia) if distancia is not None else "ERR"
    msg = f"{NODE_ID};nivel:{nivel_str};dist:{dist_str};alerta:{alerta}"

    print(f"TX → {msg}")
    if lora.send_with_ack(msg):
        print("   ACK ✓")
    else:
        print("   Sin respuesta ✗")
    time.sleep(5)
