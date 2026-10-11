# =========================================================================
#  CHALLENGE 08 - Dual-core real con _thread (Pico fisica)
#  Sesion 08: Procesamiento multihilo / dual-core
#  Axel Garcia Arellano
#
#  Core 1 (hilo nuevo) : tarea critica -> lee ADC, filtra y clasifica
#  Core 0 (programa)   : boton, LEDs, heartbeat y serial
#  Los datos que comparten ambos nucleos viven en "shared" y siempre se
#  leen/escriben con el lock tomado, para que nunca se mezclen a medias.
#  Mismos pines, umbrales y formato serial que main_wokwi.py.
# =========================================================================

from machine import Pin, ADC
from time import ticks_ms, ticks_diff, ticks_add, sleep_ms
import _thread

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
SENSOR_PERIOD_MS = 20   # Core 1: 50 Hz
BUTTON_PERIOD_MS = 50   # Core 0: 20 Hz
UI_PERIOD_MS = 200      # Core 0: 5 Hz (heartbeat y parpadeo de alarma)
LOG_PERIOD_MS = 1000    # Core 0: 1 Hz
IDLE_MS = 2             # pausa minima de cada loop

# ---------------- Hardware ----------------
adc = ADC(Pin(PIN_ADC))
led_normal = Pin(PIN_LED_NORMAL, Pin.OUT, value=0)
led_warning = Pin(PIN_LED_WARNING, Pin.OUT, value=0)
led_alarm = Pin(PIN_LED_ALARM, Pin.OUT, value=0)
heartbeat = Pin(PIN_HEARTBEAT, Pin.OUT, value=0)
button = Pin(PIN_BUTTON, Pin.IN, Pin.PULL_UP)

# ---------------- Datos compartidos entre nucleos ----------------
lock = _thread.allocate_lock()
shared = {
    "raw": 0,
    "filtered": 0,
    "percent": 0.0,
    "state": "INIT",
    "samples": 0,
    "ack": False,
    "running": True,    # Core 0 lo pone en False para detener el Core 1
    "error": None,      # Core 1 guarda aqui el error si su hilo falla
}

# ---------------- Variables solo del Core 0 ----------------
alarm_blink = False
last_button = 1
last_logged_count = 0


# Regresa True cuando ya llego (o paso) el tiempo objetivo
def due(now, target):
    return ticks_diff(now, target) >= 0


# Promedio movil: entra la lectura nueva y sale la mas vieja
def moving_average(window, raw):
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


# ---------------- CORE 1: sensor critico ----------------
def sensor_core():
    try:
        sensor_loop()
    except Exception as e:
        # Sin esto el hilo moriria en silencio y el Core 0 se quedaria en INIT
        print("SENSOR_CORE ERROR:", repr(e))
        with lock:
            shared["error"] = repr(e)


def sensor_loop():
    window = []         # el filtro vive solo en el Core 1, no necesita lock
    next_sample = ticks_ms()

    while True:
        now = ticks_ms()
        if due(now, next_sample):
            next_sample = ticks_add(now, SENSOR_PERIOD_MS)

            # Lectura y calculo fuera del lock: el Core 0 no espera por esto
            raw = adc.read_u16()
            filtered = moving_average(window, raw)
            percent = to_percent(filtered)
            state = classify(percent)

            with lock:
                if not shared["running"]:
                    break
                shared["raw"] = raw
                shared["filtered"] = filtered
                shared["percent"] = percent
                shared["state"] = state
                shared["samples"] += 1
                # Si la condicion de alarma desaparece, el ACK se borra
                if state != "ALARM":
                    shared["ack"] = False

        sleep_ms(IDLE_MS)


# ---------------- CORE 0: tareas de interfaz ----------------
# Copia de los datos compartidos tomada de una sola vez con el lock
def read_shared():
    with lock:
        return (shared["raw"], shared["filtered"], shared["percent"],
                shared["state"], shared["samples"], shared["ack"],
                shared["error"])


def button_task():
    global last_button, last_logged_count

    current = button.value()

    # Solo cuenta una pulsacion nueva (flanco 1 -> 0)
    if last_button == 1 and current == 0:
        with lock:
            in_alarm = shared["state"] == "ALARM"
            if in_alarm:
                shared["ack"] = True
            else:
                shared["samples"] = 0
        if in_alarm:
            print(">>> CORE 0: ALARMA RECONOCIDA | ack= True")
        else:
            last_logged_count = 0
            print(">>> CORE 0: sin ALARM, contador de muestras reiniciado")

    last_button = current


def set_state_leds(normal, warning, alarm):
    led_normal.value(normal)
    led_warning.value(warning)
    led_alarm.value(alarm)


def ui_task():
    global alarm_blink

    _, _, _, state, _, ack, _ = read_shared()
    heartbeat.toggle()

    if state == "NORMAL":
        set_state_leds(1, 0, 0)
    elif state == "WARNING":
        set_state_leds(0, 1, 0)
    elif state == "ALARM":
        # Sin ACK el rojo parpadea; con ACK queda fijo
        alarm_blink = not alarm_blink
        set_state_leds(0, 0, 1 if ack else alarm_blink)


def log_task():
    global last_logged_count

    raw, filtered, percent, state, samples, ack, error = read_shared()
    if error:
        print("SENSOR_CORE ERROR | Core 1 detenido:", error)
        return

    rate = samples - last_logged_count
    last_logged_count = samples
    print("CORE0 | raw=", raw,
          "filtered=", filtered,
          "percent=", round(percent, 1),
          "state=", state,
          "samples_core1=", samples,
          "rate=", rate, "/s",
          "ack=", ack)


# ---------------- CORE 0: loop principal ----------------
# Sus variables son locales a proposito: en el RP2040/RP2350 no hay GIL, y
# si el Core 0 crea globales nuevas mientras el Core 1 busca una (por ejemplo
# to_percent), el diccionario de globales se reorganiza y el Core 1 puede
# recibir un NameError falso. Despues de lanzar el hilo no se crean globales.
def main():
    print("CHALLENGE 08 - Dual-core real con _thread (Pico fisica)")
    print("Umbrales: WARNING >=", WARNING_PCT, "% | ALARM >=", ALARM_PCT, "%")
    print("Filtro: promedio movil de", FILTER_SIZE, "muestras cada", SENSOR_PERIOD_MS, "ms")
    print("Boton: en ALARM = ACK | fuera de ALARM = reset del contador")
    print(20 * "=")

    _thread.start_new_thread(sensor_core, ())
    print("Core 1: adquisicion del ADC iniciada")
    print("Core 0: boton, LEDs, heartbeat y serial")

    now = ticks_ms()
    next_button = now
    next_ui = now
    next_log = ticks_add(now, LOG_PERIOD_MS)

    try:
        while True:
            now = ticks_ms()

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
        # Al detener (Ctrl-C) se avisa al Core 1 que termine y se apagan los LEDs
        with lock:
            shared["running"] = False
        sleep_ms(50)    # tiempo para que el Core 1 vea la bandera y salga
        set_state_leds(0, 0, 0)
        heartbeat.value(0)
        print("\n[FIN] Core 1 detenido, LEDs apagados")


main()
