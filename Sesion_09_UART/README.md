# Sesión 09 - Comunicación UART

**Materia:** Laboratorio de Elementos Programables
**Sesión:** 09 - UART Command Center (terminal por USB + loopback UART0 GP0 → GP1)

_Trabajo individual: Axel García Arellano · 201251_

## Objetivo

Controlar dos LEDs de la Pico con comandos de texto enviados desde la computadora. Cada comando tiene que pasar por el UART hardware de la Pico antes de ejecutarse, y la Pico siempre contesta con `ACK`, `STATUS` o `ERR`.

| Archivo | Qué hace |
|---|---|
| [`main.py`](./main.py) | UART Command Center: transporte UART0 + parser de tramas + LEDs |
| [`tabla_pruebas.csv`](./tabla_pruebas.csv) | Plan de pruebas PASS / FAIL |
| [`evidencia/`](./evidencia) | Videos de las pruebas (terminal + Pico con el jumper) |

## 1. Qué es UART

UART (Universal Asynchronous Receiver/Transmitter) es comunicación **serial**, **asíncrona** y **full duplex**:

- **Serial:** los bits viajan uno detrás de otro por un solo cable.
- **Asíncrona:** no hay cable de reloj. Los dos extremos acuerdan antes la velocidad (baud rate) y cada uno mide el tiempo de los bits por su cuenta.
- **Full duplex:** una línea para transmitir (TX) y otra para recibir (RX), así que se puede mandar y recibir al mismo tiempo.

UART solo mueve bytes. Que `SET,LED1,1` signifique "prende el LED1" lo define el protocolo que programé en `main.py`.

## 2. TX y RX

El TX de un equipo va al RX del otro, y los dos comparten GND:

```
Equipo A        Equipo B
  TX  ────────►  RX
  RX  ◄────────  TX
  GND ─────────  GND
```

Conectar TX con TX no sirve: serían dos salidas empujando la misma línea y ninguna entrada escuchando.

En esta práctica la Pico habla consigo misma. Un jumper une **GP0 (TX de UART0)** con **GP1 (RX de UART0)**, así que lo que sale por TX vuelve a entrar por RX. Como es la misma placa, el GND ya es común.

## 3. Baud rate y 8N1

```python
uart = UART(0, baudrate=9600, bits=8, parity=None, stop=1,
            tx=Pin(0), rx=Pin(1))
```

- **9600 bps:** 9600 bits por segundo, cada bit dura ≈ 104 µs.
- **8N1:** 1 bit de inicio + **8** bits de datos + **N**inguna paridad + **1** bit de parada = 10 bits por carácter.
- Por lo tanto 9600 / 10 ≈ **960 caracteres por segundo**. Una trama como `SET,LED1,1\n` (11 bytes) tarda ≈ 11.5 ms en cruzar el jumper, muy por debajo del timeout de 1000 ms.

Si un extremo transmite a 9600 y el otro lee a 115200, el receptor muestrea los bits en momentos equivocados y aparecen caracteres basura o se pierden datos. En el loopback esto no pasa porque TX y RX son el mismo periférico con la misma configuración.

## 4. USB/REPL ≠ UART

| | USB / REPL | UART0 |
|---|---|---|
| Camino físico | Cable USB (puerto micro-USB de la Pico) | Pines GP0 (TX) y GP1 (RX) |
| En el código | `print()` y `input()` | `uart.write()`, `uart.any()`, `uart.read()` |
| ¿Lo muestra la terminal? | Sí | **No**, sale por un pin |
| Uso en la práctica | Consola del operador | Transporte del comando |

La terminal de MicroPico (o Thonny) solo ve lo que viaja por USB. Lo que se manda con `uart.write()` sale por el pin GP0 y la terminal no lo muestra, aunque el UART esté funcionando bien. Por eso se usa el jumper: el comando sale por GP0, vuelve por GP1 y el programa lo imprime con `print("UART RX :", ...)`. Así la terminal muestra lo que **realmente cruzó** el UART.

## 5. Por qué el loopback GP0 → GP1

Sin un adaptador USB–UART no hay otro equipo conectado a GP0/GP1. El loopback permite comprobar el UART real con un solo cable:

```
input() ─USB─► programa ─uart.write()─► GP0 TX ─jumper─► GP1 RX ─► receive_complete_line() ─► parser ─► LEDs
                                                                                                  │
terminal ◄─────────────────────────── print("RESP :", ...) ◄──────────────────────────────────────┘
```

