# Sesión 04 - Interrupciones y Temporizadores

## 1. Objetivo

Pasar de estar preguntando todo el tiempo si algo paso (sondeo o *polling*) a que el microcontrolador nos avise solo cuando en verdad ocurre un evento, usando una interrupción (IRQ) en el botón. Además, generar una señal de tiempo sin bloquear el programa principal, usando un temporizador no bloqueante (`Timer` en modo `ONE_SHOT`).

Ambos conceptos se aplican en un juego de tiempo de reacción: se enciende un LED en un instante aleatorio y se mide cuánto tarda el usuario en presionar el botón, detectando también salidas falsas (presionar antes de tiempo).

## 2. Circuito

| Componente | Pin GPIO |
|---|---|
| Botón (pull-up interno) | GP16 |
| LED de señal (verde) | GP15 |
| LED de espera (rojo) | GP14 |

El botón va a GND por un lado y a GP16 por el otro, sin resistencia externa, porque se usa el pull-up interno del microcontrolador. Cada LED lleva su resistencia de 330 ohm en serie hacia GND.

## 3. Qué es una interrupción

Antes hacíamos *polling*: en el loop principal preguntábamos todo el tiempo "¿ya se presionó el botón?, ¿ya se presionó el botón?". Eso funciona, pero desperdicia tiempo del procesador y puede hacer que se nos pase el evento si estamos ocupados haciendo otra cosa en ese momento.

Una interrupción (IRQ) es diferente: le decimos al microcontrolador "avísame tú cuando pase esto" y seguimos con lo nuestro. En este caso usamos `IRQ_FALLING`, que se dispara justo en el flanco de bajada del botón (cuando pasa de 1 a 0, o sea, cuando se presiona porque tenemos pull-up).

La regla de oro de las interrupciones es que el código dentro del handler (la ISR) debe ser lo más rápido posible: solo levantar banderas o guardar timestamps, nunca imprimir con `print()` ni usar `sleep_ms()` ahí dentro, porque eso bloquearía el sistema de interrupciones.

También usamos debounce por software: con `ticks_diff()` comparamos el tiempo actual contra el último click válido, y si pasaron menos de 80 ms lo ignoramos. Esto es porque un botón mecánico "rebota" físicamente y puede generar varias interrupciones falsas por un solo click real.

## 4. Qué es un temporizador

Un temporizador (`Timer(-1)` en modo `ONE_SHOT`) programa algo para que pase en el futuro, por ejemplo encender un LED en X segundos, pero sin detener el resto del programa. Esto es muy distinto a `sleep_ms()`, que sí bloquea todo mientras espera.

En el juego de reflejos, el timer es el que decide cuándo aparece la señal: se programa con un delay aleatorio y cuando se cumple, dispara el callback que enciende el LED verde. Si el usuario presiona el botón antes de tiempo (salida falsa), cancelamos el timer con `timer.deinit()` para que no dispare después sin sentido.

## 5. Resultados en ms



================================
Round 3
Espera la senal visual. No presiones antes.
Delay aleatorio: 1487 ms
================================
Reaccion: 542 ms

================================
Round 4
Espera la senal visual. No presiones antes.
Delay aleatorio: 7350 ms
================================
Reaccion: 335 ms

================================
Round 5
Espera la senal visual. No presiones antes.
Delay aleatorio: 6646 ms
================================
Reaccion: 274 ms

================================
Round 6
Espera la senal visual. No presiones antes.
Delay aleatorio: 7856 ms
================================
Reaccion: 249 ms

================================
Round 7
Espera la senal visual. No presiones antes.
Delay aleatorio: 4218 ms
================================
Reaccion: 290 ms

================================
Round 8
Espera la senal visual. No presiones antes.
Delay aleatorio: 9670 ms
================================
Reaccion: 279 ms

================================
Round 9
Espera la senal visual. No presiones antes.
Delay aleatorio: 6678 ms
================================
---- Closed serial port COM3 due to disconnection from the machine ----

## 6. Problemas encontrados

Ahora si no hubo ningun problema para armar el circuito ni en la parte del codigo, todo quedo muy claro y el circuito estaba muy sencillo, no tenia un alto grado de dificultad. 

## 7. Conclusión

En la sesion se pudo entender la importancia de una interrupcion y el uso de un temporizador al momento de ocupar la rasp o un sistema embebido, ahora puedes permitirle al microcontrolador que puede hacer varias cosas diferentes sin tener que estar revisando a cada rato si algo habia pasado. Con este juego de reflejos se pudo notar el cambio porque se combinan las 2 ideas, lo del IRQ y el Timer en el led, si algo estaba mal se notaba mucho, tambien que el ISR bien diseñado solo hace lo minimo.
