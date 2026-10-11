# =========================================================================
#  CHALLENGE 08 - Multitarea cooperativa (version Wokwi)
#  Sesion 08: Procesamiento multihilo / dual-core
#  Axel Garcia Arellano
#
#  Un solo nucleo ejecuta 4 tareas periodicas sin bloquearse:
#    sensor  (20 ms)  : lee ADC, filtra, clasifica y cuenta muestras
#    boton   (50 ms)  : ACK de alarma o reset del contador
#    UI      (200 ms) : LEDs de estado y heartbeat
#    serial  (1000 ms): imprime el estado del sistema
#  Cada tarea revisa su "turno" con ticks_ms(); nunca hay sleep largo.
# =========================================================================

from machine import Pin, ADC
from time import ticks_ms, ticks_diff, ticks_add, sleep_ms

# ---------------- Pines ----------------
PIN_ADC = 26            # GP26 / ADC0 - potenciometro
PIN_LED_NORMAL = 13     # LED verde
PIN_LED_WARNING = 14    # LED amarillo
PIN_LED_ALARM = 15      # LED rojo
PIN_HEARTBEAT = 12      # LED azul
PIN_BUTTON = 16         # boton a GND (PULL_UP: libre = 1, presionado = 0)

# ---------------- Umbrales (% de la senal filtrada) ----------------
ADC_MAX = 65535         # read_u16() entrega de 0 a 65535
WARNING_PCT = 50        # 50 % a 74.9 % -> WARNING
ALARM_PCT = 75          # 75 % o mas    -> ALARM

# ---------------- Filtro ----------------
FILTER_SIZE = 8         # muestras del promedio movil (8 x 20 ms = 160 ms)

# ---------------- Periodos de las tareas (ms) ----------------
SENSOR_PERIOD_MS = 20   # 50 Hz
BUTTON_PERIOD_MS = 50   # 20 Hz
UI_PERIOD_MS = 200      # 5 Hz (heartbeat y parpadeo de alarma)
LOG_PERIOD_MS = 1000    # 1 Hz
IDLE_MS = 2             # pausa minima del loop principal

# ---------------- Hardware ----------------
adc = ADC(Pin(PIN_ADC))
led_normal = Pin(PIN_LED_NORMAL, Pin.OUT, value=0)
led_warning = Pin(PIN_LED_WARNING, Pin.OUT, value=0)
led_alarm = Pin(PIN_LED_ALARM, Pin.OUT, value=0)
heartbeat = Pin(PIN_HEARTBEAT, Pin.OUT, value=0)
button = Pin(PIN_BUTTON, Pin.IN, Pin.PULL_UP)

# ---------------- Estado del sistema ----------------
window = []             # ultimas FILTER_SIZE lecturas crudas
raw_value = 0
filtered_value = 0
percent_value = 0.0
state = "INIT"
sample_count = 0
last_logged_count = 0   # para calcular muestras por segundo
alarm_ack = False
alarm_blink = False
last_button = 1


# Regresa True cuando ya llego (o paso) el tiempo objetivo
def due(now, target):
    return ticks_diff(now, target) >= 0


# Promedio movil: entra la lectura nueva y sale la mas vieja
def moving_average(raw):
    window.append(raw)
    if len(window) > FILTER_SIZE:
        window.pop(0)
    return sum(window) // len(window)


def to_percent(raw):
    return raw * 100 / ADC_MAX


def classify(percent):
    if percent >= ALARM_PCT:
        return "ALARM"
    elif percent >= WARNING_PCT:
        return "WARNING"
    else:
        return "NORMAL"


# ---------------- Tareas ----------------
def sensor_task():
    global raw_value, filtered_value, percent_value, state
    global sample_count, alarm_ack

    raw_value = adc.read_u16()
    filtered_value = moving_average(raw_value)
    percent_value = to_percent(filtered_value)
    state = classify(percent_value)
    sample_count += 1

    # Si la condicion de alarma desaparece, el ACK anterior se borra
    if state != "ALARM":
        alarm_ack = False


def button_task():
    global last_button, alarm_ack, sample_count, last_logged_count

    current = button.value()

    # Solo cuenta una pulsacion nueva (flanco 1 -> 0)
    if last_button == 1 and current == 0:
        if state == "ALARM":
            alarm_ack = True
            print(">>> ALARMA RECONOCIDA | ack= True")
        else:
            sample_count = 0
            last_logged_count = 0
            print(">>> Sin ALARM: contador de muestras reiniciado")

    last_button = current


def set_state_leds(normal, warning, alarm):
    led_normal.value(normal)
    led_warning.value(warning)
    led_alarm.value(alarm)


def ui_task():
    global alarm_blink

    heartbeat.toggle()

    if state == "NORMAL":
        set_state_leds(1, 0, 0)
    elif state == "WARNING":
        set_state_leds(0, 1, 0)
    elif state == "ALARM":
        # Sin ACK el rojo parpadea; con ACK queda fijo
        alarm_blink = not alarm_blink
        set_state_leds(0, 0, 1 if alarm_ack else alarm_blink)


def log_task():
    global last_logged_count

    rate = sample_count - last_logged_count
    last_logged_count = sample_count
    print("raw=", raw_value,
          "filtered=", filtered_value,
          "percent=", round(percent_value, 1),
          "state=", state,
          "samples=", sample_count,
          "rate=", rate, "/s",
          "ack=", alarm_ack)


# ---------------- Inicio ----------------
print("CHALLENGE 08 - Multitarea cooperativa (Wokwi)")
print("Umbrales: WARNING >=", WARNING_PCT, "% | ALARM >=", ALARM_PCT, "%")
print("Filtro: promedio movil de", FILTER_SIZE, "muestras cada", SENSOR_PERIOD_MS, "ms")
print("Boton: en ALARM = ACK | fuera de ALARM = reset del contador")
print(20 * "=")

now = ticks_ms()
next_sensor = now
next_button = now
next_ui = now
next_log = ticks_add(now, LOG_PERIOD_MS)

try:
    while True:
        now = ticks_ms()

        if due(now, next_sensor):
            sensor_task()
            next_sensor = ticks_add(now, SENSOR_PERIOD_MS)

        if due(now, next_button):
            button_task()
            next_button = ticks_add(now, BUTTON_PERIOD_MS)

        if due(now, next_ui):
            ui_task()
            next_ui = ticks_add(now, UI_PERIOD_MS)

        if due(now, next_log):
            log_task()
            next_log = ticks_add(now, LOG_PERIOD_MS)

        sleep_ms(IDLE_MS)
finally:
    # Al detener (Ctrl-C) se apagan todos los LEDs
    set_state_leds(0, 0, 0)
    heartbeat.value(0)
    print("\n[FIN] Sistema detenido, LEDs apagados")
