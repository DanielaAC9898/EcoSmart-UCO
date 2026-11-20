# Prueba del gateway ESP32: descifrado, publicacion MQTT, reconexion y ACK/NACK
# Uso (desde tests/06_simulacion_v1.1/): micropython test_gateway.py ../../firmware/esp32/gateway_lora_mqtt <mensajes_del_nodo.json>
import sys, json
CODIGO, MSGS = sys.argv[1], sys.argv[2]
sys.path.insert(0, "mocks"); sys.path.insert(0, CODIGO)
import machine_fake, time_fake
sys.modules["machine"] = machine_fake
sys.modules["time"] = time_fake
import cryptolib, binascii
from umqtt import simple as mq
import lora_lib

with open(MSGS) as f:
    cifrados = json.load(f)
key = b"1234567890123456"
def descifrar(c):
    p = cryptolib.aes(key, 1).decrypt(binascii.a2b_base64(c)); return p[:-p[-1]].decode()

# Cada escenario: (descripcion, dato LoRa, preparar_fallas, verificacion)
def foto():
    return (len(mq.ESTADO["publicados"]), mq.ESTADO["conexiones"], len(lora_lib.INSTANCIA[0].enviados))

ESC = [
  ("E1 Mensaje valido, MQTT OK",
     cifrados[0], {}, "ACK", 1, 0),
  ("E2 Mensaje valido, MQTT se cae y la reconexion funciona",
     cifrados[5], {"fallar_publish": 1}, "ACK", 1, 1),
  ("E3 Mensaje valido, MQTT caido y el broker no responde",
     cifrados[6], {"fallar_publish": 1, "fallar_connect": 1}, "NACK", 0, 0),
  ("E4 Trama corrupta (Base64 invalido)",
     "@@no-es-base64@@", {}, "NACK", 0, 0),
  ("E5 Trama con longitud que no es multiplo de 16",
     binascii.b2a_base64(b"x"*10).decode().strip(), {}, "NACK", 0, 0),
  ("E6 Recuperacion: mensaje valido despues de las fallas",
     cifrados[8], {}, "ACK", 1, 0),
]
resultados = []
estado = {"tick": 0, "i": -1, "antes": None, "esperando": False}

def cerrar_escenario():
    k = estado["i"]
    desc, dato, _, resp_esp, pub_esp, recon_esp = ESC[k]
    p0, c0, s0 = estado["antes"]; p1, c1, s1 = foto()
    L = lora_lib.INSTANCIA[0]
    resp = L.enviados[-1] if s1 > s0 else "(ninguna)"
    pub_ok = (p1 - p0) == pub_esp
    if pub_esp == 1 and pub_ok:
        pub_ok = mq.ESTADO["publicados"][-1][1] == descifrar(dato)   # se publico el JSON correcto
    ok = resp == resp_esp and pub_ok and (c1 - c0) == recon_esp
    resultados.append((ok, desc, resp, p1 - p0, c1 - c0, resp_esp, pub_esp, recon_esp))

def tick():
    estado["tick"] += 1
    if estado["esperando"]:
        cerrar_escenario(); estado["esperando"] = False
    if estado["tick"] % 5 == 0:
        estado["i"] += 1
        if estado["i"] < len(ESC):
            desc, dato, fallas, *_ = ESC[estado["i"]]
            for k, v in fallas.items(): mq.ESTADO[k] = v
            estado["antes"] = foto()
            lora_lib.INSTANCIA[0].recibir(dato)
            estado["esperando"] = True
        elif estado["i"] == len(ESC):
            mq.ESTADO["fallar_ping"] = 1          # E7: se cae la conexion en el ping periodico
            estado["con_antes_ping"] = mq.ESTADO["conexiones"]
    if time_fake.AHORA[0] > 45000:                # dos ciclos de ping (cada 20 s)
        raise time_fake.StopTest()
time_fake.HOOK_TICK[0] = tick

crash = None
try:
    import main   # firmware/gateway_esp32/main.py
except time_fake.StopTest:
    pass
except Exception as e:
    crash = e

print("\n================ RESULTADOS GATEWAY ================")
n_ok = 0
for ok, desc, resp, pub, rec, re_, pe, ce in resultados:
    n_ok += ok
    print("%s  %s\n       respuesta LoRa=%s (esperada %s) | publicaciones=%d (esp. %d) | reconexiones=%d (esp. %d)" % ("PASA " if ok else "FALLA", desc, resp, re_, pub, pe, rec, ce))
e7 = crash is None and mq.ESTADO["pings"] >= 1 and mq.ESTADO["conexiones"] - estado["con_antes_ping"] == 1
print("%s  E7 El ping periodico detecta la caida y reconecta (pings OK=%d, reconexiones por ping=%d, esp. 1)" % ("PASA " if e7 else "FALLA", mq.ESTADO["pings"], mq.ESTADO["conexiones"] - estado["con_antes_ping"]))
n_ok += e7
print("Programa siguio corriendo sin bloquearse: %s" % ("SI" if crash is None else "NO -> %r" % crash))
print("Total: %d/%d escenarios correctos" % (n_ok, len(ESC) + 1))
