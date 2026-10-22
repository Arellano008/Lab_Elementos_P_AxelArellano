# =========================================================================
#  CHALLENGE 09 - UART Command Center (Pico fisica + loopback)
#  Sesion 09: Comunicacion UART
#  Axel Garcia Arellano
#
#  comandos:  PING | HELP | GET,STATUS | SET,<LED1|LED2|ALL>,<0|1>
#           TOGGLE,<LED1|LED2|ALL> | BLINK,<LED1|LED2>,<ms> (0 = detener)
#  Respuestas: ACK,... | STATUS,... | ERR,<motivo>
# =========================================================================

from machine import UART, Pin, Timer
from time import sleep_ms, ticks_ms, ticks_diff

# ---------------- Pines ----------------
PIN_UART_TX = 0         # GP0 = UART0 TX
PIN_UART_RX = 1         # GP1 = UART0 RX
PIN_LED1 = 13           # GP13 -> LED1
PIN_LED2 = 14           # GP14 -> LED2

# ---------------- UART ----------------
BAUDRATE = 9600         # 8N1: 10 bits por byte -> ~960 bytes/s
RX_TIMEOUT_MS = 1000

# ---------------- BLINK ----------------
BLINK_MIN_MS = 50
BLINK_MAX_MS = 5000

uart = UART(0, baudrate=BAUDRATE, bits=8, parity=None, stop=1,
            tx=Pin(PIN_UART_TX), rx=Pin(PIN_UART_RX))

leds = {
    "LED1": Pin(PIN_LED1, Pin.OUT, value=0),
    "LED2": Pin(PIN_LED2, Pin.OUT, value=0),
}

# Un timer por LED para BLINK. Usa interrupcion de timer, asi el LED sigue
# parpadeando mientras input() espera el siguiente comando.
blink_timers = {}


# =========================================================================
#  Capa de transporte (igual que en el starter del profesor)
# =========================================================================

def clear_rx():
    """Vacia datos viejos del buffer RX antes de una nueva prueba."""
    while uart.any():
        uart.read()


def receive_complete_line(timeout_ms=RX_TIMEOUT_MS):
    """
    Lee byte por byte hasta encontrar '\\n'.
    Evita procesar una trama parcial cuando uart.any() se activa
    apenas llega el primer caracter.
    """
    buffer = bytearray()
    start = ticks_ms()

    while ticks_diff(ticks_ms(), start) < timeout_ms:

        while uart.any():
            byte = uart.read(1)

            if not byte:
                break

            if byte == b"\n":
                try:
                    return buffer.decode().rstrip("\r")
                except UnicodeError:
                    # Bytes corruptos (p. ej. baud rate distinto): no es texto
                    return ""

            buffer.extend(byte)

        sleep_ms(1)

    # Si expiro el tiempo, NO aceptamos una trama incompleta.
    return None


def uart_roundtrip(text, timeout_ms=RX_TIMEOUT_MS):
    clear_rx()

    # Enviar una trama completa terminada en LF.
    uart.write((text + "\n").encode())

    # Esperar explicitamente hasta recibir LF.
    return receive_complete_line(timeout_ms)


# =========================================================================
#  Salidas
# =========================================================================

def stop_blink(device):
    timer = blink_timers.pop(device, None)
    if timer is not None:
        timer.deinit()


def start_blink(device, period_ms):
    stop_blink(device)
    led = leds[device]
    timer = Timer(-1)
    timer.init(period=period_ms, mode=Timer.PERIODIC,
               callback=lambda t: led.toggle())
    blink_timers[device] = timer


def target_devices(device):
    """LED1 -> [LED1], ALL -> [LED1, LED2], otro -> None."""
    if device == "ALL":
        return list(leds)
    if device in leds:
        return [device]
    return None


def status_frame():
    # TODO 1
    return "STATUS,LED1,{},LED2,{}".format(leds["LED1"].value(),
                                           leds["LED2"].value())


