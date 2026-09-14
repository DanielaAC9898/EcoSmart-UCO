"""
Suscriptor MQTT — muestra en consola los datos del sistema EcoSmart UCO.
Correr en la PC o Raspberry Pi con Mosquitto activo.

Instalar dependencia: pip install paho-mqtt
Uso: python subscriber.py
"""

import paho.mqtt.client as mqtt
from datetime import datetime

BROKER = "localhost"   # Cambiar si Mosquitto corre en otra máquina
PORT   = 1883
TOPIC  = "ecosmart/puntos"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Conectado al broker {BROKER}:{PORT}")
        print(f"Suscrito al tópico: {TOPIC}\n")
        client.subscribe(TOPIC)
    else:
        print(f"Error de conexión, código: {rc}")


def on_message(client, userdata, msg):
    datos = msg.payload.decode()
    ahora = datetime.now().strftime("%H:%M:%S")

    print(f"[{ahora}] {msg.topic}")
    print(f"  Raw: {datos}")

    # Parsear y mostrar legible
    try:
        partes = datos.split(";")
        nodo = partes[0]
        valores = {k: v for k, v in (p.split(":") for p in partes[1:])}
        nivel  = float(valores.get("nivel", -1))
        dist   = float(valores.get("dist", -1))
        alerta = valores.get("alerta", "0") == "1"

        barra = "█" * int(nivel / 5) if nivel >= 0 else ""
        estado = "⚠  LLENO" if alerta else "✓  OK"

        print(f"  Nodo   : {nodo}")
        print(f"  Nivel  : {nivel:.1f}%  [{barra:<20}]")
        print(f"  Dist.  : {dist:.1f} cm")
        print(f"  Estado : {estado}")
    except Exception:
        pass
    print()


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Conectando a {BROKER}:{PORT}...")
client.connect(BROKER, PORT, keepalive=60)
client.loop_forever()
