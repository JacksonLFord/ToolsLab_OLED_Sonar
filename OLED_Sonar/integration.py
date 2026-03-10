from machine import Pin, ADC, I2C
from utime import sleep, ticks_ms, ticks_diff
import time

# =============================================================
# --- Pin Setup ---
# =============================================================
analog  = ADC(Pin(28))                        # Analog input from line sensor (GP28, ADC2)
digital = Pin(15, Pin.IN, Pin.PULL_DOWN)      # Digital input from line sensor (GP15)
led     = Pin(22, Pin.OUT, 0)                 # LED output (GP22), starts OFF

Trig = Pin(16, Pin.OUT, 0)                    # Ultrasonic trigger pin (GP16), starts LOW
Echo = Pin(17, Pin.IN, 0)                     # Ultrasonic echo pin (GP17)

# =============================================================
# --- Ultrasonic Sensor Constants ---
# =============================================================
SOUNDVELOCITY       = 340
MAXIMUM_DISTANCE_CM = 200
MAXIMUM_TIME        = MAXIMUM_DISTANCE_CM * 2 * 10000 // SOUNDVELOCITY

# =============================================================
# --- I2C + OLED Setup ---
# =============================================================
i2c     = I2C(0, sda=Pin(20), scl=Pin(21), freq=400000)
devices = i2c.scan()
print("I2C devices found:", [hex(d) for d in devices])

if not devices:
    print()
    print("ERROR: No I2C devices detected!")
    print()
    print("Troubleshooting checklist:")
    print("  1. Check wiring:")
    print("     VCC -> 3V3 (pin 36)")
    print("     GND -> GND (pin 23)")
    print("     SDA -> GP20 (pin 26)")
    print("     SCL -> GP21 (pin 27)")
    print("  2. Make sure connections are solid (not loose)")
    print("  3. Some displays use 5V, try VCC -> VBUS (pin 40)")
    print("  4. Check if SDA/SCL labels are swapped on your board")
    oled = None

else:
    from sh1106 import SH1106_I2C
    addr = devices[0]
    print("Using device at address:", hex(addr))
    oled = SH1106_I2C(128, 64, i2c, addr=addr)

    # --- Startup Screen 1: Greeting ---
    oled.fill(0)
    oled.text("Good evening,", 0, 0)
    oled.text("sir.", 0, 12)
    oled.show()
    sleep(2)

    # --- Startup Screen 2: System Status ---
    oled.fill(0)
    oled.text("JARVIS online.", 0, 0)
    oled.text("All systems", 0, 16)
    oled.text("gucchi.", 0, 28)
    oled.show()
    sleep(2)

    # --- Startup Screen 3: Mode Announcement ---
    oled.fill(0)
    oled.text("Debugging mode", 0, 0)
    oled.text("engaged.", 0, 12)
    oled.text("Loading... >:)", 0, 28)
    oled.show()
    sleep(3)

# =============================================================
# --- Ultrasonic Distance Function ---
# =============================================================
def get_distance():
    Trig.value(1)
    time.sleep_us(10)
    Trig.value(0)
    startWait = time.ticks_us()
    while not Echo.value():
        if time.ticks_diff(time.ticks_us(), startWait) > MAXIMUM_TIME:
            return None
    pingStart = time.ticks_us()
    while Echo.value():
        pass
    pingStop = time.ticks_us()
    distanceTime = time.ticks_diff(pingStop, pingStart) // 2
    return int(distanceTime * SOUNDVELOCITY / 10000)

# =============================================================
# --- Explosion Animation ---
# =============================================================
def draw_explosion():
    cx, cy = 64, 30

    # --- Frame 1: Small circle ---
    oled.fill(0)
    oled.text("** BOOM!! **", 16, 0)
    oled.ellipse(cx, cy, 5, 5, 1)
    oled.show()
    sleep(0.1)

    # --- Frame 2: Medium burst with spikes ---
    oled.fill(0)
    oled.text("** BOOM!! **", 16, 0)
    oled.ellipse(cx, cy, 10, 10, 1)
    oled.vline(cx,      cy - 18, 8, 1)   # up
    oled.vline(cx,      cy + 10, 8, 1)   # down
    oled.hline(cx - 18, cy,      8, 1)   # left
    oled.hline(cx + 10, cy,      8, 1)   # right
    oled.show()
    sleep(0.1)

    # --- Frame 3: Large burst with longer spikes ---
    oled.fill(0)
    oled.text("** BOOM!! **", 16, 0)
    oled.ellipse(cx, cy, 16, 16, 1)
    oled.vline(cx,      cy - 26, 10, 1)  # up
    oled.vline(cx,      cy + 16, 10, 1)  # down
    oled.hline(cx - 26, cy,      10, 1)  # left
    oled.hline(cx + 16, cy,      10, 1)  # right
    oled.show()
    sleep(0.1)

    # --- Frame 4: Filled explosion peak ---
    oled.fill(0)
    oled.text("** BOOM!! **", 16, 0)
    for r in range(1, 20):
        oled.ellipse(cx, cy, r, r, 1)
    oled.show()
    sleep(0.15)

    # --- Frame 5: Flash white ---
    oled.fill(1)
    oled.show()
    sleep(0.05)

    # --- Frame 6: Shrinking rings ---
    for r in [18, 14, 10, 6, 3]:
        oled.fill(0)
        oled.text("** BOOM!! **", 16, 0)
        oled.ellipse(cx, cy, r, r, 1)
        oled.show()
        sleep(0.08)

    # --- Frame 7: Aftermath ---
    oled.fill(0)
    oled.text("...too close,", 16, 20)
    oled.text("   sir.", 16, 36)
    oled.show()
    sleep(2)

time.sleep(2)

# =============================================================
# --- Main Loop ---
# =============================================================
while True:
    # --- Read Sensors ---
    reading  = analog.read_u16()
    voltage  = round(reading * 3.3 / 65535, 2)
    distance = get_distance()

    # --- Line Sensor Logic ---
    if voltage > 1.5:
        line_str = "Line: BLACK"
        led.value(1)
    else:
        line_str = "Line: WHITE"
        led.value(0)

    # --- Distance String ---
    if distance is None:
        dist_str = "Dist: Out of Range"
        dist_bar = 0
    else:
        dist_str = "Dist: " + str(distance) + " cm"
        dist_bar = min(distance, 30)

    # --- Proximity LED warning ---
    if distance is not None and distance < 10:
        led.value(1)

    # --- BOOM if 1cm or less ---
    if distance is not None and distance <= 1:
        print("*** BOOM *** Object at", distance, "cm!")
        led.value(1)
        if oled:
            draw_explosion()
        led.value(0)
        time.sleep_ms(500)
        continue    # Skip normal display update this cycle

    # --- Print to Terminal ---
    print(line_str, "|", dist_str, "| Voltage:", voltage, "V")

 # --- OLED Display ---
    if oled:
        oled.fill(0)

        oled.text(line_str, 0, 0)
        oled.text("Voltage: " + str(voltage) + "V", 0, 12)
        oled.text(dist_str, 0, 24)

        dist_bar  = min(distance, 30) if distance else 0
        bar_width = dist_bar * 128 // 30
        oled.text("0cm",  0,  38)
        oled.text("30cm", 88, 38)
        oled.hline(0, 50, 128, 1)
        oled.fill_rect(0, 52, bar_width, 8, 1)

        oled.show()

    time.sleep_ms(500)
