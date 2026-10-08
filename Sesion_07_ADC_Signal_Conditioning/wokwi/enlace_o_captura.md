# Simulación en Wokwi

Trabajo individual: Axel García Arellano (#201251).

## Enlace público del proyecto y el de la Fotoresistencia

https://wokwi.com/projects/476816920783892481

https://wokwi.com/projects/477353681322258433

## Cómo recrear la simulación

1. En [wokwi.com](https://wokwi.com) crea un proyecto nuevo **Raspberry Pi Pico → MicroPython** (Pico RP2040; Wokwi no simula bien la Pico 2 W).
2. En la pestaña `diagram.json` borra todo y pega el contenido de [`diagram.json`](./diagram.json): potenciómetro en GP26/3V3/GND y LEDs verde/amarillo/rojo con 220 Ω en GP13/GP14/GP15.
3. En la pestaña `main.py` pega el contenido de [`../main.py`](../main.py) y presiona ▶. Gira el potenciómetro (clic sobre él) y observa el serial y los LEDs.
