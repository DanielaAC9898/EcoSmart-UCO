from machine import Pin, SPI
import time

# Registros constantes del SX1278
REG_FIFO = 0x00
REG_OP_MODE = 0x01
REG_FRF_MSB = 0x06
REG_FRF_MID = 0x07
REG_FRF_LSB = 0x08
REG_PA_CONFIG = 0x09
REG_FIFO_ADDR_PTR = 0x0D
REG_FIFO_TX_BASE_ADDR = 0x0E
REG_FIFO_RX_BASE_ADDR = 0x0F
REG_IRQ_FLAGS = 0x12
REG_MODEM_CONFIG_1 = 0x1D
REG_MODEM_CONFIG_2 = 0x1E
REG_PAYLOAD_LENGTH = 0x22

MODE_LONG_RANGE_MODE = 0x80
MODE_SLEEP = 0x00
MODE_STDBY = 0x01
MODE_TX = 0x03
MODE_RX_CONTINUOUS = 0x05

# Registros adicionales para RX e Interrupciones
REG_FIFO_RX_CURRENT_ADDR = 0x10
REG_IRQ_FLAGS = 0x12
REG_DIO_MAPPING_1 = 0x40
REG_MODEM_STAT = 0x18
REG_PKT_SNR_VALUE = 0x19
REG_PKT_RSSI_VALUE = 0x1A

IRQ_RX_DONE_MASK = 0x40
IRQ_TX_DONE_MASK = 0x08

REG_MODEM_CONFIG_1 = 0x1D
REG_MODEM_CONFIG_2 = 0x1E

REG_PA_DAC = 0x4D
REG_SYNC_WORD = 0x39

