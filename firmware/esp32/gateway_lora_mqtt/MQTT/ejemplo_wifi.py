"""
PROVISIONAL -- reemplazar por el archivo original del equipo.

El gateway (main.py) importa `conectar_wifi` desde `MQTT/ejemplo_wifi.py`,
pero ese archivo original no estaba en el repositorio (pendiente: pedirlo
al equipo). Este reemplazo solo reutiliza la conexión compartida de
`firmware/common/wifi.py` y las credenciales de `secrets.py`, para que el
proyecto quede completo e importable.

En la placa: copiar `firmware/common/wifi.py` a la raíz del ESP32 y crear
`secrets.py` a partir de `secrets_ejemplo.py`.
"""


def conectar_wifi(ssid=None, password=None):
    from wifi import conectar_wifi as _conectar
    if ssid is None:
        from secrets import WIFI_SSID as ssid, WIFI_PASSWORD as password
    return _conectar(ssid, password)
