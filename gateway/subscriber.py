"""
Suscriptor MQTT -- muestra en consola los datos del sistema EcoSmart UCO.
Correr en la PC o Raspberry Pi con Mosquitto activo.

Tópicos usados (decisión 2026-09-22): solo dos, planos, uno por nodo --
no hay jerarquía "ecosmart/puntos/...":
  ecosmart/rp2040  -- nodo exterior (llega por el gateway LoRa->MQTT)
  ecosmart/esp32   -- nodo interior (publica directo por Wi-Fi)
Nos suscribimos con el comodín de un nivel "ecosmart/+" para recibir
ambos con un solo suscriptor.

Instalar dependencia: pip install paho-mqtt
Uso: python subscriber.py
"""

import json

import paho.mqtt.client as mqtt
from datetime import datetime

BROKER = "localhost"       # Cambiar si Mosquitto corre en otra máquina
PORT = 1883
TOPIC_FILTER = "ecosmart/+"  # coincide con ecosmart/rp2040 y ecosmart/esp32


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Conectado al broker {BROKER}:{PORT}")
        print(f"Suscrito a: {TOPIC_FILTER}\n")
        client.subscribe(TOPIC_FILTER)
    else:
        print(f"Error de conexión, código: {rc}")


def _parsear_semicolon(datos):
    """Formato viejo: 'ECO-01;nivel:45.2;dist:32.8;alerta:0'"""
    partes = datos.split(";")
    nodo = partes[0]
    valores = {k: v for k, v in (p.split(":") for p in partes[1:])}
    return {
        "nodo_id": nodo,
        "nivel": valores.get("nivel"),
        "dist": valores.get("dist"),
        "alerta": valores.get("alerta") == "1",
    }


def _parsear_json(datos):
    """Formato nuevo (tests/05_leds_json y nodo_interior): JSON."""
    data = json.loads(datos)
    return {
        "nodo_id": data.get("nodo_id", "?"),
        "estado": data.get("estado"),
        "dist": data.get("distancia_cm"),
    }


def on_message(client, userdata, msg):
    datos = msg.payload.decode()
    ahora = datetime.now().strftime("%H:%M:%S")

    print(f"[{ahora}] {msg.topic}")
    print(f"  Raw: {datos}")

    parsed = None
    try:
        parsed = _parsear_json(datos)
    except (ValueError, TypeError):
        try:
            parsed = _parsear_semicolon(datos)
        except Exception:
            parsed = None

    if parsed is None:
        print("  (mensaje de prueba sin formato estructurado todavía)")
    else:
        print(f"  Nodo   : {parsed.get('nodo_id', '?')}")
        if "estado" in parsed:
            print(f"  Estado : {parsed['estado']}")
        if "nivel" in parsed and parsed["nivel"] is not None:
            print(f"  Nivel  : {parsed['nivel']}%")
        if parsed.get("dist") is not None:
            print(f"  Dist.  : {parsed['dist']} cm")
        if parsed.get("alerta"):
            print("  Alerta : ⚠ LLENO")
    print()


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Conectando a {BROKER}:{PORT}...")
client.connect(BROKER, PORT, keepalive=60)
client.loop_forever()
