from machine import Pin
from time import ticks_ms, ticks_diff, sleep_ms

# Boton con pull-up interno: libre = 1, presionado = 0
button = Pin(16, Pin.IN, Pin.PULL_UP)

contador = 0
ultimo = 0

def boton_irq(pin):
    global contador, ultimo
    ahora = ticks_ms()
    # debounce: ignora el evento si paso muy poco tiempo desde el ultimo click valido
    if ticks_diff(ahora, ultimo) > 80:
        contador += 1
        ultimo = ahora

# Se dispara solo cuando el pin pasa de 1 a 0 (flanco de bajada = boton presionado)
button.irq(trigger=Pin.IRQ_FALLING, handler=boton_irq)

while True:
    print("clics:", contador)
    sleep_ms(500)