class LoRa:
    def __init__(self, spi, cs, reset, dio0, frequency=433E6, callback=None):
            self.spi = spi
            self.cs = Pin(cs, Pin.OUT, value=1)
            self.reset = Pin(reset, Pin.OUT)
            self.dio0 = Pin(dio0, Pin.IN)
            self.frequency = frequency
            self.on_receive = callback  # Función que se ejecuta al recibir datos
            
            self.reset_module()
            self.init_lora()
            
            # Configurar interrupción en el pin DIO0 (flanco de subida)
            self.dio0.irq(handler=self._handle_interrupt, trigger=Pin.IRQ_RISING)

    def _handle_interrupt(self, pin):
            irq_flags = self.read_reg(REG_IRQ_FLAGS)
            
            # Caso: Recepción Completa
            if irq_flags & IRQ_RX_DONE_MASK:
                # Limpiar flag de interrupción en el chip
                self.write_reg(REG_IRQ_FLAGS, IRQ_RX_DONE_MASK)
                
                # Leer dirección del último paquete recibido
                current_addr = self.read_reg(REG_FIFO_RX_CURRENT_ADDR)
                self.write_reg(REG_FIFO_ADDR_PTR, current_addr)
                
                # Leer longitud del paquete
                packet_len = self.read_reg(0x13) # REG_RX_NB_BYTES
                
                payload = []
                for _ in range(packet_len):
                    payload.append(chr(self.read_reg(REG_FIFO)))
                
                data = "".join(payload)
                
                # Ejecutar callback del usuario si existe
                if self.on_receive:
                    self.on_receive(data)

            # Caso: Envío Completo
            elif irq_flags & IRQ_TX_DONE_MASK:
                self.write_reg(REG_IRQ_FLAGS, IRQ_TX_DONE_MASK)

    def set_rx_mode(self):
        # Mapear DIO0 a RXDone (00 en los bits 7-6 de REG_DIO_MAPPING_1)
        self.write_reg(REG_DIO_MAPPING_1, 0x00)
        self.write_reg(REG_OP_MODE, 0x80 | 0x05) # LoRa + RX CONTINUOUS

    def reset_module(self):
        self.reset.value(0)
        time.sleep(0.01)
        self.reset.value(1)
        time.sleep(0.01)

    def write_reg(self, reg, val):
        self.cs.value(0)
        self.spi.write(bytearray([reg | 0x80, val]))
        self.cs.value(1)

    def read_reg(self, reg):
        self.cs.value(0)
        self.spi.write(bytearray([reg & 0x7F]))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def init_lora(self):
        # 1. Poner en modo Sleep para configurar
        self.write_reg(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_SLEEP)
        
        # 2. Configurar frecuencia (433MHz)
        # F_steps = (frequency * 2^19) / 32,000,000
        f_steps = int((self.frequency * 524288) / 32000000)
        self.write_reg(REG_FRF_MSB, (f_steps >> 16) & 0xFF)
        self.write_reg(REG_FRF_MID, (f_steps >> 8) & 0xFF)
        self.write_reg(REG_FRF_LSB, f_steps & 0xFF)
        
        # 3. Configurar Modulación
        # REG_MODEM_CONFIG_1 (0x1D): BW=125kHz (0x70), CodingRate=4/5 (0x02), ExplicitHeader (0x00)
        self.write_reg(REG_MODEM_CONFIG_1, 0x82) 
        
        # REG_MODEM_CONFIG_2 (0x1E): SF7 (0x70), CRC=On (0x04)
        self.write_reg(REG_MODEM_CONFIG_2, 0x74) 
        
        # 4. Configurar Sync Word (Crucial: 0x12 es el default)
        self.write_reg(REG_SYNC_WORD, 0x12)
        
        # 5. Configurar Potencia y PA_BOOST (Recomendado para Ra-02)
        self.write_reg(REG_PA_CONFIG, 0x8F) # OutputPower=15dBm, PA_BOOST habilitado
        # self.write_reg(REG_PA_DAC, 0x87) # Opcional: Max power si es necesario (17-20dBm)

        # 6. Preparamos el FIFO para RX
        self.write_reg(REG_FIFO_TX_BASE_ADDR, 0x00)
        self.write_reg(REG_FIFO_RX_BASE_ADDR, 0x00)
        
        # REG_PREAMBLE_LSB = 0x21
        self.write_reg(0x21, 12)

        # 7. Finalmente, Standby para confirmar los cambios
        self.write_reg(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_STDBY)

    def send(self, data):
        self.write_reg(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_STDBY)
        self.write_reg(REG_FIFO_ADDR_PTR, 0)
        self.write_reg(REG_PAYLOAD_LENGTH, len(data))
        
        for char in data:
            self.write_reg(REG_FIFO, ord(char))
            
        self.write_reg(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_TX)
        
        # Esperar a que termine de enviar (opcional: usar interrupción en DIO0)
        while not (self.read_reg(REG_IRQ_FLAGS) & 0x08):
            pass
        self.write_reg(REG_IRQ_FLAGS, 0x08) # Limpiar flag TX Done
        
    def get_rssi(self):
        # Para el SX1278 a 433MHz, el RSSI se calcula: -164 + reg_value
        return self.read_reg(REG_PKT_RSSI_VALUE) - 164

    def get_snr(self):
        # El valor es un byte con signo (complemento a 2)
        value = self.read_reg(REG_PKT_SNR_VALUE)
        if value > 127:
            value = (256 - value) * -1
        return value / 4

    def send_with_ack(self, data, timeout_ms=3000):
        self.send(data)
        time.sleep_ms(10) # El "respiro" para el hardware
        
        self.write_reg(0x12, 0xFF) # Limpiar interrupciones previas
        self.set_rx_mode()
        
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
            # VALIDACIÓN: Leemos el registro de interrupciones (IRQ_FLAGS)
            irq_flags = self.read_reg(0x12)
            
            # 0x40 es la máscara para RX_DONE (Paquete recibido)
            if irq_flags & 0x40:
                # Opcional: Validar CRC (0x20 es PayloadCrcError)
                if irq_flags & 0x20:
                    print("⚠️ Paquete recibido pero con CRC corrupto")
                    self.write_reg(0x12, 0x20) # Limpiar error y seguir esperando
                    continue
                    
                # Si llegó aquí, el ACK es físicamente válido
                print(f"ACK detectado (RSSI: {self.get_rssi()})")
                self.write_reg(0x12, 0xFF) # Limpiar flags
                return True
                
            time.sleep_ms(5) # Pequeña pausa para no saturar el bus SPI
            
        return False

    def send_ack(self):
        self.write_reg(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_STDBY)
        
        # Limpiar punteros del FIFO
        self.write_reg(REG_FIFO_ADDR_PTR, 0)
        self.write_reg(REG_FIFO_TX_BASE_ADDR, 0)
        
        # Escribir el ACK
        data = "ACK_CONFIRM_RECEIVE_OK"
        self.write_reg(REG_PAYLOAD_LENGTH, len(data))
        for char in data:
            self.write_reg(REG_FIFO, ord(char))
            
        # El delay es la clave: 50ms es el "punto dulce"
        time.sleep_ms(50) 
        
        self.write_reg(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_TX)
        
        # Esperar TX_DONE con timeout de seguridad
        start = time.ticks_ms()
        while not (self.read_reg(REG_IRQ_FLAGS) & 0x08):
            if time.ticks_diff(time.ticks_ms(), start) > 500: break
                
        self.write_reg(REG_IRQ_FLAGS, 0xFF) # Limpiar todos los flags
        self.set_rx_mode()
        
    def set_spreading_factor(self, sf):
        if sf < 6 or sf > 12:
            raise ValueError("SF debe estar entre 6 y 12")
        
        # El SF se guarda en los 4 bits más significativos de REG_MODEM_CONFIG_2
        # También activamos la detección de CRC para asegurar datos limpios
        current_setting = self.read_reg(REG_MODEM_CONFIG_2)
        new_setting = (current_setting & 0x0F) | (sf << 4) | 0x04 # 0x04 activa RX Payload CRC Check
        
        self.write_reg(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_STDBY)
        self.write_reg(REG_MODEM_CONFIG_2, new_setting)
        
        # Nota: Si usas SF11 o SF12, se recomienda activar el Low Data Rate Optimize
        if sf >= 11:
            config1 = self.read_reg(REG_MODEM_CONFIG_1)
            self.write_reg(REG_MODEM_CONFIG_1, config1 | 0x01) # LowDataRateOptimize = 1
            
        print(f"Modo configurado a SF{sf}")

    def set_bandwidth(self, bw_hz):
        # BW se configura en REG_MODEM_CONFIG_1 (bits 7-4)
        # 7: 125kHz (default), 8: 250kHz, 9: 500kHz
        bw_map = {125000: 7, 250000: 8, 500000: 9}
        if bw_hz in bw_map:
            val = bw_map[bw_hz]
            current = self.read_reg(REG_MODEM_CONFIG_1)
            self.write_reg(REG_MODEM_CONFIG_1, (current & 0x0F) | (val << 4))
            
    def set_frequency(self, frequency):
        """
        Ajusta la frecuencia de operación en Hz (ej. 433E6)
        """
        # 1. Validación de rango para el SX1278 (Banda de 433MHz)
        if frequency < 410E6 or frequency > 525E6:
            print("Advertencia: Frecuencia fuera de rango para Ra-02")
            return

        # 2. El chip debe estar en SLEEP o STDBY para cambiar frecuencia
        current_mode = self.read_reg(REG_OP_MODE)
        self.write_reg(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_SLEEP)

        # 3. Cálculo del valor de 24 bits (F_osc = 32,000,000 Hz)
        # Valor = (F_target * 2^19) / 32,000,000
        f_steps = int((frequency * 524288) / 32000000)

        # 4. Escribir en los registros FRF_MSB (0x06), MID (0x07) y LSB (0x08)
        self.write_reg(0x06, (f_steps >> 16) & 0xFF)
        self.write_reg(0x07, (f_steps >> 8) & 0xFF)
        self.write_reg(0x08, f_steps & 0xFF)

        self.frequency = frequency
        
        # 5. Volver al modo anterior (o Standby por seguridad)
        self.write_reg(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_STDBY)
        print(f"Frecuencia ajustada a: {frequency/1E6:.3f} MHz")
        
    def set_tx_power(self, level, high_power=False):
        """
        Ajusta la potencia de transmisión.
        :param level: Nivel de potencia de 2 a 17 (dBm).
        :param high_power: Si es True, activa el modo de 20dBm (usa más batería).
        """
        # 1. Validar el rango de entrada
        if level < 2: level = 2
        if level > 17: level = 17

        # 2. El chip debe estar en Standby para cambiar configuración de potencia
        self.write_reg(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_STDBY)

        if not high_power:
            # Configuración estándar (PA_BOOST activado)
            # El cálculo para PA_BOOST es: Pout = 2 + OutputPower
            # Queremos que 'level' sea el Pout real.
            output_power = level - 2
            # Bit 7 (PaBoost)=1, Bits 6-4 (MaxPower)=111, Bits 3-0 (OutputPower)
            self.write_reg(0x09, 0x80 | 0x70 | output_power)
            
            # Desactivar el DAC de alta potencia (Modo normal)
            self.write_reg(0x4D, 0x84) 
        else:
            # Modo de alta potencia (20 dBm)
            # Forzamos los registros para máxima salida
            self.write_reg(0x09, 0xFF) 
            # REG_PA_DAC (0x4D): 0x87 activa los +20dBm
            self.write_reg(0x4D, 0x87) 
            print("Modo de alta potencia (20dBm) activado. Cuidado con el consumo.")

        print(f"Potencia de TX configurada a: {level if not high_power else 20} dBm")
