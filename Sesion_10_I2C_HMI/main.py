# SESION 10 - CHALLENGE 10: Smart I2C HMI Monitor
# Raspberry Pi Pico + MicroPython (Wokwi)
# Axel Garcia Arellano
#
# Bus I2C0: SDA = GP4, SCL = GP5, 400 kHz
# OLED SSD1306 128x64 (0x3C)  +  MPU6050 opcional (0x68, BONUS)
# ADC GP26 (potenciometro) | Boton GP16 a GND (PULL_UP, tecla A) | LED ALARM GP15
#
# Paginas (boton -> flanco 1->0):
#   1 LIVE  : ADC %, estado NORMAL/WARNING/ALARM, barra, LED
#   2 I2C   : SDA/SCL, frecuencia, direcciones del scan, temperatura MPU6050
#   3 STATS : minimo, maximo, numero de muestras

from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
from time import ticks_ms, ticks_diff, sleep_ms

# ---------------- Configuracion ----------------
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400_000
OLED_CANDIDATES = (0x3C, 0x3D)   # la direccion real la decide scan()
MPU_ADDR = 0x68

WARNING_TH = 50.0                # NORMAL  <  50 %
ALARM_TH = 75.0                  # WARNING <  75 %, ALARM >= 75 %

SAMPLE_MS = 100                  # periodo de muestreo + refresco OLED
MPU_MS = 500                     # periodo de lectura del MPU6050
DEBOUNCE_MS = 50                 # antirrebote del boton
LOOP_MS = 10                     # pausa minima del lazo (sin sleeps largos)

PAGE_NAMES = ('LIVE', 'I2C', 'STATS')

# ---------------- Hardware ----------------
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
adc = ADC(26)
button = Pin(16, Pin.IN, Pin.PULL_UP)
led_alarm = Pin(15, Pin.OUT)
led_alarm.value(0)


# ---------------- TODO 1: scan + validacion ----------------
def scan_bus():
    found = i2c.scan()
    print('I2C scan -> Decimal:', found, '| Hex:', [hex(a) for a in found])
    return found


def find_oled(found):
    for addr in OLED_CANDIDATES:
        if addr in found:
            return addr
    return None


def wait_for_oled():
    """Diagnostico: no avanza al driver hasta que scan() vea la OLED."""
    while True:
        found = scan_bus()
        addr = find_oled(found)
        if addr is not None:
            print('OLED detectada en', hex(addr), '(', addr, 'decimal )')
            return found, addr
        led_alarm.value(0)
        if not found:
            print('ERROR: scan() vacio. Revisar VCC, GND, SDA=GP4, SCL=GP5.')
        else:
            print('ERROR: OLED no detectada (se esperaba 0x3C/0x3D).',
                  'Dispositivos:', [hex(a) for a in found])
        print('Reintentando scan en 1 s...')
        sleep_ms(1000)


print('=== Smart I2C HMI Monitor ===')
print('I2C0: SDA=GP{}  SCL=GP{}  freq={} Hz'.format(SDA_PIN, SCL_PIN, I2C_FREQ))
devices, oled_addr = wait_for_oled()

# ---------------- TODO 2: objeto OLED ----------------
oled = SSD1306_I2C(128, 64, i2c, addr=oled_addr)


# ---------------- BONUS: MPU6050 en el mismo bus ----------------
mpu_ok = False
mpu_temp = None


def mpu_init():
    global mpu_ok
    mpu_ok = False
    if MPU_ADDR not in devices:
        print('MPU6050 no presente (bonus desactivado)')
        return
    try:
        i2c.writeto_mem(MPU_ADDR, 0x6B, b'\x00')          # PWR_MGMT_1: despertar
        who = i2c.readfrom_mem(MPU_ADDR, 0x75, 1)[0]      # WHO_AM_I
        print('MPU6050 WHO_AM_I =', hex(who))
        mpu_ok = True
    except OSError as e:
        print('MPU6050 error:', e)


def mpu_read_temp():
    global mpu_temp, mpu_ok
    if not mpu_ok:
        return
    try:
        d = i2c.readfrom_mem(MPU_ADDR, 0x41, 2)           # TEMP_OUT_H / L
        raw = (d[0] << 8) | d[1]
        if raw & 0x8000:
            raw -= 65536
        mpu_temp = raw / 340 + 36.53
    except OSError:
        mpu_ok = False
        mpu_temp = None
        print('MPU6050 dejo de responder')


mpu_init()


