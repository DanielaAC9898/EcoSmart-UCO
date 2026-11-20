# Prueba del nodo RP2040: calibracion del semaforo + formato del mensaje cifrado
# Uso (desde tests/06_simulacion_v1.1/): micropython test_nodo.py ../../firmware/rp2040/nodo_exterior <archivo_salida.json>
import sys, json
CODIGO, SALIDA = sys.argv[1], sys.argv[2]
sys.path.insert(0, "mocks"); sys.path.insert(0, CODIGO)
import machine_fake, time_fake
sys.modules["machine"] = machine_fake
sys.modules["time"] = time_fake
import cryptolib, binascii

def trama(cm, checksum_ok=True, basura=b""):
    mm = int(round(cm * 10)); hi, lo = mm >> 8, mm & 0xFF
    cs = (0xFF + hi + lo) & 0xFF
    if not checksum_ok: cs = (cs + 1) & 0xFF
    return basura + bytes([0xFF, hi, lo, cs])

# (descripcion, respuesta del sensor, estado esperado, distancia esperada, LEDs esperados (V,A,R))
CASOS = [
    ("Caneca vacia 120 cm",        trama(120.0), "DISPONIBLE", 120.0, (1,0,0)),
    ("Justo encima de 70 (70.1)",  trama(70.1),  "DISPONIBLE", 70.1,  (1,0,0)),
    ("Limite 70.0 cm",             trama(70.0),  "MEDIO",      70.0,  (0,1,0)),
    ("Medio 55 cm",                trama(55.0),  "MEDIO",      55.0,  (0,1,0)),
    ("Limite 40.0 cm",             trama(40.0),  "MEDIO",      40.0,  (0,1,0)),
    ("Justo debajo de 40 (39.9)",  trama(39.9),  "LLENO",      39.9,  (0,0,1)),
    ("Lleno 25 cm",                trama(25.0),  "LLENO",      25.0,  (0,0,1)),
    ("Trama con ruido previo",     trama(85.3, basura=b"\x00\x12"), "DISPONIBLE", 85.3, (1,0,0)),
    ("Sensor sin respuesta (zona ciega)", None, "LLENO _UMBRAL", 0.0, (0,0,1)),
    ("Checksum invalido",          trama(60.0, checksum_ok=False), "LLENO _UMBRAL", 0.0, (0,0,1)),
    ("Lectura fuera de rango 600 cm", trama(600.0), "LLENO _UMBRAL", 0.0, (0,0,1)),
]
machine_fake.UART.RESPUESTAS = [c[1] for c in CASOS]

def al_dormir(s):
    if len(machine_fake.UART.RESPUESTAS) == 0:
        raise time_fake.StopTest()
time_fake.HOOK_SLEEP[0] = al_dormir

try:
    import main   # firmware/nodo_rp2040/main.py
except time_fake.StopTest:
    pass

import lora_lib
L = lora_lib.INSTANCIA[0]
key = b"1234567890123456"
ok_total = 0; resultados = []
print("\n================ RESULTADOS NODO ================")
for n, (desc, _, est_esp, dist_esp, leds_esp) in enumerate(CASOS):
    cif = L.con_ack[n]
    plano = cryptolib.aes(key, 1).decrypt(binascii.a2b_base64(cif))
    plano = plano[:-plano[-1]].decode()
    d = json.loads(plano)
    leds = L.leds_al_enviar[n]
    ok = d["estado"] == est_esp and abs(d["distancia_cm"] - dist_esp) < 0.05 and leds == leds_esp and d["msg_id"] == n
    ok_total += ok
    print("%s  %-34s estado=%-14s dist=%6.1f LEDs(V,A,R)=%s  bytes_LoRa=%d" % ("PASA" if ok else "FALLA", desc, d["estado"], d["distancia_cm"], leds, len(cif)))
    resultados.append(cif)
print("Total: %d/%d casos correctos" % (ok_total, len(CASOS)))
with open(SALIDA, "w") as f:
    json.dump(resultados, f)
