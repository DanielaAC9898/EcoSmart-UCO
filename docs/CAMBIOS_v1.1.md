# EcoSmart UCO — Registro de cambios v1.1

**Fecha:** 16 de noviembre de 2026
**Alcance:** firmware del gateway ESP32 y del nodo RP2040
**Estado:** probado en simulación ✅ · validación en hardware ⏳ (ver §5)

---

## 1. Resumen

| ID | Archivo | Tipo | Descripción |
|---|---|---|---|
| H1 | `firmware/esp32/gateway_lora_mqtt/main.py` | Corrección de error | La reconexión MQTT nunca se ejecutaba. El descifrado y la publicación quedan en bloques `try` separados. |
| H2 | `firmware/rp2040/nodo_exterior/main.py` | Calibración | Umbrales del semáforo actualizados a la calibración final (40 cm / 70 cm) y escritos como constantes. |

No cambiaron el formato del mensaje (JSON), los identificadores (`ECO-2`), el tópico MQTT (`iot`), los pines ni la clave. **Node-RED, MySQL y Grafana no requieren ningún cambio.** Las diferencias exactas línea por línea están en `cambios_gateway.diff` y `cambios_nodo.diff`.

---

## 2. H1 — Corrección de la reconexión MQTT en el gateway

### Causa
```python
try:
    ...descifrar... ; client.publish(...)
except Exception:      # se evalúa primero y atrapa TODO
    ...NACK...
except OSError:        # inalcanzable: OSError es subclase de Exception
    ...reconectar...
```
Python usa el **primer** `except` compatible. Un fallo de red al publicar (`OSError`) caía en el primer bloque, se reportaba como "Error al descifrar", se enviaba NACK y **nunca se reconectaba**.

### Solución
El procesamiento ahora tiene tres pasos independientes:

| Paso | Qué hace | Si falla |
|---|---|---|
| A. Descifrar | Base64 → AES → quitar relleno → texto | `mensaje = None` |
| B. Publicar | `client.publish(...)`. Si falla, reconecta y reintenta **una** vez | `publicado = False` |
| C. Responder | `ACK` si `publicado`, `NACK` en cualquier otro caso | — |

Con esto el **ACK significa "el dato llegó al broker"**, que es la semántica de extremo a extremo que se quería.

---

## 3. H2 — Calibración final del semáforo

| Nivel | LED | Llenado | Distancia medida | Regla en código |
|---|---|---|---|---|
| Bajo | Verde | 0 a 50 % | más de 70 cm | `d > 70` |
| Medio | Amarillo | 50 a 80 % | entre 40 y 70 cm | `40 <= d <= 70` |
| Alto | Rojo | más de 80 % | menos de 40 cm | `d < 40` |
| Sin lectura | Rojo | — | sin respuesta, checksum inválido o > 500 cm | `LLENO _UMBRAL`, distancia 0.0 |

Constantes nuevas: `UMBRAL_ALTO_CM = 40.0` y `UMBRAL_MEDIO_CM = 70.0`. Para recalibrar otra caneca solo se cambian estas dos líneas.

> **Nota de diseño:** la tabla implica una caneca con unos 100 cm de profundidad útil y el sensor unos 20 cm por encima del nivel máximo. Esos 20 cm coinciden con la zona ciega del AJ-SR04M, así que la calibración es físicamente coherente.

---

## 4. Evidencia de pruebas

### Método
El firmware se ejecutó **sin modificaciones** en el intérprete oficial de **MicroPython v1.24.1 (port Unix)**, que trae los mismos `cryptolib`, `ubinascii` y `json` que usa el ESP32/RP2040. El hardware se reemplazó por **dobles de prueba (mocks)** en `tests/06_simulacion_v1.1/mocks/`:

| Mock | Simula |
|---|---|
| `machine_fake.py` | Pines de los LEDs y UART del AJ-SR04M (devuelve tramas `0xFF + alto + bajo + checksum`) |
| `lora_lib.py` | Radio SX1278: guarda lo transmitido y dispara la interrupción de recepción |
| `umqtt/simple.py` | Broker MQTT con **inyección de fallas** (caída al publicar, broker inalcanzable, falla en ping) |
| `time_fake.py` | Reloj virtual para recorrer 45 s de operación en milisegundos |

Ambos archivos además **compilan con `mpy-cross`** (el compilador oficial de MicroPython), lo que descarta errores de sintaxis.

### Resultados del nodo RP2040 (11 casos)

| Caso | Estado | LEDs (V,A,R) | v1.1 | Original |
|---|---|---|---|---|
| Vacía 120 cm | DISPONIBLE | 1,0,0 | ✅ | ✅ |
| 70.1 cm | DISPONIBLE | 1,0,0 | ✅ | ✅ |
| Límite 70.0 cm | MEDIO | 0,1,0 | ✅ | ❌ (daba DISPONIBLE) |
| 55 cm | MEDIO | 0,1,0 | ✅ | ❌ |
| Límite 40.0 cm | MEDIO | 0,1,0 | ✅ | ❌ |
| 39.9 cm | LLENO | 0,0,1 | ✅ | ❌ |
| 25 cm | LLENO | 0,0,1 | ✅ | ❌ |
| Trama con ruido previo | DISPONIBLE | 1,0,0 | ✅ | ✅ |
| Sensor sin respuesta | LLENO _UMBRAL | 0,0,1 | ✅ | ✅ |
| Checksum inválido | LLENO _UMBRAL | 0,0,1 | ✅ | ✅ |
| 600 cm (fuera de rango) | LLENO _UMBRAL | 0,0,1 | ✅ | ✅ |
| **Total** | | | **11/11** | 6/11 |

