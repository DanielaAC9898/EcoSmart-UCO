# Doble de prueba de la libreria LoRa del equipo
INSTANCIA = [None]
class LoRa:
    def __init__(self, spi, cs=None, reset=None, dio0=None, callback=None):
        self.callback = callback
        self.enviados = []        # lo que el gateway responde (ACK/NACK)
        self.con_ack = []         # lo que el nodo transmite
        self.leds_al_enviar = []
        self.rx_mode = 0
        INSTANCIA[0] = self
    def set_bandwidth(self, bw): self.bw = bw
    def set_rx_mode(self): self.rx_mode += 1
    def send(self, msg): self.enviados.append(msg)
    def send_with_ack(self, msg):
        import machine
        self.con_ack.append(msg)
        self.leds_al_enviar.append((machine.PINES[2].value(), machine.PINES[3].value(), machine.PINES[6].value()))
        return True
    def recibir(self, dato):   # simula la interrupcion DIO0
        self.callback(dato)