# ---------------- TODO 3: clasificacion ----------------
def classify(percent):
    if percent < WARNING_TH:
        return 'NORMAL'
    if percent < ALARM_TH:
        return 'WARNING'
    return 'ALARM'


# ---------------- TODO 4: barra ----------------
def draw_bar(percent, y=50):
    percent = max(0.0, min(100.0, percent))
    oled.rect(4, y, 120, 12, 1)
    inner = int(116 * percent / 100)
    if inner > 0:
        oled.fill_rect(6, y + 2, inner, 8, 1)
    # marcas de umbral (50 % y 75 %)
    for th in (WARNING_TH, ALARM_TH):
        x = 6 + int(116 * th / 100)
        oled.vline(x, y - 3, 3, 1)


# ---------------- TODO 5: paginas ----------------
def draw_header(page):
    title = '{} {}/3'.format(PAGE_NAMES[page], page + 1)
    oled.fill_rect(0, 0, 128, 10, 1)
    oled.text(title, 2, 1, 0)


def live_page(percent, state):
    oled.text('ADC: {:5.1f} %'.format(percent), 0, 14)
    if state == 'ALARM':
        # estado resaltado en video inverso
        oled.fill_rect(0, 25, 8 * len(state) + 4, 11, 1)
        oled.text(state, 2, 27, 0)
    else:
        oled.text(state, 2, 27)
    oled.text('LED:' + ('ON' if state == 'ALARM' else 'OFF'), 72, 27)
    draw_bar(percent)


def i2c_page():
    oled.text('SDA:GP{} SCL:GP{}'.format(SDA_PIN, SCL_PIN), 0, 13)
    oled.text('FREQ: {} kHz'.format(I2C_FREQ // 1000), 0, 23)
    oled.text('DEV: {}'.format(len(devices)), 0, 33)
    oled.text(','.join(hex(a) for a in devices)[:16], 0, 43)
    if mpu_ok and mpu_temp is not None:
        oled.text('MPU T:{:5.1f}C'.format(mpu_temp), 0, 54)
    else:
        oled.text('OLED: ' + hex(oled_addr), 0, 54)


def stats_page():
    oled.text('MIN: {:5.1f} %'.format(min_value), 0, 16)
    oled.text('MAX: {:5.1f} %'.format(max_value), 0, 28)
    oled.text('N:   {}'.format(samples), 0, 40)
    oled.text('AVG: {:5.1f} %'.format(total / samples if samples else 0), 0, 52)


def draw_page(page, percent, state):
    oled.fill(0)
    draw_header(page)
    if page == 0:
        live_page(percent, state)
    elif page == 1:
        i2c_page()
    else:
        stats_page()


# ---------------- Estado ----------------
page = 0
last_button = 1
last_edge = ticks_ms()
samples = 0
total = 0.0
min_value = 100.0
max_value = 0.0
percent = 0.0
state = 'NORMAL'

t_sample = ticks_ms() - SAMPLE_MS
t_mpu = ticks_ms() - MPU_MS

print('Sistema listo. Boton A = cambiar pagina.')

# ---------------- Lazo principal (no bloqueante) ----------------
while True:
    now = ticks_ms()

    # TODO 7: boton por flanco 1->0 con antirrebote
    current = button.value()
    if last_button == 1 and current == 0 and ticks_diff(now, last_edge) > DEBOUNCE_MS:
        page = (page + 1) % 3
        last_edge = now
        print('Pagina ->', page + 1, PAGE_NAMES[page])
        t_sample = now - SAMPLE_MS   # redibujar inmediatamente
    last_button = current

    # BONUS: lectura periodica del MPU6050
    if ticks_diff(now, t_mpu) >= MPU_MS:
        t_mpu = now
        mpu_read_temp()

    # Muestreo + HMI cada SAMPLE_MS
    if ticks_diff(now, t_sample) >= SAMPLE_MS:
        t_sample = now
        percent = adc.read_u16() * 100 / 65535
        state = classify(percent)

        samples += 1
        total += percent
        min_value = min(min_value, percent)
        max_value = max(max_value, percent)

        # TODO 6: LED ALARM solo en ALARM
        led_alarm.value(1 if state == 'ALARM' else 0)

        # TODO 8: fill -> draw -> show
        draw_page(page, percent, state)
        try:
            oled.show()
        except OSError as e:
            # La OLED dejo de contestar (ACK) -> diagnostico y re-scan
            print('ERROR I2C al enviar framebuffer:', e)
            devices, oled_addr = wait_for_oled()
            oled = SSD1306_I2C(128, 64, i2c, addr=oled_addr)
            mpu_init()

    sleep_ms(LOOP_MS)
