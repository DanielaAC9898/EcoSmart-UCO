"""
TEST 01 — Sensor JSN-SR04T
Verifica el funcionamiento individual del sensor. Solo valida captura de data, no está conectado a LoRa o MQTT.
Archivo tipo main.py va en RP2040 y con sola en Thonny, "Esperando: lecturas de distancia en cm cada seg."
"""

from machine import Pin
from jsn_sr04t import JSNSR04T
import time

# ── Configurar estos pines según definición ──
TRIG_PIN = 2
ECHO_PIN = 3
ALTURA_CANECA_CM = 60
# ──────────────────────────────────────────

sensor = JSNSR04T(TRIG_PIN, ECHO_PIN)
print("Test sensor JSN-SR04T iniciado")
print(f"Altura de referencia (caneca vacía): {ALTURA_CANECA_CM} cm\n")

while True:
    distancia = sensor.distancia_cm()
    nivel     = sensor.nivel_llenado(ALTURA_CANECA_CM)

    if distancia is None:
        print("Sin lectura (fuera de rango o error)")
    else:
        barra = "█" * int(nivel / 5) if nivel else ""
        print(f"Distancia: {distancia:5.1f} cm  |  Llenado: {nivel:5.1f}%  {barra}")

    time.sleep(1)
