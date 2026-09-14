# EcoSmart UCO — Red IoT de monitoreo de puntos ecológicos

Red de sensores IoT para monitorear el nivel de llenado de los puntos ecológicos de la Universidad Católica de Oriente.

## Arquitectura (Parcial — Capas 1 a 3)

```
JSN-SR04T → RP2040 → LoRa SX1278 → ESP32 → WiFi → Mosquitto (consola)
```

## Estructura del repositorio

```
firmware/
  common/         Librerías compartidas (LoRa, sensor)
  rp2040/         Nodo exterior transmisor
  esp32/          Gateway LoRa → MQTT
tests/
  01_sensor/      Prueba aislada del sensor JSN-SR04T
  02_lora_pingpong/ Prueba de comunicación LoRa básica
  03_lora_con_sensor/ LoRa + sensor integrados
gateway/
  mosquitto.conf  Configuración del broker
  subscriber.py   Suscriptor en consola (PC/RPi)
```

## Orden de pruebas recomendado

1. `tests/01_sensor/` — verificar que el sensor lee distancia correctamente
2. `tests/02_lora_pingpong/` — verificar que LoRa transmite y recibe
3. `tests/03_lora_con_sensor/` — integración sensor + LoRa
4. `firmware/` — versión final integrada con MQTT

## Hardware

| Componente | Uso |
|---|---|
| Raspberry Pi Pico (RP2040) | Nodo exterior transmisor |
| ESP32 | Gateway receptor LoRa + WiFi |
| LoRa SX1278 (Ra-02) | Comunicación de largo alcance |
| JSN-SR04T | Sensor ultrasónico de nivel (waterproof) |

## Integrantes

- Johan Steven Ochoa
- Wendy Daniela Alzate
- José Manuel Pavas
