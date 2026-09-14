"""
Driver para sensor ultrasónico JSN-SR04T en MicroPython.
Compatible con RP2040 y ESP32.

Conexión:
  VCC  → 5V
  GND  → GND
  TRIG → pin configurado en config.py
  ECHO → pin configurado en config.py

Rango útil: 20 cm – 450 cm
"""

from machine import Pin, time_pulse_us
import time


class JSNSR04T:
    def __init__(self, trig_pin, echo_pin, timeout_us=30000):
        """
        trig_pin  : número de pin GPIO para TRIG
        echo_pin  : número de pin GPIO para ECHO
        timeout_us: tiempo máximo de espera en microsegundos (default 30 ms → ~5 m)
        """
        self.trig = Pin(trig_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.timeout_us = timeout_us
        self.trig.value(0)

    def distancia_cm(self):
        """
        Retorna la distancia medida en centímetros.
        Retorna None si no hay objeto detectado o hay error.
        """
        # Pulso de disparo: 10 µs
        self.trig.value(0)
        time.sleep_us(2)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)

        # Medir duración del eco
        duracion = time_pulse_us(self.echo, 1, self.timeout_us)

        if duracion < 0:
            return None  # Timeout: sin objeto detectado o fuera de rango

        # Velocidad del sonido: 343 m/s → 0.0343 cm/µs → dividir entre 2 (ida y vuelta)
        distancia = (duracion * 0.0343) / 2
        return round(distancia, 1)

    def nivel_llenado(self, altura_caneca_cm):
        """
        Calcula el porcentaje de llenado de la caneca.
        altura_caneca_cm: altura interior de la caneca en cm (distancia cuando está vacía)
        Retorna un valor entre 0 y 100, o None si hay error de lectura.
        """
        distancia = self.distancia_cm()
        if distancia is None:
            return None

        # Si la distancia es mayor a la altura, el sensor está mal instalado
        distancia = min(distancia, altura_caneca_cm)
        porcentaje = ((altura_caneca_cm - distancia) / altura_caneca_cm) * 100
        return round(porcentaje, 1)
