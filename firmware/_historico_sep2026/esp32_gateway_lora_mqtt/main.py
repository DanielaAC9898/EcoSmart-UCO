"""
Gateway ESP32 -- Receptor LoRa -> MQTT
Recibe mensajes del nodo RP2040 por LoRa y los publica en Mosquitto.

Nota (2026-09-22): el callback de LoRa NO publica por MQTT directamente.
Solo guarda el dato en una variable global; la publicación ocurre en el
bucle principal. Publicar (I/O de red, puede bloquear) dentro de una
interrupción es riesgoso en MicroPython -- puede colgar el dispositivo.
Este patrón de "guardar y publicar afuera" viene de revisar la rama
`feature_josepavas` (gateway.py de José) -- se consolidó aquí en vez de
fusionar ese archivo tal cual, para no duplicar el gateway ni dejar
credenciales sueltas en el código (todo queda en config.py).

Al subir a la ESP32, copiar junto con este main.py y config.py:
  firmware/common/lora_lib.py
  firmware/common/wifi.py
"""

import time
from machine import Pin, SPI
from umqtt.simple import MQTTClient
from lora_lib import LoRa
from wifi import conectar_wifi
import config


def conectar_mqtt():
    client = MQTTClient(config.MQTT_CLIENT_ID, config.MQTT_BROKER, port=config.MQTT_PORT, keepalive=60)
    client.connect()
    print(f"MQTT conectado -> {config.MQTT_BROKER}:{config.MQTT_PORT}")
    return client


# Variable puente entre el callback de LoRa (interrupción) y el bucle
# principal, que es donde de verdad se publica por MQTT.
dato_lora = None


def al_recibir(datos):
    """Callback de LoRa (se ejecuta en interrupción, DIO0). Solo guarda el dato."""
    global dato_lora
    print(f"RX <- {datos}")
    dato_lora = datos


# -- Inicialización --------------------------------------
conectar_wifi(config.WIFI_SSID, config.WIFI_PASSWORD)
mqtt = conectar_mqtt()

spi = SPI(config.LORA_SPI_ID,
          baudrate=1_000_000,
          sck=Pin(config.LORA_SCK),
          mosi=Pin(config.LORA_MOSI),
          miso=Pin(config.LORA_MISO))

lora = LoRa(spi,
            cs=config.LORA_CS,
            reset=config.LORA_RESET,
            dio0=config.LORA_DIO0,
            frequency=config.LORA_FREQ,
            callback=al_recibir)

lora.set_rx_mode()
print("Gateway listo. Esperando mensajes LoRa...")

# -- Bucle principal ---------------------------------------
ultimo_ping = time.ticks_ms()

while True:
    # 1. Si llegó un dato por LoRa, publicarlo (aquí sí es seguro hacer I/O)
    if dato_lora is not None:
        datos = dato_lora
        dato_lora = None
        try:
            mqtt.publish(config.MQTT_TOPIC, datos)
            print(f"    Publicado en {config.MQTT_TOPIC}")
        except OSError as e:
            print(f"    Error MQTT al publicar: {e}, reconectando...")
            try:
                mqtt = conectar_mqtt()
                mqtt.publish(config.MQTT_TOPIC, datos)
                print("    Publicado tras reconectar")
            except Exception as e2:
                print(f"    No se pudo reconectar/publicar: {e2}")

    # 2. Mantener viva la conexión MQTT
    if time.ticks_diff(time.ticks_ms(), ultimo_ping) > 30000:
        try:
            mqtt.ping()
        except Exception:
            print("MQTT desconectado, reconectando...")
            try:
                mqtt = conectar_mqtt()
            except Exception as e:
                print(f"Error reconectando MQTT: {e}")
        ultimo_ping = time.ticks_ms()

    time.sleep_ms(10)
