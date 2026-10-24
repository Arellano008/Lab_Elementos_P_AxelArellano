# =========================================================================
#  EXAMEN PRACTICO 02 - Sistema de Control Serial Inteligente
#  Angel Rugerio Jimenez (#201720)
#  Axel Garcia Arellano (#201251)
#
#  Core 0: comandos (USB -> UART0 TX -> jumper -> RX), LED digital y PWM
#  Core 1: ADC cada 20 ms, % del ADC, SAMPLES y boton
# =========================================================================

from machine import UART, Pin, PWM, ADC
from time import sleep_ms, ticks_ms, ticks_diff
import _thread

USE_UART = True         # False = procesar directo, sin el jumper GP0 -> GP1
RX_TIMEOUT_MS = 1000
SAMPLE_MS = 20          # periodo del Core 1 (~50 muestras/s)
FILTER_SIZE = 8         # promedio movil

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
led = Pin(13, Pin.OUT, value=0)
pwm = PWM(Pin(15), freq=10, duty_u16=0)
button = Pin(16, Pin.IN, Pin.PULL_UP)
adc = ADC(Pin(26))

# Datos que comparten los dos nucleos: siempre con el lock tomado
lock = _thread.allocate_lock()
shared = {"pwm": 0, "adc_pct": 0.0, "btn": 0, "samples": 0, "running": True}


def status_frame():
    with lock:
        return "STATUS,LED={},PWM={},ADC={:.1f},BTN={},SAMPLES={}".format(
            led.value(), shared["pwm"], shared["adc_pct"],
            shared["btn"], shared["samples"])


# ---------------- CORE 1 ----------------
def core1():
    window = []
    last_btn = 0

    while True:
        # ADC: promedio de las ultimas lecturas -> 0 a 100 %
        window.append(adc.read_u16())
        if len(window) > FILTER_SIZE:
            window.pop(0)
        adc_pct = sum(window) / len(window) * 100 / 65535

        btn = 1 - button.value()        # PULL_UP: presionado = 0 -> BTN=1
        pressed = btn == 1 and last_btn == 0
        last_btn = btn

        with lock:
            if not shared["running"]:
                break
            shared["adc_pct"] = adc_pct
            shared["btn"] = btn
            shared["samples"] += 1

        if pressed:
            print("\nEVENT,BTN,PRESSED")
            print(status_frame())

        sleep_ms(SAMPLE_MS)


# ---------------- CORE 0: UART ----------------
def uart_roundtrip(text):
    while uart.any():                   # vaciar datos viejos del RX
        uart.read()
    uart.write((text + "\n").encode())  # TX

    buffer = b""
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < RX_TIMEOUT_MS:
        if uart.any():                  # RX: juntar bytes hasta el '\n'
            byte = uart.read(1)
            if byte == b"\n":
                return buffer.decode().strip()
            buffer += byte
        else:
            sleep_ms(1)
    return None                         # trama incompleta


# ---------------- CORE 0: parser ----------------
def set_pwm(percent):
    pwm.duty_u16(percent * 65535 // 100)
    with lock:
        shared["pwm"] = percent


def handle_frame(frame):
    parts = [p.strip() for p in frame.upper().split(",")]
    cmd = parts[0]

    if cmd == "PING":
        return "PONG" if len(parts) == 1 else "ERR,BAD_FORMAT"

    if cmd == "LED":
        if len(parts) != 2 or parts[1] == "":
            return "ERR,BAD_FORMAT"
        if parts[1] not in ("0", "1"):
            return "ERR,BAD_VALUE"
        led.value(int(parts[1]))
        return "ACK,LED," + parts[1]

    if cmd == "PWM":
        if len(parts) != 2 or parts[1] == "":
            return "ERR,BAD_FORMAT"
        if not parts[1].isdigit():
            return "ERR,BAD_VALUE"
        n = int(parts[1])
        if n > 100:
            return "ERR,PWM_RANGE"
        set_pwm(n)
        return "ACK,PWM,{}".format(n)

    if cmd == "STATUS":
        return status_frame() if len(parts) == 1 else "ERR,BAD_FORMAT"

    if cmd == "ALL":                    # compuesto: LED y PWM juntos
        if len(parts) != 2 or parts[1] == "":
            return "ERR,BAD_FORMAT"
        if parts[1] not in ("0", "1"):
            return "ERR,BAD_VALUE"
        led.value(int(parts[1]))
        set_pwm(100 * int(parts[1]))
        return "ACK,ALL," + parts[1]

    # ---- BONUS ----
    if cmd == "HELP":
        if len(parts) != 1:
            return "ERR,BAD_FORMAT"
        return "ACK,HELP,PING|LED,<0|1>|PWM,<0-100>|STATUS|ALL,<0|1>|TOGGLE"

    if cmd == "TOGGLE":
        if len(parts) != 1:
            return "ERR,BAD_FORMAT"
        led.toggle()
        return "ACK,TOGGLE,LED={}".format(led.value())

    return "ERR,UNKNOWN_COMMAND"


# ---------------- CORE 0: main ----------------
# Variables locales: con el Core 1 corriendo no se crean globales nuevas
def main():
    print(50 * "=")
    print(" EXAMEN PRACTICO 02 - Control Serial Inteligente")
    print(" LED=GP13  PWM=GP15  BTN=GP16  ADC=GP26")
    print(" UART0 9600 8N1 | Jumper GP0 -> GP1")
    print(50 * "=")
    print(" Comandos:")
    for name in ("PING", "LED,<0|1>", "PWM,<0-100>", "STATUS",
                 "ALL,<0|1>", "HELP", "TOGGLE"):
        print("   " + name)
    print(50 * "=")
    _thread.start_new_thread(core1, ())

    try:
        while True:
            command = input("CMD> ").strip()
            if not command:
                continue

            print("USB CMD :", command)
            received = uart_roundtrip(command) if USE_UART else command
            if received is None:
                print("RESP    : ERR,NO_UART_DATA (revisa el jumper GP0->GP1)")
                continue

            print("UART RX :", received)
            print("RESP    :", handle_frame(received))
    finally:
        # Al dar Stop: detener el Core 1 y apagar salidas
        with lock:
            shared["running"] = False
        sleep_ms(50)
        led.value(0)
        pwm.duty_u16(0)
        print("\n[FIN] Core 1 detenido, salidas apagadas")


main()
