"""import machine
import time
import ubinascii
from umqtt.simple import MQTTClient
from MQTT.ejemplo_wifi import conectar_wifi


# =========================================================
# 1. CONFIGURACION WIFI
# =========================================================

conectar_wifi("IoT", "EIJabcd1234")


# =========================================================
# 2. CONFIGURACION MQTT
# =========================================================

MQTT_BROKER = "192.168.0.101"
MQTT_PORT = 1883

CLIENT_ID = ubinascii.hexlify(machine.unique_id())

TOPIC_PUB = b"ecosmart/rp2040"


# =========================================================
# 3. CONECTAR AL BROKER
# =========================================================

client = MQTTClient(
    CLIENT_ID,
    MQTT_BROKER,
    port=MQTT_PORT,
    keepalive=60
)

client.connect()

print("Conectado al broker MQTT")


# =========================================================
# 4. PUBLICAR MENSAJE
# =========================================================

mensaje = b"Hola desde rp2040"

client.publish(
    TOPIC_PUB,
    mensaje
)

print("Mensaje publicado:")
print(mensaje.decode())

print("Topic:", TOPIC_PUB.decode())


# =========================================================
# 5. MANTENER CONEXION
# =========================================================

while True:

    client.ping()

    time.sleep(30)"""










"""
# main.py en el ESP32
# Receptor LoRa + MQTT

from machine import Pin, SPI
from lora_lib import LoRa
import machine
import time
import ubinascii
from umqtt.simple import MQTTClient
from MQTT.ejemplo_wifi import conectar_wifi


# =========================================================
# 1. WIFI
# =========================================================

conectar_wifi("IoT", "EIJabcd1234")


# =========================================================
# 2. MQTT
# =========================================================

MQTT_BROKER = "192.168.0.101"
MQTT_PORT = 1883

CLIENT_ID = ubinascii.hexlify(machine.unique_id())

TOPIC_PUB = b"ecosmart/rp2040"


client = MQTTClient(
    CLIENT_ID,
    MQTT_BROKER,
    port=MQTT_PORT,
    keepalive=60
)

client.connect()

print("Conectado al broker MQTT")


# =========================================================
# 3. LORA
# =========================================================

def al_recibir(dato):

    print("================================")
    print("Recibido por LoRa:", dato)

    mensaje = str(dato)

    client.publish(
        TOPIC_PUB,
        mensaje
    )

    print("Publicado por MQTT:", mensaje)
    print("================================")


# Pines estándar para HSPI en ESP32
spi = SPI(
    2,
    baudrate=1000000,
    sck=Pin(14),
    mosi=Pin(13),
    miso=Pin(12)
)

lora = LoRa(
    spi,
    cs=7,
    reset=6,
    dio0=5,
    callback=al_recibir
)

lora.set_bandwidth(125000)
lora.set_rx_mode()


# =========================================================
# 4. RECEPTOR
# =========================================================

print("--- RECEPTOR ESP32 ESCUCHANDO ---")
print("--- LORA -> MQTT ---")


while True:

    time.sleep(1)"""





# main.py
# ESP32 - Receptor LoRa + MQTT

from machine import Pin, SPI
from lora_lib import LoRa
import machine
import time
import ubinascii
from umqtt.simple import MQTTClient
from MQTT.ejemplo_wifi import conectar_wifi


# =========================================================
# 1. WIFI
# =========================================================

conectar_wifi("IoT", "EIJabcd1234")


# =========================================================
# 2. CONFIGURACION MQTT
# =========================================================

MQTT_BROKER = "192.168.0.101"
MQTT_PORT = 1883

CLIENT_ID = ubinascii.hexlify(machine.unique_id())

TOPIC_PUB = b"ecosmart/rp2040"


# Variable para almacenar el dato recibido por LoRa
dato_lora = None


# =========================================================
# 3. CONECTAR MQTT
# =========================================================

def conectar_mqtt():

    print("Conectando al broker MQTT...")

    client = MQTTClient(
        CLIENT_ID,
        MQTT_BROKER,
        port=MQTT_PORT,
        keepalive=60
    )

    client.connect()

    print("MQTT conectado")

    return client


client = conectar_mqtt()


# =========================================================
# 4. CALLBACK LORA
# =========================================================

def al_recibir(dato):

    global dato_lora

    print("Recibido por LoRa:", dato)

    # Solo guardamos el dato.
    # NO publicamos MQTT aqui porque este callback
    # se ejecuta dentro de una interrupcion.

    dato_lora = dato


# =========================================================
# 5. CONFIGURACION LORA
# =========================================================

spi = SPI(
    2,
    baudrate=1000000,
    sck=Pin(14),
    mosi=Pin(13),
    miso=Pin(12)
)

lora = LoRa(
    spi,
    cs=7,
    reset=6,
    dio0=5,
    callback=al_recibir
)

lora.set_bandwidth(125000)
lora.set_rx_mode()


print("--------------------------------")
print("RECEPTOR ESP32")
print("LoRa -> MQTT")
print("--------------------------------")


# =========================================================
# 6. BUCLE PRINCIPAL
# =========================================================

ultimo_ping = time.ticks_ms()

while True:

    # -----------------------------------------------------
    # Revisar si llego un dato por LoRa
    # -----------------------------------------------------

    if dato_lora is not None:

        dato = dato_lora

        # Limpiar la variable
        dato_lora = None

        print("Procesando dato LoRa...")

        try:

            # Convertir a texto
            mensaje = str(dato)

            # Publicar MQTT
            client.publish(
                TOPIC_PUB,
                mensaje
            )

            print("Publicado MQTT:")
            print("Topic:", TOPIC_PUB.decode())
            print("Mensaje:", mensaje)

        except OSError as e:

            print("Error MQTT:", e)

            # Intentar reconectar
            try:

                print("Intentando reconectar MQTT...")

                client = conectar_mqtt()

                # Intentar publicar nuevamente
                client.publish(
                    TOPIC_PUB,
                    mensaje
                )

                print("Mensaje publicado despues de reconectar")

            except Exception as e2:

                print("No fue posible reconectar MQTT:", e2)


    # -----------------------------------------------------
    # Mantener MQTT activo
    # -----------------------------------------------------

    if time.ticks_diff(
        time.ticks_ms(),
        ultimo_ping
    ) > 30000:

        try:

            client.ping()

            print("MQTT ping")

        except OSError as e:

            print("MQTT desconectado:", e)

            try:

                client = conectar_mqtt()

            except Exception as e2:

                print("Error reconectando MQTT:", e2)

        ultimo_ping = time.ticks_ms()


    time.sleep_ms(10)
