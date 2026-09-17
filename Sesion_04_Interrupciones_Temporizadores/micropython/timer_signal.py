from machine import Pin, Timer
from time import sleep_ms

led_signal = Pin(15, Pin.OUT)  # se enciende cuando el timer dispara
led_wait   = Pin(14, Pin.OUT)  # encendido mientras esperamos

timer = Timer(-1)
timer_disparado = False


def timer_callback(t):
    global timer_disparado
    timer_disparado = True


# Estado inicial: esperando
led_signal.off()
led_wait.on()
print("PRUEBA TIMER")
print("Senal = OFF")
print("Espera = ON")
print("Esperando 3 segundos...")

# Temporizador de UNA sola vez (ONE_SHOT): dispara una vez a los 3000 ms y ya
timer.init(mode=Timer.ONE_SHOT, period=3000, callback=timer_callback)

contador = 0

while True:
    print("MAIN trabajando:", contador)
    contador += 1

    if timer_disparado:
        timer_disparado = False
        led_signal.on()
        led_wait.off()
        print("TIMER DISPARADO")
        print("Senal = ON")

    sleep_ms(500)
