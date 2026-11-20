"""
Nodo interior -- ESP32 (sin LoRa)
Lee el nivel de llenado con el AJ-SR04M, arma el JSON y lo publica por
Wi-Fi/MQTT directo al broker -- a diferencia del nodo exterior
RP2040+LoRa, que pasa por el gateway.

Reutiliza el driver compartido `jsn_sr04t.py` y la conexión WiFi
compartida `wifi.py` (ambos en firmware/common/) -- el primero también
usado por el nodo RP2040, el segundo también usado por el gateway ESP32.

IMPORTANTE al subir el firmware al ESP32: además de este main.py y el
config.py, copiar también a la raíz del dispositivo:
  firmware/common/jsn_sr04t.py
  firmware/common/wifi.py

Nota sobre el sensor: ver leer_distancia_cm() -- se manda un byte de
comando por si acaso, aunque el módulo (R27=47K, confirmado 2026-09-22)
ya transmite automáticamente sin necesitarlo.
"""

from machine import Pin
from jsn_sr04t import JSNSR04T
from wifi import conectar_wifi
from umqtt.simple import MQTTClient
import config
import time
import json

# ---------------------------------------------------------------
# 1. LEDs del semáforo local
# ---------------------------------------------------------------
led_verde = Pin(config.LED_VERDE_PIN, Pin.OUT)
led_amarillo = Pin(config.LED_AMARILLO_PIN, Pin.OUT)
led_rojo = Pin(config.LED_ROJO_PIN, Pin.OUT)

# ---------------------------------------------------------------
# 2. Sensor (driver compartido con el nodo RP2040)
# ---------------------------------------------------------------
sensor = JSNSR04T(config.UART_ID, config.TX_PIN, config.RX_PIN)


def leer_distancia_cm():
    
    sensor.uart.write(b'\x01')
    return sensor.distancia_cm()


def Semaforo():
    raw_dist = leer_distancia_cm()

    led_verde.value(0)
    led_amarillo.value(0)
    led_rojo.value(0)

    if raw_dist is None or raw_dist < config.ZONA_CIEGA_CM or raw_dist > config.DISTANCIA_MAX_CM:
        led_rojo.value(1)
        return 0.0, "LLENO_UMBRAL"
    elif raw_dist <= config.UMBRAL_LLENO_CM:
        led_rojo.value(1)
        return raw_dist, "LLENO"
    elif config.UMBRAL_LLENO_CM < raw_dist <= config.UMBRAL_MEDIO_CM:
        led_amarillo.value(1)
        return raw_dist, "MEDIO"
    else:
        led_verde.value(1)
        return raw_dist, "DISPONIBLE"


def conectar_mqtt():
    client = MQTTClient(config.MQTT_CLIENT_ID, config.MQTT_BROKER, port=config.MQTT_PORT, keepalive=60)
    client.connect()
    print(f"MQTT conectado -> {config.MQTT_BROKER}:{config.MQTT_PORT}")
    return client


# ---------------------------------------------------------------
# 3. Inicialización de red
# ---------------------------------------------------------------
conectar_wifi(config.WIFI_SSID, config.WIFI_PASSWORD)
mqtt = conectar_mqtt()

print(f"[{config.NODE_ID}] Nodo interior ESP32 iniciado (sin LoRa)")
i = 0
ultimo_ping = time.ticks_ms()

while True:
    dist, estado = Semaforo()

    data = {
        "msg_id": i,
        "estado": estado,
        "distancia_cm": round(dist, 1),
        "nodo_id": config.NODE_ID,
    }

    mensaje = json.dumps(data)
    print("Lectura:", mensaje)

    try:
        mqtt.publish(config.MQTT_TOPIC, mensaje)
        print(f"Publicado en {config.MQTT_TOPIC}")
    except OSError as e:
        print(f"Error MQTT al publicar: {e}, reconectando...")
        try:
            mqtt = conectar_mqtt()
            mqtt.publish(config.MQTT_TOPIC, mensaje)
        except Exception as e2:
            print(f"No se pudo reconectar/publicar: {e2}")

    if time.ticks_diff(time.ticks_ms(), ultimo_ping) > 30000:
        try:
            mqtt.ping()
        except Exception:
            pass
        ultimo_ping = time.ticks_ms()

    time.sleep(config.INTERVALO_S)
    i += 1
