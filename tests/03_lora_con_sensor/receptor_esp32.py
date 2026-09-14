"""
TEST 03 — LoRa + Sensor JSN-SR04T (Receptor en ESP32)
Solo muestra los datos en consola. Sin MQTT todavía.
Cargar en el ESP32 junto con lora_lib.py.
"""
from machine import Pin, SPI
from lora_lib import LoRa
import time

def al_recibir(datos):
    print(f"\n{'='*40}")
    print(f"Mensaje recibido: {datos}")
    # Parsear el mensaje para mostrarlo legible
    try:
        partes = datos.split(";")
        nodo = partes[0]
        valores = {k: v for k, v in (p.split(":") for p in partes[1:])}
        print(f"  Nodo   : {nodo}")
        print(f"  Nivel  : {valores.get('nivel', '?')} %")
        print(f"  Dist.  : {valores.get('dist', '?')} cm")
        alerta = valores.get('alerta', '0')
        print(f"  Alerta : {'⚠ LLENO' if alerta == '1' else 'OK'}")
    except Exception:
        pass
    print(f"{'='*40}")

spi  = SPI(1, baudrate=1_000_000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
lora = LoRa(spi, cs=27, reset=26, dio0=25, frequency=433e6, callback=al_recibir)
lora.receive()

print("Test 03 — Receptor ESP32 listo. Esperando datos del nodo...")
while True:
    time.sleep(1)
