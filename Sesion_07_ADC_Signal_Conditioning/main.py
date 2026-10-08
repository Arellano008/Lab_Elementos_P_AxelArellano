# =========================================================================
#  DO 03 / CHALLENGE 07 - Smart Analog Monitor
#  Sesion 07: Conversion ADC y acondicionamiento de senal
#  Axel Garcia Arellano
#
#  Cadena de acondicionamiento:
#  raw (ADC) -> promedio movil -> voltaje / porcentaje -> estado -> LED
#  La senal FILTRADA decide el estado, nunca una lectura aislada.
#  Circuito: potenciometro en GP26/ADC0, LEDs en GP13/GP14/GP15.
# =========================================================================

from machine import Pin, ADC
from time import sleep_ms

# ---------------- Hardware ----------------
sensor = ADC(Pin(26))                  # GP26 = ADC0 (0 a 3.3 V maximo)
green = Pin(13, Pin.OUT, value=0)      # GP13 - LED verde    -> NORMAL
yellow = Pin(14, Pin.OUT, value=0)     # GP14 - LED amarillo -> WARNING
red = Pin(15, Pin.OUT, value=0)        # GP15 - LED rojo     -> ALARM

# ---------------- Parametros ----------------
VREF = 3.3              # voltaje de referencia del ADC de la Pico
ADC_MAX = 65535         # read_u16() siempre entrega de 0 a 65535
WARNING = 50            # % a partir del cual se enciende el amarillo
ALARM = 75              # % a partir del cual se enciende el rojo
N = 10                  # muestras del promedio movil
SAMPLE_MS = 100         # periodo de muestreo -> la ventana cubre 1 s

window = []             # aqui se guardan las ultimas N lecturas crudas


# ---------------- Lectura y conversion ----------------
# Lee el ADC: un numero entero de 0 (0 V) a 65535 (3.3 V)
def read_raw():
    return sensor.read_u16()


# Regla de tres: 0 -> 0.0 V y 65535 -> 3.3 V
# max()/min() aseguran que el valor nunca salga del rango valido
def to_voltage(raw):
    raw = max(0, min(ADC_MAX, raw))
    return raw * VREF / ADC_MAX


# Regla de tres: 0 -> 0 % y 65535 -> 100 %
def to_percent(raw):
    raw = max(0, min(ADC_MAX, raw))
    return raw * 100 / ADC_MAX


# ---------------- Filtro ----------------
# Promedio movil: entra la lectura nueva, sale la mas vieja cuando ya
# hay N, y se regresa el promedio. Una lectura con ruido solo pesa 1/N.
def filter_avg(raw):
    window.append(raw)
    if len(window) > N:
        window.pop(0)
    return sum(window) / len(window)


# ---------------- Clasificacion ----------------
# Convierte el porcentaje FILTRADO en un estado:
#   menos de 50 %  -> NORMAL
#   50 % a 74.9 %  -> WARNING
#   75 % o mas     -> ALARM
def classify(percent):
    if percent >= ALARM:
        return "ALARM"
    elif percent >= WARNING:
        return "WARNING"
    else:
        return "NORMAL"


# ---------------- Salidas ----------------
# Solo un LED encendido a la vez: cada LED se compara con el estado,
# la comparacion da True (1) en uno solo y False (0) en los otros dos
def update_outputs(state):
    green.value(state == "NORMAL")
    yellow.value(state == "WARNING")
    red.value(state == "ALARM")


# Todo en una linea: lectura cruda, voltaje filtrado, % crudo, % filtrado y estado
def print_status(raw, voltage, raw_percent, filt_percent, state):
    print("raw:", raw,
          "| V:", "{:.2f}".format(voltage),
          "| % crudo:", "{:.1f}".format(raw_percent),
          "| % filtrado:", "{:.1f}".format(filt_percent),
          "| estado:", state)


# ---------------- Inicio ----------------
print("CHALLENGE 07 - Smart Analog Monitor")
print("Entrada: GP26/ADC0 | LEDs: GP13=verde, GP14=amarillo, GP15=rojo")
print("Umbrales: WARNING >=", WARNING, "% | ALARM >=", ALARM, "%")
print("Filtro: promedio movil de", N, "muestras cada", SAMPLE_MS, "ms")
print(20 * "=")

estado_anterior = "INICIO"

try:
    while True:
        raw = read_raw()                         # 1) medir
        filtered = filter_avg(raw)               # 2) filtrar
        voltage = to_voltage(filtered)           # 3) convertir (senal filtrada)
        raw_percent = to_percent(raw)
        # Se redondea a 1 decimal para decidir con el mismo numero que se imprime
        # (sin esto, raw = 32767 da 49.9992 %: se veia "50.0" pero salia NORMAL)
        filt_percent = round(to_percent(filtered), 1)
        state = classify(filt_percent)           # 4) clasificar
        update_outputs(state)                    # 5) actuar

        # Aviso visible en el serial cada vez que cambia el estado
        if state != estado_anterior:
            print("[CAMBIO]", estado_anterior, "->", state)
            estado_anterior = state

        print_status(raw, voltage, raw_percent, filt_percent, state)
        sleep_ms(SAMPLE_MS)
finally:
    # Al detener con Ctrl-C (o si hay un error) se apagan los LEDs
    green.value(0)
    yellow.value(0)
    red.value(0)
    print("\n[FIN] Monitor detenido, LEDs apagados")
