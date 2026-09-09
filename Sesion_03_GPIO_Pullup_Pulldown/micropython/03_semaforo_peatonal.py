from machine import Pin
from time import sleep_ms

# Pines (los mismos que en C/C++ y en el circuito fisico)
car_red    = Pin(15, Pin.OUT)
car_yellow = Pin(14, Pin.OUT)
car_green  = Pin(13, Pin.OUT)
ped_red    = Pin(12, Pin.OUT)
ped_green  = Pin(11, Pin.OUT)
button     = Pin(16, Pin.IN, Pin.PULL_UP)


def set_lights(car_r, car_y, car_g, ped_r, ped_g):
    car_red.value(car_r)
    car_yellow.value(car_y)
    car_green.value(car_g)
    ped_red.value(ped_r)
    ped_green.value(ped_g)


def cars_go():
    set_lights(0, 0, 1,   1, 0)


def cars_prepare_to_stop():
    set_lights(0, 1, 0,   1, 0)


def pedestrians_go():
    set_lights(1, 0, 0,   0, 1)


def crossing_sequence():
    print('S1 TRANSICION: autos amarillo, peaton rojo')
    cars_prepare_to_stop()
    sleep_ms(1500)

    print('S2 CRUCE: autos rojo, peaton verde')
    pedestrians_go()
    sleep_ms(4000)

    print('S3 FIN: peaton verde parpadea')
    for i in range(4):
        ped_green.toggle()
        sleep_ms(300)

    print('S0 REPOSO: autos verde, peaton rojo')
    cars_go()


cars_go()
print('Sistema listo. S0 REPOSO: autos verde / peaton rojo')
last = 1

while True:
    now = button.value()
    if last == 1 and now == 0:
        sleep_ms(30)  # debounce
        if button.value() == 0:
            print('CLICK valido: peaton solicito cruce')
            crossing_sequence()
            while button.value() == 0:  # wait for release
                sleep_ms(10)
    last = now
    sleep_ms(10)
