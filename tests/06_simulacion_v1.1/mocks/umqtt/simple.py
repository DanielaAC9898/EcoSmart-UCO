# Doble de prueba de umqtt.simple con inyeccion de fallas
ESTADO = {"conexiones": 0, "publicados": [], "fallar_publish": 0, "fallar_connect": 0, "fallar_ping": 0, "pings": 0}
class MQTTClient:
    def __init__(self, client_id, server, port=1883, keepalive=0, **k):
        self.server = server; self.port = port
    def connect(self):
        if ESTADO["fallar_connect"] > 0:
            ESTADO["fallar_connect"] -= 1
            raise OSError(113)      # EHOSTUNREACH
        ESTADO["conexiones"] += 1
    def publish(self, topic, msg, retain=False, qos=0):
        if ESTADO["fallar_publish"] > 0:
            ESTADO["fallar_publish"] -= 1
            raise OSError(104)      # ECONNRESET
        ESTADO["publicados"].append((topic, msg))
    def ping(self):
        if ESTADO["fallar_ping"] > 0:
            ESTADO["fallar_ping"] -= 1
            raise OSError(104)
        ESTADO["pings"] += 1
