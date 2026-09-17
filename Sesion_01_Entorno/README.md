# Sesión 01 - Entorno y Arquitectura

## 1. Objetivo

Armar el primer circuito en Wokwi y lograr un "Hola Mundo Dual": el mismo LED parpadeando, programado una vez en MicroPython y otra vez en C/C++, para comparar ambos flujos de trabajo desde el principio del curso.

## 2. Entorno de trabajo

Lo que instalé para poder trabajar en el curso:

- VS Code
- Git
- Python 3
- Extensión oficial "Raspberry Pi Pico" de VS Code (trae Pico SDK, CMake y compiladores de forma automática)
- Thonny o MicroPico para programar en MicroPython
- Firmware UF2 de MicroPython para la Pico 2 W
- Cable USB de datos (no solo de carga)
- Cuenta en Wokwi para simular el circuito

## 3. Circuito

LED en GP15 con su resistencia de 330 ohm en serie hacia GND. Se usa el mismo pin y la misma lógica que en las sesiones siguientes, para mantener consistencia de pines en todo el repositorio.

## 4. Código

En MicroPython el enfoque es más directo: uso `Pin.toggle()` dentro de un loop con `sleep()`, y el intérprete va traduciendo cada línea en tiempo real mientras corre en la Pico. Es rápido de probar y modificar, ideal para prototipar.

En C/C++ el enfoque es distinto: controlo el pin manualmente con `gpio_put()` poniéndolo en alto o en bajo, con `sleep_ms()` entre cada cambio. Aquí el código se compila primero a un binario (usando el Pico SDK) y ese binario es el que se sube y corre en la Pico, ya no hay un intérprete traduciendo en tiempo real.

## 5. Evidencia

<!-- Agregar aqui: captura de la simulacion en Wokwi (o enlace publico al proyecto) -->

<!-- Agregar aqui: foto o video del LED parpadeando en la Pico fisica -->

## 6. Infografía

La infografía de esta sesión está en [infographic/AxelArellano_S01_Infografia.svg](./infographic/AxelArellano_S01_Infografia.svg) (pendiente de exportar a PNG, ver nota en la carpeta `infographic/`).

## 7. Problemas encontrados

<!-- Describir aqui cualquier problema real encontrado -->

## 8. Conclusión

<!-- Reflexion personal breve: que se aprendio al comparar MicroPython vs C/C++ desde el primer circuito -->
