# Sesion 03 - GPIO, Pull-up/Pull-down y Semaforo Peatonal

## Objetivo

Implementar un sistema de entrada/salida completo (INPUT -> PROCESO -> OUTPUT) en la Raspberry Pi Pico 2 W: leer un boton con pull-up interno, resolver el rebote mecanico (debounce) por software, y usar esa entrada para disparar una secuencia de semaforo (autos + peaton) con una condicion de seguridad explicita. El mismo circuito se probo en MicroPython, en el simulador Wokwi y en C/C++ con el Pico SDK sobre hardware fisico.

## Circuito

| Senal          | Pin Pico  | Notas                                  |
|----------------|-----------|-----------------------------------------|
| Auto rojo      | GP15      | LED + resistencia 330 ohm a GND         |
| Auto amarillo  | GP14      | LED + resistencia 330 ohm a GND         |
| Auto verde     | GP13      | LED + resistencia 330 ohm a GND         |
| Peaton rojo    | GP12      | LED + resistencia 330 ohm a GND         |
| Peaton verde   | GP11      | LED + resistencia 330 ohm a GND         |
| Boton          | GP16      | Pull-up interno; boton -> GND           |

Cada LED va en serie con su resistencia de 330 ohm hacia GND. El boton solo necesita una pata a GP16 y la otra a GND (sin resistencia externa) porque se usa `gpio_pull_up()` / `Pin.PULL_UP` internamente.

Diagrama simulable: ver `wokwi/diagram.json`.

## Funcionamiento

El sistema tiene 4 estados:

- **S0 REPOSO:** autos en verde, peaton en rojo (estado por defecto).
- **S1 TRANSICION:** autos en amarillo, peaton sigue en rojo (1.5 s).
- **S2 CRUCE:** autos en rojo, peaton en verde (4 s).
- **S3 FIN:** autos en rojo, peaton verde parpadeando como aviso de que el cruce esta por terminar.
- Regresa a S0.

Al presionar el boton se dispara `crossing_sequence()`, que recorre S1 -> S2 -> S3 -> S0 automaticamente. El codigo esta organizado en funciones con significado (`cars_go()`, `cars_prepare_to_stop()`, `pedestrians_go()`) en vez de escribir 0/1 sueltos, para que sea mas legible y evitar activar una combinacion peligrosa por error.

**Invariante de seguridad:** auto verde y peaton verde nunca estan activos al mismo tiempo. Esto se garantiza centralizando todas las salidas en una sola funcion (`set_lights()`), en vez de prender/apagar pines sueltos en distintas partes del codigo.

## Pull-up / Pull-down

Se uso **pull-up interno** en GP16: sin nada conectado, un pin de entrada queda "flotante" (su valor no esta garantizado). Con pull-up, el pin queda en 1 logico por defecto; al conectar el boton a GND, presionarlo fuerza el pin a 0. Por eso en este circuito **libre = 1** y **presionado = 0**.

## Pruebas realizadas

- [ ] Lectura de boton en MicroPython (`01_button_read.py`): libre = 1, presionado = 0.
- [ ] Debounce en MicroPython (`02_button_debounce.py`): un solo "CLICK valido" por presion, incluso manteniendo el boton presionado varios segundos.
- [ ] Semaforo completo en MicroPython y en Wokwi (`03_semaforo_peatonal.py`): secuencia S0->S1->S2->S3->S0 correcta.
- [ ] Lectura de boton en C/C++ (`cpp/button_read/`): mismo comportamiento que en MicroPython.
- [ ] Semaforo completo en C/C++ sobre hardware fisico (`cpp/traffic_light/`): secuencia correcta, sin estados peligrosos, wait-for-release funcionando.

## Problemas encontrados

Al compilar el proyecto en C/C++ para la Pico 2 W (RP2350) con el toolchain `15_2_Rel1` que descarga la extension de VS Code por defecto, la configuracion de CMake fallaba con errores de enlazado (`dangerous relocation: unsupported relocation`, `Unknown destination type (ARM/Thumb)`) al compilar las rutinas internas de newlib (`_exit`, `_close`, `_read`, etc.). Es un bug conocido de esa version del toolchain (GCC 15.2 / binutils 2.44) con el multilib de Cortex-M33 que usa la Pico 2. Se resolvio cambiando `toolchainVersion` a `14_2_Rel1` en el `CMakeLists.txt` y descargando esa version desde "Switch SDK" en la extension.

En el apartado del circuito tuve el problema que no supe como conectar el boton, bueno estaba en una posicion donde no se podia leer la entrada y el ground pero en la clase pude solucionar ese tema preguntandole directamente al profe

## Conclusion
 
La practica me dejo claro lo que puede hacer un pin de entrar al momento de dejarse "flotando", dando a entender que en esta ocasion si lo dejabamos flotando: sin el pull-up interno, GP16 no tendria un valor confiable y cuando se activo fue lo que le dio un estado definido de 1, que cuando se presionaba daba 0. Tambien entendi porque el boton necesita el debounce: sin los 30 ms de espera y la confirmacion posterior, una presion podria tomarse como varios clicks, dando muchas secuencias repetidas mientras mantenia el boton presionado. Igual comparar entre micropython y C++ sobre el mismo circuito ayuda a separar 2 cosas que usualmente se mezclan.



