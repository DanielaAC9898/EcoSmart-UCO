"""
TEST 05 -- LoRa + Sensor + LEDs + JSON (Receptor en ESP32)
El transmisor ahora manda el mensaje como JSON (ver transmisor_rp2040.py).
Se parsea con ujson para mostrarlo legible; si el parseo falla (por
ejemplo, un paquete corrupto o de una prueba anterior sin JSON), se
muestra el texto crudo tal cual llegó -- no se descarta el paquete.
Cargar en el ESP32 junto con lora_lib.py.
"""
from machine import Pin, SPI
from lora_lib import LoRa
import ujson
import time


def al_recibir(datos):
    print(f"\n{'='*40}")
    print(f"Mensaje recibido (crudo): {datos}")
    try:
        data = ujson.loads(datos)
        print(f"  msg_id       : {data.get('msg_id')}")
        print(f"  estado       : {data.get('estado')}")
        print(f"  distancia_cm : {data.get('distancia_cm')}")
    except (ValueError, TypeError):
        print("  (no se pudo parsear como JSON)")
    print(f"{'='*40}")


spi  = SPI(1, baudrate=1_000_000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
lora = LoRa(spi, cs=27, reset=26, dio0=25, frequency=433e6, callback=al_recibir)
lora.set_rx_mode()

print("Test 05 -- Receptor ESP32 listo. Esperando datos JSON del nodo...")
while True:
    time.sleep(1)