En cada caso se verificó además que el mensaje cifrado se descifra al JSON correcto con `msg_id` consecutivo. Tamaño de la trama LoRa: 152 a 172 caracteres (el límite del SX1278 es 255 bytes).

### Resultados del gateway ESP32 (7 escenarios)

Las tramas de prueba son **las que produjo el nodo v1.1**, así que la prueba también valida que nodo y gateway son compatibles.

| Escenario | Esperado | v1.1 | Original |
|---|---|---|---|
| E1 Mensaje válido, MQTT OK | Publica + ACK | ✅ | ✅ |
| **E2 MQTT se cae, la reconexión funciona** | Reconecta + publica + ACK | ✅ | ❌ **NACK, sin reconexión, dato perdido** |
| E3 MQTT caído y broker inalcanzable | NACK, no se bloquea | ✅ | ✅ |
| E4 Base64 inválido | NACK, no publica | ✅ | ✅ |
| E5 Longitud no múltiplo de 16 | NACK, no publica | ✅ | ✅ |
| E6 Mensaje válido después de las fallas | Publica + ACK | ✅ | ✅ |
| E7 Falla en el ping periódico | Reconecta | ✅ | ✅ |
| **Total** | | **7/7** | 6/7 |

El escenario E2 reproduce el error H1 en el código original y demuestra que la v1.1 lo corrige. La salida completa está en `evidencia_pruebas.txt`.

### Cómo repetir las pruebas
```bash
# 1. Compilar MicroPython (una sola vez)
git clone --depth 1 -b v1.24.1 https://github.com/micropython/micropython.git
make -C micropython/mpy-cross && make -C micropython/ports/unix submodules && make -C micropython/ports/unix
MP=micropython/ports/unix/build-standard/micropython
# 2. Ejecutar (desde la carpeta tests/06_simulacion_v1.1/)
$MP test_nodo.py    ../../firmware/rp2040/nodo_exterior     mensajes.json
$MP test_gateway.py ../../firmware/esp32/gateway_lora_mqtt  mensajes.json
```

---

## 5. ⏳ Validar al finalizar la documentación

### 5.1 Validación de la v1.1 en hardware real (obligatoria antes de cerrar)
La simulación prueba la **lógica**. No prueba el radio, el Wi-Fi ni el sensor físico.

- [ ] **H1-HW1:** con el sistema funcionando, detener el broker en la Raspberry Pi (`sudo systemctl stop mosquitto`), esperar una transmisión del nodo y volver a iniciarlo. Esperado: el gateway reconecta solo y el dato aparece en Grafana.
- [ ] **H1-HW2:** apagar el router unos 30 s. Esperado: NACK en el nodo y recuperación automática al volver la red.
- [ ] **H2-HW1:** medir con cinta métrica a 30, 55 y 90 cm. Esperado: rojo, amarillo y verde, con la distancia del dashboard dentro de ±2 cm.
- [ ] Grabar en video H1-HW1 y H2-HW1: sirven como evidencia para el informe de pruebas y para el video de Uqui.

### 5.2 Mejoras de seguridad (temas en aprendizaje)

**H3 — Cifrado y autenticación del enlace LoRa**
- *Hoy:* AES-128 en modo ECB con clave fija en el código, y el `unique_id` del RP2040 como identificador.
- *Conceptos por aprender:* cifrar (que nadie lea) ≠ autenticar (que nadie modifique ni suplante); por qué ECB repite patrones; qué es un ataque de repetición (*replay*); la diferencia entre MAC (dirección de red), HMAC (código de autenticación) y `unique_id` (número de serie del chip).
- *Mejora propuesta:* AES-CBC con IV aleatorio + HMAC-SHA256 + contador que el gateway exige creciente; clave en `secrets.py` fuera de Git (`.gitignore`).
- *Mínimo para la entrega:* sacar la clave del repositorio público y documentar en el informe de seguridad las limitaciones conocidas. Reconocer una limitación también es buena ingeniería.

**H4 — Autenticación en MQTT**
- *Hoy:* Mosquitto en el puerto 1883 sin usuario ni contraseña; el JSON viaja en texto plano dentro de la red local.
- *Mejora propuesta:* `allow_anonymous false` + `password_file` + ACL por tópico (usuario `gateway` solo publica en `iot`; usuario `nodered` solo se suscribe). Después, TLS en el puerto 8883.
- *Impacto:* hay que actualizar `conectar_mqtt()` (parámetros `user` y `password`) y la configuración del broker en Node-RED.

