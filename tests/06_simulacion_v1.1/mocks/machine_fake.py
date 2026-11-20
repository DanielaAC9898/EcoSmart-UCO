# Doble de prueba (mock) del modulo machine para correr en MicroPython Unix
PINES = {}
class Pin:
    OUT = 1
    IN = 0
    def __init__(self, n, mode=None, *a, **k):
        self.n = n; self._v = 0
        PINES[n] = self
    def value(self, v=None):
        if v is None: return self._v
        self._v = v
class SPI:
    def __init__(self, *a, **k): pass
class UART:
    # RESPUESTAS: lista de bytes que el "sensor" devuelve tras cada comando 0x01
    RESPUESTAS = []
    def __init__(self, *a, **k): self.buf = b""
    def any(self): return len(self.buf)
    def read(self):
        b = self.buf; self.buf = b""; return b if b else None
    def write(self, data):
        if UART.RESPUESTAS:
            r = UART.RESPUESTAS.pop(0)
            self.buf = r if r is not None else b""
def unique_id():
    return bytes([0xe6, 0x61, 0x18, 0xc4, 0x17, 0x86, 0x7e, 0x21])
