# Evidencia en Wokwi — Sesión 02

Simulaciones usadas para obtener la evidencia de memoria y direcciones, ya que aún no se cuenta con la placa física Pico 2 W.

## Proyecto C/C++ (Pico SDK)

🔗 https://wokwi.com/projects/473819554116900865

Placa simulada: Raspberry Pi Pico (RP2040). Código de mapa de memoria que imprime las direcciones de una variable `const`, una global, una local (stack) y un puntero de heap (`malloc`).

## Proyecto MicroPython

🔗 https://wokwi.com/projects/473819754517622785

Placa simulada: Raspberry Pi Pico W (RP2040). Script que mide memoria libre con `gc.mem_free()` antes y después de reservar un `bytearray(10000)`.

## Nota de alcance

Ambas simulaciones corren sobre el chip **RP2040**, no sobre el **RP2350** de la placa real (Pico 2 W). Esto permitió validar la lógica de ambos lenguajes, pero no el rendimiento, consumo ni comportamiento específico de los núcleos Hazard3/Cortex-M33. Validación en hardware físico pendiente.