**H5 — QoS de MQTT**
- *Hoy:* Node-RED se suscribe con QoS 2, pero el gateway publica con QoS 0 (el valor por defecto de `umqtt.simple`). El QoS real es el **menor** de los dos, es decir 0.
- *Opciones:* (a) publicar con `qos=1` desde el gateway; o (b) dejar QoS 0 y justificarlo, porque el ACK por LoRa ya confirma la entrega al broker.

### 5.3 Detalles menores
- [ ] `"LLENO _UMBRAL"` tiene un espacio. Si se corrige, actualizar al mismo tiempo los filtros y mapeos de valores en Grafana y los datos en MySQL.
- [ ] Node-RED se conecta a MySQL por `192.168.0.108`. Como Mosquitto, Node-RED, MySQL y Grafana corren en la misma Raspberry Pi, usar `127.0.0.1` evita que falle al cambiar de red.
- [ ] En la documentación, llamar a la "MAC" *identificador único del RP2040 (`machine.unique_id`)*.
- [ ] Corregir la codificación del texto en la función `InsertarDB` de Node-RED (`funciï¿½n`).
- [ ] Confirmar los parámetros LoRa que usa `lora_lib` por defecto (SF, CR, potencia, sync word) para la tabla del documento.

---

## 6. Tablas actualizadas para el documento técnico (reemplazan las del Entregable 02)

### 6.1 Hardware (as-built)
| Componente | Referencia | Uso |
|---|---|---|
| Nodo de sensado | Raspberry Pi Pico (RP2040) | Lee el sensor, clasifica el nivel, controla el semáforo, cifra y transmite por LoRa |
| Sensor de nivel | AJ-SR04M ultrasónico impermeable (UART, modo 4, comando 0x01) | Distancia a la superficie de los residuos |
| Actuador | Semáforo de 3 LEDs (verde, amarillo, rojo) en la carcasa Uqui | Indica el estado en el punto ecológico |
| Radio | 2 × SX1278 Ra-02 (433 MHz) | Enlace LoRa entre el nodo y el gateway |
| Gateway | ESP32 + SX1278 | Recibe por LoRa, descifra, publica por Wi-Fi/MQTT y responde ACK/NACK |
| Servidor | Raspberry Pi 4 | Mosquitto, Node-RED, MySQL/MariaDB y Grafana |
| Carcasa | Impresión 3D (mascota "Uqui") | Protege la electrónica y aloja el semáforo |

### 6.2 Asignación de pines
| Señal | Nodo (RP2040) | Gateway (ESP32) |
|---|---|---|
| LED verde / amarillo / rojo | GP2 / GP3 / GP6 | — |
| UART sensor: TX → RX del sensor / RX ← TX del sensor | GP4 / GP5 (UART1, 9600 bps) | — |
| SPI SX1278: SCK / MOSI / MISO | GP18 / GP19 / GP16 (SPI0) | GPIO14 / GPIO13 / GPIO12 (SPI2) |
| NSS (CS) | GP17 | GPIO7 |
| RESET | GP15 | GPIO6 |
| DIO0 (interrupción) | GP14 | GPIO5 |

### 6.3 Enlace LoRa
| Parámetro | Valor |
|---|---|
| Frecuencia | 433 MHz |
| Ancho de banda | **125 kHz** (el E02 decía 250 kHz) |
| SF, CR, potencia, sync word | Valores por defecto de `lora_lib` (confirmar, ver §5.3) |
| Trama | JSON → relleno PKCS7 → AES-128 → Base64 (152–172 caracteres) |
| Confirmación | ACK si el dato llegó al broker / NACK si falla el descifrado o la publicación |

### 6.4 MQTT y plataforma
| Elemento | Configuración |
|---|---|
| Broker | Eclipse Mosquitto en la Raspberry Pi 4, puerto 1883 |
| Tópico | `iot` |
| Publicador | Gateway ESP32 (`umqtt.simple`, QoS 0) |
| Payload | `{"msg_id", "estado", "distancia_cm", "nodo_Id", "mac"}` |
| Procesamiento | Node-RED: valida el identificador del nodo e inserta con SQL parametrizado |
| Almacenamiento | MySQL/MariaDB, base `iot`, tabla `valores` (`fecha = NOW()`, zona −05:00) |
| Visualización | Grafana, selector de nodo, refresco cada 5 s |

### 6.5 Cambio de alcance (registrar en el documento técnico)
| Antes (E01/E02) | Ahora | Justificación sugerida |
|---|---|---|
| 2 nodos: interior Wi-Fi (ESP32-S3) + exterior LoRa (RP2040) | 1 nodo LoRa (RP2040) + gateway ESP32 | Concentrar el piloto en la arquitectura más exigente (LoRa + gateway); la red sigue usando Wi-Fi y LoRa |
| Broker y suscriptor en un PC | Raspberry Pi 4 con toda la plataforma | Cumple la capa de procesamiento del enunciado |
| Sensor IR secundario | No implementado | ⚠️ Ver requisito "dos sensores" |