El parser no usa el texto que escribí en la terminal, sino lo que llegó por RX. Si quito el jumper, `receive_complete_line()` no recibe nada en 1 s, regresa `None` y el comando **no se ejecuta**:

```
CMD> SET,LED1,1
USB CMD : SET,LED1,1
UART RX : SIN DATOS. Revisa el jumper GP0->GP1
RESP    : ERR,NO_UART_DATA
```

### Recepción por línea completa

`receive_complete_line()` (la misma del starter v3) lee **byte por byte** y solo regresa la trama cuando llega `\n`. Con `uart.any()` + `uart.readline()` directo, `any()` se activa en cuanto llega el primer byte y `readline()` podía regresar una trama a medias (`STATUS` → `STATU`). Antes de cada envío `clear_rx()` vacía el buffer para que no se mezclen restos de la prueba anterior.

Agregué un `try/except UnicodeError` en el `decode()`: si llegan bytes corruptos (por ejemplo con un baud rate distinto), la trama se trata como texto vacío y termina en `ERR,UNKNOWN_FRAME` en lugar de tumbar el programa.

## 6. Formato de trama

```
CMD , DEVICE , VALUE \n
SET , LED1   , 1
```

| Trama | Qué hace | Respuesta |
|---|---|---|
| `PING` | Prueba de vida del protocolo | `ACK,PONG` |
| `GET,STATUS` | Lee el estado de los dos LEDs | `STATUS,LED1,<0/1>,LED2,<0/1>` |
| `SET,<LED1\|LED2\|ALL>,<0\|1>` | Apaga o prende uno o los dos LEDs | `ACK,<DEVICE>,<VALUE>` |
| `TOGGLE,<LED1\|LED2\|ALL>` *(bonus)* | Invierte el estado | `ACK,LED1,<nuevo>` o `ACK,TOGGLE,LED1,x,LED2,y` |
| `BLINK,<LED1\|LED2>,<ms>` *(bonus)* | Parpadeo con periodo de 50–5000 ms; `0` lo detiene | `ACK,LED2,BLINK,500` / `ACK,LED2,BLINK_OFF` |
| `HELP` *(bonus)* | Lista de comandos | `ACK,HELP,...` |

Antes de interpretar, el parser pasa todo a mayúsculas, separa con `split(",")` y quita espacios de cada campo, así que `set, led2 , 0` también funciona.

El `BLINK` usa un `machine.Timer` por LED. El programa pasa casi todo el tiempo detenido en `input()` esperando el siguiente comando, así que un parpadeo hecho en el loop se congelaría. El timer cambia el LED por interrupción y sigue parpadeando mientras escribo. Un `SET` o `TOGGLE` sobre ese LED detiene el parpadeo.

## 7. ACK / ERR / STATUS

- **ACK:** la trama era válida y se ejecutó. Incluye lo que se hizo (`ACK,LED1,1`) para confirmar que se entendió bien.
- **STATUS:** respuesta a una consulta. Reporta los dos LEDs en una sola trama.
- **ERR:** la trama no se ejecutó. El motivo dice qué falló:

| Error | Cuándo | Ejemplo |
|---|---|---|
| `ERR,BAD_FIELDS` | Número de campos incorrecto | `SET,LED1`, `PING,1` |
| `ERR,BAD_DEVICE` | Dispositivo que no existe | `SET,LED3,1`, `BLINK,ALL,500` |
| `ERR,BAD_VALUE` | Valor que no es `0`/`1` (o no es número en BLINK) | `SET,LED1,9` |
| `ERR,BAD_PERIOD` | Periodo de BLINK fuera de 50–5000 ms | `BLINK,LED2,10` |
| `ERR,BAD_GET_FRAME` | `GET` de algo distinto a `STATUS` | `GET,FOO` |
| `ERR,UNKNOWN_FRAME` | Comando que no existe / texto libre | `hola mundo` |
| `ERR,NO_UART_DATA` | No llegó nada por RX (sin jumper) | cualquier comando |

El programa siempre responde: toda trama termina en un `ACK`, `STATUS` o `ERR`.

## 8. Conexiones

| Componente | Pin de la Pico | Pata física | Función |
|---|---|---|---|
| Jumper | **GP0 (UART0 TX) → GP1 (UART0 RX)** | 1 → 2 | Loopback UART |
| LED1 + resistencia 220–330 Ω a GND | GP13 | 17 | LED1 |
| LED2 + resistencia 220–330 Ω a GND | GP14 | 19 | LED2 |
| Cátodos de los LEDs | GND | 18 (o cualquier GND) | Referencia |

