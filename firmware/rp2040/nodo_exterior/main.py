#CODIGO NODO RP2040 + LORA + AUTENTICACION
import machine
from machine import Pin, SPI, UART
from lora_lib import LoRa
import time
import json
import cryptolib
import ubinascii

# 1. Clave de exactamente 16 bytes (128 bits) para AES-128
key = b"1234567890123456"

# 2. Configuración de LEDs
led_verde = Pin(2, Pin.OUT)
led_amarillo = Pin(3, Pin.OUT)
led_rojo = Pin(6, Pin.OUT)

# 3. Configuración SPI0 para módulo LoRa (SX1278)
spi = SPI(0, baudrate=1000000, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
lora = LoRa(spi, cs=17, reset=15, dio0=14)
lora.set_bandwidth(125000)

# 4. Configuración UART1 para AJ-SR04M (Modo 4 - 47k)
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# 5. Calibración final del semáforo (v1.1)
#    Nivel  LED       Llenado     Distancia medida
#    Bajo   Verde     0 a 50 %    más de 70 cm
#    Medio  Amarillo  50 a 80 %   entre 40 y 70 cm
#    Alto   Rojo      más de 80 % menos de 40 cm
UMBRAL_ALTO_CM = 40.0    # por debajo de este valor -> LLENO (rojo)
UMBRAL_MEDIO_CM = 70.0   # entre 40 y 70 cm (inclusive) -> MEDIO (amarillo)

# Función de relleno PKCS7 para ajustar los datos a múltiplos de 16 bytes
def pad(data_bytes):
    pad_len = 16 - (len(data_bytes) % 16)
    return data_bytes + bytes([pad_len] * pad_len)

def read_raw_distance():
    if uart.any():
        uart.read()

    uart.write(b'\x01')
    time.sleep_ms(100)

    if uart.any():
        raw_bytes = uart.read()
        for i in range(len(raw_bytes) - 3):
            if raw_bytes[i] == 0xFF:
                high, low, checksum = raw_bytes[i+1], raw_bytes[i+2], raw_bytes[i+3]
                if (0xFF + high + low) & 0xFF == checksum:
                    return ((high << 8) + low) / 10.0
    return None

def Semaforo():
    raw_dist = read_raw_distance()

    led_verde.value(0)
    led_amarillo.value(0)
    led_rojo.value(0)

    # 1. Tratamiento de zona ciega o error
    # Si la basura tapa el sensor (menos de 20cm) a veces arroja None o valores >500.0
    if raw_dist is None or raw_dist > 500.0:
        led_rojo.value(1)
        return 0.0, "LLENO _UMBRAL"

    # 2. Nivel Alto (>80%): Menos de 40 cm
    elif raw_dist < UMBRAL_ALTO_CM:
        led_rojo.value(1)
        return raw_dist, "LLENO"

    # 3. Nivel Medio (50% a 80%): Entre 40 cm y 70 cm
    elif raw_dist <= UMBRAL_MEDIO_CM:
        led_amarillo.value(1)
        return raw_dist, "MEDIO"

    # 4. Nivel Bajo (0 a 50%): Más de 70 cm
    else:
        led_verde.value(1)
        return raw_dist, "DISPONIBLE"

print("--- TRANSMISOR PICO (JSON + AES + MAC) + LORA INICIADO ---")

# --- AUTENTICACIÓN: Obtener la "MAC" (ID Único) de la RP2040 ---
uid_bytes = machine.unique_id()
uid_hex = ubinascii.hexlify(uid_bytes).decode('utf-8')
mac_pico = ':'.join(uid_hex[i:i+2] for i in range(0, len(uid_hex), 2))
print("MAC/ID asignada a este nodo:", mac_pico)
# --------------------------------------------------------------

i = 0

while True:
    dist, estado = Semaforo()

    # 1. Creación del diccionario de datos (Incluyendo la MAC)
    data = {
        "msg_id": i,
        "estado": estado,
        "distancia_cm": round(dist, 1),
        "nodo_Id": "ECO-2",
        "mac": mac_pico
    }

    # 2. Convertir a JSON
    mensaje = json.dumps(data)

    # 3. Convertir a bytes y aplicar relleno PKCS7
    mensaje_bytes = mensaje.encode('utf-8')
    mensaje_padded = pad(mensaje_bytes)

    # 4. Cifrar con AES en modo ECB
    cipher = cryptolib.aes(key, 1)
    bytes_cifrados = cipher.encrypt(mensaje_padded)

    # 5. Convertir a Base64
    mensaje_cifrado = ubinascii.b2a_base64(bytes_cifrados).decode('utf-8').strip()

    print("JSON plano:", mensaje)
    print("Enviando Cifrado:", mensaje_cifrado)

    if lora.send_with_ack(mensaje_cifrado):
        print("Confirmado por receptor")
    else:
        print("Sin respuesta de receptor LoRa")

    time.sleep(5)
    i += 1
