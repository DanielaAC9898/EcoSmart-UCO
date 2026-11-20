from machine import Pin, SPI
from lora_lib import LoRa
import machine
import time
import ubinascii
from umqtt.simple import MQTTClient
from MQTT.ejemplo_wifi import conectar_wifi

# Importar librería de cifrado (MicroPython)
try:
    import cryptolib
except ImportError:
    import ucryptolib as cryptolib

key = b"1234567890123456"

# =========================================================
# 1. WIFI
# =========================================================

# =========================================================
# 2. CONFIGURACION MQTT
# =========================================================

MQTT_BROKER = "192.168.101.13"
MQTT_PORT = 1883

CLIENT_ID = ubinascii.hexlify(machine.unique_id())

TOPIC_PUB = b"iot"


# Variable para almacenar el dato recibido por LoRa
dato_lora = None


# Función para eliminar el relleno PKCS7
def unpad(data_bytes):
    pad_len = data_bytes[-1]
    return data_bytes[:-pad_len]


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

    print("Recibido por LoRa (Cifrado Base64):", dato)

    # Solo guardamos el dato para procesarlo fuera de la interrupción
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
print("LoRa (Descifra) -> MQTT (Texto Plano)")
print("--------------------------------")


# =========================================================
# 6. BUCLE PRINCIPAL
# =========================================================

ultimo_ping = time.ticks_ms()

while True:

    # -----------------------------------------------------
    # Revisar si llegó un dato por LoRa
    # -----------------------------------------------------

    if dato_lora:

        dato = dato_lora
        dato_lora = None

        print("Procesando y descifrando dato LoRa...")

        # CORRECCIÓN H1 (v1.1): descifrar y publicar se separan en dos
        # bloques try. Antes, "except Exception" atrapaba también el
        # OSError de MQTT (OSError es subclase de Exception), por lo que
        # la reconexión nunca se ejecutaba y el fallo de red se reportaba
        # como error de descifrado.

        mensaje = None

        # ---------------------------------------------
        # PASO A: Descifrar (solo errores de descifrado)
        # ---------------------------------------------
        try:
            # 1. Convertir Base64 a bytes cifrados
            bytes_cifrados = ubinascii.a2b_base64(dato)

            # 2. Descifrar con AES en modo ECB (modo 1)
            cipher = cryptolib.aes(key, 1)
            mensaje_padded = cipher.decrypt(bytes_cifrados)

            # 3. Quitar el relleno PKCS7
            mensaje_bytes = unpad(mensaje_padded)

            # 4. Convertir bytes a texto UTF-8 (JSON plano)
            mensaje = mensaje_bytes.decode('utf-8')

            print("Mensaje descifrado con éxito:", mensaje)

        except Exception as e_descifrado:
            print("Error al descifrar el mensaje LoRa:", e_descifrado)
            mensaje = None

        # ---------------------------------------------
        # PASO B: Publicar en MQTT (solo errores de red)
        # ---------------------------------------------
        publicado = False

        if mensaje is not None:

            try:
                # 5. Publicar en MQTT directamente en texto plano
                client.publish(
                    TOPIC_PUB,
                    mensaje
                )
                publicado = True

            except Exception as e:

                print("Error publicando MQTT:", e)

                # -----------------------------------------
                # Reconectar MQTT si se pierde la conexión
                # y reintentar UNA vez la publicación
                # -----------------------------------------
                try:

                    print("Reconectando MQTT...")

                    client = conectar_mqtt()

                    client.publish(
                        TOPIC_PUB,
                        mensaje
                    )
                    publicado = True

                    print("Mensaje publicado después de reconectar")

                except Exception as e2:

                    print("Error reconectando MQTT:", e2)

        # ---------------------------------------------
        # PASO C: Responder al nodo por LoRa
        # ACK  = el dato llegó al broker MQTT
        # NACK = no se pudo descifrar o no se pudo publicar
        # ---------------------------------------------
        if publicado:

            print("Publicado en MQTT (Texto plano):")
            print("Topic:", TOPIC_PUB.decode())
            print("Mensaje:", mensaje)

            time.sleep_ms(150)
            lora.send("ACK")
            lora.set_rx_mode()
            print("Confirmación (ACK) enviada al transmisor por LoRa")

        else:

            time.sleep_ms(50)
            lora.send("NACK")
            lora.set_rx_mode()
            print("Notificación de fallo (NACK) enviada por LoRa")


    # -----------------------------------------------------
    # Mantener MQTT activo (Ping periódicos)
    # -----------------------------------------------------

    if time.ticks_diff(
        time.ticks_ms(),
        ultimo_ping
    ) >= 20000:

        try:

            client.ping()

            print("MQTT activo")

        except Exception as e:

            print("Conexión MQTT perdida:", e)

            conectado = False

            while not conectado:

                try:

                    print("Intentando conectar nuevamente...")

                    client = conectar_mqtt()

                    conectado = True

                    print("MQTT reconectado")

                except Exception as e2:

                    print("Fallo conexión MQTT:", e2)

                    time.sleep(5)

        ultimo_ping = time.ticks_ms()


    time.sleep_ms(10)