## 9. Resultados de la tabla de pruebas

Probado en la Pico 2 W física (MicroPython v1.29.0) desde VS Code con MicroPico, con el jumper GP0 → GP1 puesto. La tabla completa está en [`tabla_pruebas.csv`](./tabla_pruebas.csv).

☑ = probado y observado.

En todas las pruebas `UART RX` coincidió exactamente con `USB CMD`, es decir, cada trama cruzó completa el UART antes de procesarse.

**Pruebas obligatorias**

| # | Comando enviado | Esperado | Obtenido | Resultado |
|---|---|---|---|---|
| 1 | `ping` | `ACK,PONG` | `ACK,PONG` | ☑ PASS |
| 2 | `set,led1,1` | `ACK,LED1,1` | `ACK,LED1,1` | ☑ PASS |
| 3 | `SET,LED1,0` | `ACK,LED1,0` | `ACK,LED1,0` | ☑ PASS |
| 4 | `set,led2,1` | `ACK,LED2,1` | `ACK,LED2,1` | ☑ PASS |
| 5 | `set,all,1` | `ACK,ALL,1` | `ACK,ALL,1` | ☑ PASS |
| 6 | `get,status` | `STATUS,LED1,1,LED2,1` | `STATUS,LED1,1,LED2,1` | ☑ PASS |
| 7 | `set,led3,1` | `ERR,BAD_DEVICE` | `ERR,BAD_DEVICE` | ☑ PASS |
| 8 | `set,led2,9` | `ERR,BAD_VALUE` | `ERR,BAD_VALUE` | ☑ PASS |
| 9 | `hola mundo` | `ERR,UNKNOWN_FRAME` | `ERR,UNKNOWN_FRAME` | ☑ PASS |

**Pruebas extra (validaciones y bonus)**

| # | Comando enviado | Esperado | Obtenido | Resultado |
|---|---|---|---|---|
| 10 | `help` | `ACK,HELP,...` | `ACK,HELP,PING\|GET,STATUS\|SET,...` | ☑ PASS |
| 11 | `set,all,0` | `ACK,ALL,0` | `ACK,ALL,0` | ☑ PASS |
| 12 | `get, status` (con espacio) | `STATUS,LED1,0,LED2,0` | `STATUS,LED1,0,LED2,0` | ☑ PASS |
| 13 | `blink` | `ERR,BAD_FIELDS` | `ERR,BAD_FIELDS` | ☑ PASS |
| 14 | `blink,led1` | `ERR,BAD_FIELDS` | `ERR,BAD_FIELDS` | ☑ PASS |
| 15 | `blink,led1,ms` | `ERR,BAD_VALUE` | `ERR,BAD_VALUE` | ☑ PASS |
| 16 | `blink,led1,8` | `ERR,BAD_PERIOD` | `ERR,BAD_PERIOD` | ☑ PASS |
| 17 | `blink,led1,8ms` | `ERR,BAD_VALUE` | `ERR,BAD_VALUE` | ☑ PASS |
| 18 | `blink,led2,500` | `ACK,LED2,BLINK,500` | `ACK,LED2,BLINK,500` | ☑ PASS |
| 19 | `blink,led1,500` | `ACK,LED1,BLINK,500` | `ACK,LED1,BLINK,500` | ☑ PASS |

Observaciones:

- Todos los comandos se escribieron en minúsculas y el parser los aceptó, porque convierte la trama con `upper()` antes de compararla. Las respuestas salen en mayúsculas (`ACK,LED2,1`).
- La prueba 12 (`get, status`) muestra que también se quitan los espacios alrededor de cada campo.
- La prueba 11 dejó los dos LEDs apagados, y la 12 lo confirma con `STATUS,LED1,0,LED2,0`.
- La prueba 3 se hizo en la Pico pero no quedó en el extracto de la terminal que se muestra abajo.
- En las pruebas 13 a 17 cada error sale con un motivo distinto: faltan campos (`BAD_FIELDS`), el periodo no es un número (`BAD_VALUE`) o está fuera de 50–5000 ms (`BAD_PERIOD`).
- En las pruebas 18 y 19 cada LED tiene su propio `Timer`, así que los dos pueden parpadear a la vez mientras la terminal sigue esperando el siguiente comando en `input()`.

