# =========================================================================
#  BONUS Sesion 07 - Smart Analog Monitor con fotorresistencia (LDR)
#  Axel Garcia Arellano
#
#  Mismo monitor que ../../main.py, pero el potenciometro se cambia por
#  el modulo LDR de Wokwi (wokwi-photoresistor-sensor). En Wokwi pegar
#  este archivo como main.py junto con diagram.json de esta carpeta.
#
#  Modulo LDR: la LDR va en serie con 10 kOhm y AO sale del punto medio.
#  Mas luz -> menos resistencia -> MENOS voltaje en AO.
#  Por eso el porcentaje del ADC funciona como "% de oscuridad":
#    poca oscuridad (mucha luz) -> NORMAL   (LED verde)
#    atardecer                  -> WARNING  (LED amarillo)
#    oscuro                     -> ALARM    (LED rojo)
#  Como una lampara automatica que avisa cuando ya hace falta encenderla.
# =========================================================================

from machine import Pin, ADC
from time import sleep_ms

# ---------------- Hardware ----------------
sensor = ADC(Pin(26))                  # GP26 = ADC0 <- AO del modulo LDR
green = Pin(13, Pin.OUT, value=0)      # GP13 - LED verde    -> NORMAL
yellow = Pin(14, Pin.OUT, value=0)     # GP14 - LED amarillo -> WARNING
red = Pin(15, Pin.OUT, value=0)        # GP15 - LED rojo     -> ALARM

# ---------------- Parametros ----------------
VREF = 3.3              # el modulo se alimenta con el 3V3 de la Pico
ADC_MAX = 65535         # read_u16() siempre entrega de 0 a 65535
WARNING = 50            # % de oscuridad -> aprox. 100 lux o menos
ALARM = 75              # % de oscuridad -> aprox. 21 lux o menos
N = 10                  # muestras del promedio movil
SAMPLE_MS = 100         # periodo de muestreo -> la ventana cubre 1 s

# Datos del modulo LDR de Wokwi (valores por defecto del componente)
R_FIJA = 10000          # resistencia fija del divisor (ohm)
RL10 = 50000            # resistencia de la LDR a 10 lux (ohm)
GAMMA = 0.7             # pendiente de la curva log(R) vs log(lux)

window = []             # aqui se guardan las ultimas N lecturas crudas


# ---------------- Lectura y conversion ----------------
def read_raw():
    return sensor.read_u16()


# Regla de tres: 0 -> 0.0 V y 65535 -> 3.3 V
def to_voltage(raw):
    raw = max(0, min(ADC_MAX, raw))
    return raw * VREF / ADC_MAX


# Regla de tres: 0 -> 0 % y 65535 -> 100 %
# Con la LDR este porcentaje es "% de oscuridad"
def to_percent(raw):
    raw = max(0, min(ADC_MAX, raw))
    return raw * 100 / ADC_MAX


# Estimacion de la luz en lux a partir del voltaje (solo para mostrar):
# 1) divisor de voltaje:  V = VREF * R_ldr / (R_ldr + R_FIJA)
#    despejando:          R_ldr = R_FIJA * V / (VREF - V)
# 2) curva de la LDR:     R_ldr = RL10 * (10 / lux) ** GAMMA
#    despejando:          lux = 10 * (RL10 / R_ldr) ** (1 / GAMMA)
def to_lux(voltage):
    if voltage <= 0.001:            # practicamente 0 V -> luz muy intensa
        return 100000
    if voltage >= VREF - 0.001:     # practicamente 3.3 V -> oscuridad total
        return 0
    r_ldr = R_FIJA * voltage / (VREF - voltage)
    return 10 * (RL10 / r_ldr) ** (1 / GAMMA)


# ---------------- Filtro ----------------
# Promedio movil: entra la lectura nueva, sale la mas vieja cuando ya
# hay N, y se regresa el promedio. Una lectura con ruido solo pesa 1/N.
def filter_avg(raw):
    window.append(raw)
    if len(window) > N:
        window.pop(0)
    return sum(window) / len(window)


# ---------------- Clasificacion ----------------
# Igual que en main.py, pero el porcentaje significa oscuridad:
#   menos de 50 %  -> NORMAL  (hay luz suficiente)
#   50 % a 74.9 %  -> WARNING (esta oscureciendo)
#   75 % o mas     -> ALARM   (esta oscuro)
def classify(percent):
    if percent >= ALARM:
        return "ALARM"
    elif percent >= WARNING:
        return "WARNING"
    else:
        return "NORMAL"


# ---------------- Salidas ----------------
# Solo un LED encendido a la vez
def update_outputs(state):
    green.value(state == "NORMAL")
    yellow.value(state == "WARNING")
    red.value(state == "ALARM")


# Todo en una linea: lectura cruda, voltaje y lux filtrados,
# % de oscuridad crudo y filtrado, y estado
def print_status(raw, voltage, lux, raw_percent, filt_percent, state):
    # Con poca luz se muestra 1 decimal para que 0.1 lux no salga como "0"
    lux_txt = "{:.1f}".format(lux) if lux < 10 else "{:.0f}".format(lux)
    print("raw:", raw,
          "| V:", "{:.2f}".format(voltage),
          "| luz: ~" + lux_txt + " lux",
          "| % osc. crudo:", "{:.1f}".format(raw_percent),
          "| % osc. filtrado:", "{:.1f}".format(filt_percent),
          "| estado:", state)


# ---------------- Inicio ----------------
print("BONUS 07 - Smart Analog Monitor con LDR")
print("Entrada: AO del modulo LDR -> GP26/ADC0 | LEDs: GP13, GP14, GP15")
print("Umbrales (% oscuridad): WARNING >=", WARNING, "% | ALARM >=", ALARM, "%")
print("Equivale a: NORMAL > ~100 lux | WARNING ~21-100 lux | ALARM < ~21 lux")
print("Mueve el control de 'lux' del sensor en Wokwi para cambiar la luz")
print(20 * "=")

estado_anterior = "INICIO"

try:
    while True:
        raw = read_raw()                         # 1) medir
        filtered = filter_avg(raw)               # 2) filtrar
        voltage = to_voltage(filtered)           # 3) convertir (senal filtrada)
        lux = to_lux(voltage)
        raw_percent = to_percent(raw)
        filt_percent = round(to_percent(filtered), 1)
        state = classify(filt_percent)           # 4) clasificar
        update_outputs(state)                    # 5) actuar

        if state != estado_anterior:
            print("[CAMBIO]", estado_anterior, "->", state)
            estado_anterior = state

        print_status(raw, voltage, lux, raw_percent, filt_percent, state)
        sleep_ms(SAMPLE_MS)
finally:
    # Al detener con Ctrl-C (o si hay un error) se apagan los LEDs
    green.value(0)
    yellow.value(0)
    red.value(0)
    print("\n[FIN] Monitor detenido, LEDs apagados")
