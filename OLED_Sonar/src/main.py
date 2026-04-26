from machine import Pin, ADC, PWM, I2C, Timer
import time

# ── IR Sensors ──
ir_left  = ADC(Pin(26))
ir_right = ADC(Pin(27))

# ── Motors ──
gp10 = PWM(Pin(10))
gp11 = Pin(11, Pin.OUT)
gp12 = Pin(12, Pin.OUT)
gp13 = PWM(Pin(13))
gp10.freq(1000)
gp13.freq(1000)

# ── Buzzer ──
buzzer = PWM(Pin(22))

# ── Sonar ──
trig = Pin(14, Pin.OUT)
echo = Pin(15, Pin.IN)

# ── LEDs ──
leds = [Pin(6, Pin.OUT), Pin(7, Pin.OUT), Pin(8, Pin.OUT), Pin(9, Pin.OUT)]

# ── OLED ──
i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)
devices = i2c.scan()
print(devices)
if devices:
    from sh1106 import SH1106_I2C
    oled = SH1106_I2C(128, 64, i2c, addr=devices[0])
else:
    oled = None

# ── TUNE THESE ──
SPEED        = 83
BALANCE      = 57
TURN         = 85
THRESHOLD    = 3.3
SLOW_FACTOR  = 0.9
STOP_CONFIRM = 3
SONAR_STOP   = 20
MUSIC        = True

# ── Song of Storms ──
notes = {
    'D':  293.66,
    'E':  329.63,
    'F':  349.23,
    'G':  392.00,
    'A':  440.00,
    'Bb': 466.16,
    'C':  523.25,
}

BPM = 80
Q   = 60 / BPM
E   = Q / 2
H   = Q * 2
DQ  = Q * 1.5

melody = [
    'D',  'F',  'D',
    'D',  'F',  'D',
    'E',  'E',
    'C',  'C',
    'A',
    'D',  'F',  'D',
    'D',  'F',  'D',
    'E',  'G',  'E',
    'C',  'C',
    'A',
    'F',  'F',  'G',  'F',  'E',
    'D',  'E',  'F',  'A',
    'D',  'C',  'A',
    'F',  'F',  'G',  'F',  'E',
    'D',  'E',  'F',  'A',
    'D',  'C',  'A',
]

lengths = [
    E,  E,  Q,
    E,  E,  Q,
    E,  E,
    E,  E,
    H,
    E,  E,  Q,
    E,  E,  Q,
    E,  E,  E,
    E,  E,
    H,
    E,  E,  E,  E,  E,
    E,  E,  E,  DQ,
    E,  E,  H,
    E,  E,  E,  E,  E,
    E,  E,  E,  DQ,
    E,  E,  H,
]

# ── Shared state ──
STEERING      = 90
stop_count    = 0
status        = "STRAIGHT"
arrow         = "  ^  "
left_v        = 0.0
right_v       = 0.0
left_on       = False
right_on      = False
stopped       = False
sonar_stopped = False
oled_busy     = False          # ── NEW ──
led_index     = 0

def get_distance():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    timeout = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), timeout) > 30000:
            return 999

    start = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), start) > 30000:
            return 999

    end = time.ticks_us()
    return (time.ticks_diff(end, start) * 0.034) / 2

def leds_solid():
    for led in leds:
        led.value(1)

def leds_off():
    for led in leds:
        led.value(0)

def drive(steering, balance, speed=None):
    if speed is None:
        speed = SPEED
    base  = int(speed / 100 * 65535)
    shift = (balance - 50) / 50.0

    if shift > 0:
        left_speed  = base
        right_speed = int(base * (1.0 - shift))
    elif shift < 0:
        left_speed  = int(base * (1.0 + shift))
        right_speed = base
    else:
        left_speed  = base
        right_speed = base

    normalized = (steering - 90) / 90.0

    if normalized > 0:
        left_speed  = min(65535, int(left_speed * 1.2))
        right_speed = int(right_speed * (1.0 - normalized))
    elif normalized < 0:
        right_speed = min(65535, int(right_speed * 1.2))
        left_speed  = int(left_speed  * (1.0 + normalized))

    left_speed  = max(0, min(65535, left_speed))
    right_speed = max(0, min(65535, right_speed))

    gp11.value(0)
    gp12.value(0)
    gp10.duty_u16(left_speed)
    gp13.duty_u16(right_speed)

