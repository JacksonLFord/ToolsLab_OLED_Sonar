from machine import Pin, ADC, PWM, I2C
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

# ── OLED ──
i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)
devices = i2c.scan()
if devices:
    from sh1106 import SH1106_I2C
    oled = SH1106_I2C(128, 64, i2c, addr=devices[0])
else:
    oled = None

# ── TUNE THESE ──
SPEED       = 50
BALANCE     = 55
TURN        = 55
THRESHOLD   = 3.25
SLOW_FACTOR = 0.8   # 20% speed reduction on turns

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

    return left_speed, right_speed

def stop():
    gp10.duty_u16(0)
    gp13.duty_u16(0)
    gp11.value(0)
    gp12.value(0)

def read_ir():
    left_v  = ir_left.read_u16()  * 3.3 / 65535
    right_v = ir_right.read_u16() * 3.3 / 65535
    left_on  = left_v  >= THRESHOLD
    right_on = right_v >= THRESHOLD
    return left_on, right_on, round(left_v, 3), round(right_v, 3)

def update_oled(status, arrow, left_on, right_on, left_v, right_v, steering):
    if not oled:
        return
    oled.fill(0)
    oled.text(arrow,  52, 0)
    oled.text(status,  0, 10)
    oled.text("Spd:" + str(SPEED) + " Bal:" + str(BALANCE), 0, 20)

    oled.rect(10, 32, 20, 16, 1)
    if left_on:
        oled.fill_rect(10, 32, 20, 16, 1)
        oled.text("B", 16, 35, 0)
    else:
        oled.text("W", 16, 35, 1)
    oled.text(str(left_v),  0, 50)

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

print("=== LINE FOLLOWER ===")

STEERING = 90
cycle    = 0

while True:
    left_on, right_on, left_v, right_v = read_ir()

    if left_on and right_on:
        stop()
        status = "STOPPED"
        arrow  = "  X  "

    elif not left_on and not right_on:
        STEERING = 90
        status   = "LOST"
        arrow    = "  ?  "
        drive(STEERING, BALANCE)

    elif left_on and not right_on:
        STEERING = 90 - TURN
        status   = "LEFT"
        arrow    = " <   "
        drive(STEERING, BALANCE, speed=int(SPEED * SLOW_FACTOR))

    elif right_on and not left_on:
        STEERING = 90 + TURN
        status   = "RIGHT"
        arrow    = "   > "
        drive(STEERING, BALANCE, speed=int(SPEED * SLOW_FACTOR))

    else:
        STEERING = 90
        status   = "STRAIGHT"
        arrow    = "  ^  "
        drive(STEERING, BALANCE)

    cycle += 1
    if cycle >= 10:
        update_oled(status, arrow, left_on, right_on, left_v, right_v, STEERING)
        cycle = 0

    print(f"{status} | L:{left_v}V({'B' if left_on else 'W'}) R:{right_v}V({'B' if right_on else 'W'})")

    time.sleep(0.01)