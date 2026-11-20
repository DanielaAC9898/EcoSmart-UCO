"""
Conexión WiFi compartida (ESP32).
Usada por el gateway LoRa->MQTT y por el nodo interior directo, para
no duplicar la misma lógica de conexión en los dos main.py.
"""
import network
import time


def conectar_wifi(ssid, password, intentos=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    print("Conectando a WiFi", end="")
    for _ in range(intentos):
        if wlan.isconnected():
            break
        print(".", end="")
        time.sleep(1)
    if wlan.isconnected():
        print(f"\nWiFi OK -- IP: {wlan.ifconfig()[0]}")
    else:
        print("\nError: no se pudo conectar al WiFi")
    return wlan.isconnected()