def set_output(device, value):
    # TODO 2: solo "0"/"1" y solo LED1, LED2 o ALL
    devices = target_devices(device)
    if devices is None or value not in ("0", "1"):
        return False

    for name in devices:
        stop_blink(name)        # un SET manda sobre un BLINK activo
        leds[name].value(int(value))
    return True


# =========================================================================
#  Parser: CLEAN -> PARSE -> VALIDATE -> ACT -> REPLY
# =========================================================================

HELP_TEXT = ("ACK,HELP,PING|GET,STATUS|SET,<LED1|LED2|ALL>,<0|1>|"
             "TOGGLE,<LED1|LED2|ALL>|BLINK,<LED1|LED2>,<ms>")


def handle_set(parts):
    if len(parts) != 3:
        return "ERR,BAD_FIELDS"
    _, device, value = parts
    if target_devices(device) is None:
        return "ERR,BAD_DEVICE"
    if not set_output(device, value):
        return "ERR,BAD_VALUE"
    return "ACK,{},{}".format(device, value)


def handle_toggle(parts):
    if len(parts) != 2:
        return "ERR,BAD_FIELDS"
    device = parts[1]
    devices = target_devices(device)
    if devices is None:
        return "ERR,BAD_DEVICE"
    for name in devices:
        stop_blink(name)
        leds[name].toggle()
    if device == "ALL":
        return "ACK,TOGGLE," + status_frame()[len("STATUS,"):]
    return "ACK,{},{}".format(device, leds[device].value())


def handle_blink(parts):
    if len(parts) != 3:
        return "ERR,BAD_FIELDS"
    _, device, period = parts
    if device not in leds:              # ALL no aplica: solo un LED
        return "ERR,BAD_DEVICE"
    if not period.isdigit():
        return "ERR,BAD_VALUE"
    period_ms = int(period)
    if period_ms == 0:
        stop_blink(device)
        leds[device].off()
        return "ACK,{},BLINK_OFF".format(device)
    if not BLINK_MIN_MS <= period_ms <= BLINK_MAX_MS:
        return "ERR,BAD_PERIOD"
    start_blink(device, period_ms)
    return "ACK,{},BLINK,{}".format(device, period_ms)


def handle_frame(frame):
    # CLEAN: mayusculas y sin espacios alrededor de cada campo
    parts = [p.strip() for p in frame.strip().upper().split(",")]
    cmd = parts[0]

    # TODO 3
    if cmd == "PING":
        return "ACK,PONG" if len(parts) == 1 else "ERR,BAD_FIELDS"

    if cmd == "HELP":
        return HELP_TEXT if len(parts) == 1 else "ERR,BAD_FIELDS"

    # TODO 4
    if cmd == "GET":
        if len(parts) == 2 and parts[1] == "STATUS":
            return status_frame()
        return "ERR,BAD_GET_FRAME"

    # TODO 5
    if cmd == "SET":
        return handle_set(parts)

    if cmd == "TOGGLE":
        return handle_toggle(parts)

    if cmd == "BLINK":
        return handle_blink(parts)

    # TODO 6
    return "ERR,UNKNOWN_FRAME"


# =========================================================================
#  Programa principal
# =========================================================================

def shutdown():
    for name in list(blink_timers):
        stop_blink(name)
    for led in leds.values():
        led.off()


def main():
    print("CHALLENGE 09 - UART Command Center")
    print("UART0 {} 8N1 | Jumper: GP0(TX) -> GP1(RX)".format(BAUDRATE))
    print("Escribe HELP para ver los comandos.")

    try:
        while True:
            command = input("CMD> ").strip()

            if not command:
                continue

            print("USB CMD :", command)
            received = uart_roundtrip(command)

            if received is None:
                print("UART RX : SIN DATOS. Revisa el jumper GP0->GP1")
                print("RESP    : ERR,NO_UART_DATA")
                continue

            print("UART RX :", received)
            print("RESP    :", handle_frame(received))
    except KeyboardInterrupt:
        print("Programa detenido")
    finally:
        shutdown()


main()
