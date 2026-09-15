"""
Driver para sensor ultrasónico JSN-SR04T en MicroPython.
Modo 2 — Salida serial UART (R27 = 47K soldada).
Compatible con RP2040 y ESP32.

Conexión:
  VCC  → 5V
  GND  → GND
  TX del sensor → GP4 (RX del RP2040)  ← el sensor transmite, el RP2040 escucha
  RX del sensor → GP5 (TX del RP2040)  ← no se usa en modo solo lectura

Protocolo (cada 100ms el sensor envía 4 bytes):
  0xFF | H_DATA | L_DATA | SUM
  Distancia (mm) = (H_DATA << 8) | L_DATA
  SUM = (0xFF + H_DATA + L_DATA) & 0xFF

Rango útil: 200 mm – 4500 mm (20 cm – 450 cm)
"""

from machine import UART, Pin
import time


class JSNSR04T:
    def __init__(self, uart_id=1, tx_pin=5, rx_pin=4):
        """
        uart_id : ID del bus UART (1 por defecto en RP2040)
        tx_pin  : GP5 — TX del RP2040 (conectado a RX del sensor)
        rx_pin  : GP4 — RX del RP2040 (conectado a TX del sensor)
        """
        self.uart = UART(uart_id, baudrate=9600, tx=Pin(tx_pin), rx=Pin(rx_pin))
        time.sleep_ms(100)  # Esperar primer ciclo del sensor

    def distancia_cm(self):
        """
        Lee un frame válido del sensor.
        Retorna la distancia en centímetros, o None si hay error de lectura.
        """
        # Descartar bytes viejos del buffer
        self.uart.read()

        # Esperar un frame completo (el sensor emite cada 100ms)
        time.sleep_ms(150)

        if self.uart.any() < 4:
            return None

        datos = self.uart.read(4)

        if datos is None or len(datos) < 4:
            return None

        # Verificar byte de inicio
        if datos[0] != 0xFF:
            return None

        # Verificar checksum
        checksum = (0xFF + datos[1] + datos[2]) & 0xFF
        if checksum != datos[3]:
            return None

        distancia_mm = (datos[1] << 8) | datos[2]

        # Rango válido: 200mm – 4500mm
        if distancia_mm < 200 or distancia_mm > 4500:
            return None

        return round(distancia_mm / 10, 1)  # Convertir mm → cm

    def nivel_llenado(self, altura_caneca_cm):
        """
        Calcula el porcentaje de llenado de la caneca.
        altura_caneca_cm: altura interior de la caneca en cm (distancia cuando está vacía)
        Retorna un valor entre 0 y 100, o None si hay error de lectura.
        """
        distancia = self.distancia_cm()
        if distancia is None:
            return None

        distancia = min(distancia, altura_caneca_cm)
        porcentaje = ((altura_caneca_cm - distancia) / altura_caneca_cm) * 100
        return round(porcentaje, 1)
