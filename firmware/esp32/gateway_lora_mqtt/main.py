"""
Gateway ESP32 — Receptor LoRa → MQTT
Recibe mensajes del nodo RP2040 por LoRa y los publica en Mosquitto.
"""

import network
import time
from machine import Pin, SPI
from umqtt.simple import MQTTClient
from lora_lib import LoRa
import config


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    print("Conectando a WiFi", end="")
    for _ in range(20):
        if wlan.isconnected():
            break
        print(".", end="")
        time.sleep(1)
    if wlan.isconnected():
        print(f"\nWiFi OK — IP: {wlan.ifconfig()[0]}")
    else:
        print("\nError: no se pudo conectar al WiFi")
    return wlan.isconnected()


def conectar_mqtt():
    client = MQTTClient(config.MQTT_CLIENT_ID, config.MQTT_BROKER, port=config.MQTT_PORT)
    client.connect()
    print(f"MQTT conectado → {config.MQTT_BROKER}:{config.MQTT_PORT}")
    return client


def al_recibir(datos):
    """Callback: se ejecuta al llegar un paquete LoRa."""
    print(f"RX ← {datos}")
    try:
        mqtt.publish(config.MQTT_TOPIC, datos)
        print(f"    Publicado en {config.MQTT_TOPIC}")
    except Exception as e:
        print(f"    Error MQTT: {e}")


# ── Inicialización ──────────────────────────────────────
conectar_wifi()
mqtt = conectar_mqtt()

spi  = SPI(config.LORA_SPI_ID,
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

lora.receive()
print("Gateway listo. Esperando mensajes LoRa...")

# ── Bucle principal ─────────────────────────────────────
while True:
    # La recepción ocurre por interrupción (DIO0), este bucle solo mantiene vivo el cliente MQTT
    try:
        mqtt.ping()
    except Exception:
        print("MQTT desconectado, reconectando...")
        mqtt = conectar_mqtt()
    time.sleep(5)
