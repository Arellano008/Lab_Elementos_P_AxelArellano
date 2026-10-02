# Simulación en Wokwi

Trabajo en equipo: Angel Rugerio Jiménez (#201720) y Axel García Arellano (#201251).

## Enlace público del proyecto

PEGAR_ENLACE_AQUI

## Cómo recrear la simulación

1. En [wokwi.com](https://wokwi.com) crea un proyecto nuevo **Raspberry Pi Pico → MicroPython** (Pico RP2040; Wokwi no simula bien la Pico 2 W).
2. En la pestaña `diagram.json` borra todo y pega el contenido de [`diagram.json`](./diagram.json): potenciómetro en GP26/3V3/GND y LEDs verde/amarillo/rojo con 220 Ω en GP13/GP14/GP15.
3. En la pestaña `main.py` pega el contenido de [`../main.py`](../main.py) y presiona ▶. Gira el potenciómetro (clic sobre él) y observa el serial y los LEDs.

## Captura

![Alarma por umbrales](../evidence/threshold_alarm.png)