def stop_motors():
    gp10.duty_u16(0)
    gp13.duty_u16(0)
    gp11.value(0)
    gp12.value(0)

def update_oled(status, arrow, left_on, right_on, left_v, right_v, steering):
    if not oled:
        return
    oled.fill(0)
    oled.text(arrow, 52, 0)
    oled.text(status, 0, 10)
    oled.text("Spd:" + str(int(SPEED)) + " Bal:" + str(int(BALANCE)), 0, 20)

    oled.rect(10, 32, 20, 16, 1)
    if left_on:
        oled.fill_rect(10, 32, 20, 16, 1)
        oled.text("B", 16, 35, 0)
    else:
        oled.text("W", 16, 35, 1)
    oled.text(str(left_v), 0, 50)

    oled.rect(98, 32, 20, 16, 1)
    if right_on:
        oled.fill_rect(98, 32, 20, 16, 1)
        oled.text("B", 104, 35, 0)
    else:
        oled.text("W", 104, 35, 1)
    oled.text(str(right_v), 72, 50)

    oled.hline(0, 62, 128, 1)
    bar_x = steering * 128 // 180
    oled.fill_rect(max(0, bar_x - 2), 59, 4, 4, 1)

    oled.show()

def robot_tick(timer):
    global STEERING, stop_count, status, arrow
    global left_v, right_v, left_on, right_on
    global stopped, sonar_stopped, led_index, oled_busy

    if oled_busy:                          # ── NEW ──
        return

    if sonar_stopped:
        stop_motors()
        leds_solid()
        return

    lv = ir_left.read_u16()  * 3.3 / 65535
    rv = ir_right.read_u16() * 3.3 / 65535
    left_v   = round(lv, 3)
    right_v  = round(rv, 3)
    left_on  = lv >= THRESHOLD
    right_on = rv >= THRESHOLD

    if left_on and right_on:
        stop_count += 1
        if stop_count >= STOP_CONFIRM:
            stop_motors()
            stopped = True
            status  = "STOPPED"
            arrow   = "  X  "
            leds_solid()
        else:
            status = "STRAIGHT"
            arrow  = "  ^  "
            drive(90, BALANCE)

    elif stopped:
        if not left_on or not right_on:
            stopped    = False
            stop_count = 0
            drive(90, BALANCE)

    elif not left_on and not right_on:
        stop_count = 0
        status     = "LOST"
        arrow      = "  ?  "
        drive(90, BALANCE, speed=int(SPEED * 0.6))

    elif left_on and not right_on:
        stop_count = 0
        STEERING   = 90 - TURN
        status     = "LEFT"
        arrow      = " <   "
        drive(STEERING, BALANCE, speed=int(SPEED * SLOW_FACTOR))

    elif right_on and not left_on:
        stop_count = 0
        STEERING   = 90 + TURN
        status     = "RIGHT"
        arrow      = "   > "
        drive(STEERING, BALANCE, speed=int(SPEED * SLOW_FACTOR))

    else:
        stop_count = 0
        STEERING   = 90
        status     = "STRAIGHT"
        arrow      = "  ^  "
        drive(STEERING, BALANCE)

    if not stopped:
        leds_off()
        leds[led_index].value(1)
        led_index = (led_index + 1) % 4

timer = Timer(-1)
timer.init(period=20, mode=Timer.PERIODIC, callback=robot_tick)

print("=== LINE FOLLOWER ===")

note_index = 0
oled_cycle = 0

while True:
    dist = get_distance()
    if dist <= SONAR_STOP:
        sonar_stopped = True
        stop_motors()
        status = "OBSTACLE"
        arrow  = "  !  "
        leds_solid()
    else:
        sonar_stopped = False

    note_name = melody[note_index]
    duration  = lengths[note_index]
    freq      = notes[note_name]
    if MUSIC:
        buzzer.freq(int(freq))
        buzzer.duty_u16(32768)
        time.sleep(duration * 0.9)
        buzzer.duty_u16(0)
        time.sleep(duration * 0.1)
    else:
        buzzer.duty_u16(0)
        time.sleep(duration * 0.9)
        time.sleep(duration * 0.1)

    note_index = (note_index + 1) % len(melody)

    oled_cycle += 1
    if oled_cycle >= 3:
        oled_busy = True                   # ── NEW ──
        update_oled(status, arrow, left_on, right_on, left_v, right_v, STEERING)
        oled_busy = False                  # ── NEW ──
        oled_cycle = 0