Registro de la terminal (extracto):

```
CMD> set,all,1
USB CMD : set,all,1
UART RX : set,all,1
RESP    : ACK,ALL,1
CMD> get,status
USB CMD : get,status
UART RX : get,status
RESP    : STATUS,LED1,1,LED2,1
CMD> set,led3,1
USB CMD : set,led3,1
UART RX : set,led3,1
RESP    : ERR,BAD_DEVICE
CMD> set,led2,9
USB CMD : set,led2,9
UART RX : set,led2,9
RESP    : ERR,BAD_VALUE
CMD> hola mundo
USB CMD : hola mundo
UART RX : hola mundo
RESP    : ERR,UNKNOWN_FRAME
```

Evidencia:

Los dos videos muestran al mismo tiempo la terminal de MicroPico y la Pico en la protoboard, con el jumper GP0 → GP1 y los dos LEDs.

| Video | Duración | Qué muestra |
|---|---|---|
| [`video_pruebas_comandos.mp4`](evidencia/video_pruebas_comandos.mp4) | 2:15 | Pruebas 1–12: `help`, `ping`, `set` de cada LED y de `all`, `get,status` y los errores `BAD_DEVICE`, `BAD_VALUE` y `UNKNOWN_FRAME`. Los LEDs cambian con cada comando |
| [`video_pruebas_blink.mp4`](evidencia/video_pruebas_blink.mp4) | 0:23 | Pruebas 13–19: errores de `blink` (`BAD_FIELDS`, `BAD_VALUE`, `BAD_PERIOD`) y `blink,led2,500` / `blink,led1,500` con los LEDs parpadeando |

## 10. Exit ticket

1. **¿Por qué TX se conecta a RX?** Porque TX es la salida que transmite y RX la entrada que escucha. Una salida tiene que llegar a una entrada; TX con TX serían dos salidas sin nadie que reciba.
2. **¿Qué ocurre si los baud rates no coinciden?** El receptor mide los bits con otra duración, los límites de cada bit no coinciden y llegan caracteres corruptos o se pierden datos.
3. **¿Qué función convierte bytes en texto?** `decode()` (`b"PING"` → `"PING"`). Después `strip()` quita el `\r\n`.
4. **¿Qué ventaja tiene `SET,LED1,1` sobre una frase libre?** Tiene campos fijos y un separador conocido: el parser sabe cuántos campos esperar y puede validar cada uno por separado (acción, dispositivo, valor) y decir exactamente qué estuvo mal. Además se amplía agregando dispositivos o comandos sin cambiar el formato.
5. **¿Cuál es la diferencia entre ACK y ERR?** ACK confirma que la trama era válida y ya se ejecutó; ERR avisa que no se ejecutó y por qué. Con eso el sistema que manda el comando sabe si tiene que reintentar o corregir.

## Estructura de la carpeta

```text
Sesion_09_UART/
├── README.md
├── main.py                   # UART Command Center (Niveles 1, 2 y bonus)
├── tabla_pruebas.csv         # plan de pruebas PASS / FAIL
└── evidencia/
    ├── video_pruebas_comandos.mp4   # terminal + Pico: pruebas 1-12 (PING, SET, STATUS, ERR)
    └── video_pruebas_blink.mp4      # terminal + Pico: pruebas 13-19 (BLINK)
```

También se incluyen `.micropico` y `.vscode/`, la configuración de la extensión MicroPico, igual que en las sesiones anteriores.

## Cómo ejecutar

### VS Code + MicroPico (lo que usé)

1. Armar el circuito de la sección 8, con el jumper GP0 → GP1.
2. Conectar la Pico por USB (con MicroPython) y abrir **esta carpeta** en VS Code.
3. Esperar a que la barra inferior indique que la placa está conectada (o `MicroPico: Connect`).
4. Abrir `main.py` y presionar **Run**. En la terminal de MicroPico aparece `CMD>`: dar clic en la terminal y escribir los comandos.
5. Para detenerlo, **Stop** (o Ctrl-C). El programa apaga los LEDs y detiene los timers de BLINK.

### Thonny

1. `Herramientas → Opciones → Intérprete → MicroPython (Raspberry Pi Pico)` y elegir el puerto (`/dev/ttyACM0`).
2. Abrir `main.py` y presionar **Run (F5)**. Escribir los comandos en el Shell, después del `CMD>`.
3. Stop / Ctrl-C para detener.
