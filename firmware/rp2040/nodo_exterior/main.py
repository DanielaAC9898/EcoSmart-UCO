"""
Nodo exterior — RP2040
Lee el nivel de llenado con JSN-SR04T y lo transmite por LoRa.

Formato del mensaje:
  ECO-01;nivel:45.2;dist:32.8;alerta:0
"""

from machine import Pin, SPI
from jsn_sr04t import JSNSR04T
from lora_lib import LoRa
import config
import time


def construir_mensaje(node_id, nivel, distancia):
    alerta = 1 if nivel is not None and nivel >= config.UMBRAL_LLENADO else 0
    nivel_str  = str(nivel)  if nivel     is not None else "ERR"
    dist_str   = str(distancia) if distancia is not None else "ERR"
    return f"{node_id};nivel:{nivel_str};dist:{dist_str};alerta:{alerta}"


# ── Inicialización ──────────────────────────────────────
sensor = JSNSR04T(config.TRIG_PIN, config.ECHO_PIN)

spi  = SPI(config.LORA_SPI_ID,
           baudrate=1_000_000,
           sck=Pin(config.LORA_SCK),
           mosi=Pin(config.LORA_MOSI),
           miso=Pin(config.LORA_MISO))

lora = LoRa(spi,
            cs=config.LORA_CS,
            reset=config.LORA_RESET,
            dio0=config.LORA_DIO0,
            frequency=config.LORA_FREQ)

print(f"[{config.NODE_ID}] Nodo iniciado. Enviando cada {config.INTERVALO_S}s")

# ── Bucle principal ─────────────────────────────────────
while True:
    distancia = sensor.distancia_cm()
    nivel     = sensor.nivel_llenado(config.ALTURA_CANECA_CM)
    mensaje   = construir_mensaje(config.NODE_ID, nivel, distancia)

    print(f"TX → {mensaje}")

    if lora.send_with_ack(mensaje):
        print("    ACK recibido")
    else:
        print("    Sin respuesta del gateway")

    time.sleep(config.INTERVALO_S)
