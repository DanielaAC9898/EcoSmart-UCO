"""
TEST 01 — Sensor JSN-SR04T
Objetivo: verificar que el sensor lee distancia correctamente, sin LoRa ni MQTT.

Cargar este archivo como main.py en el RP2040 y ver la consola en Thonny.
Esperado: lecturas de distancia en cm cada segundo.
"""

from jsn_sr04t import JSNSR04T
import time

# ── Pines UART ──────────────────────────────
UART_ID  = 1   # UART1 del RP2040
TX_PIN   = 5   # GP5 → RX del sensor
RX_PIN   = 4   # GP4 ← TX del sensor
ALTURA_CANECA_CM = 60
# ────────────────────────────────────────────

sensor = JSNSR04T(UART_ID, TX_PIN, RX_PIN)
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
