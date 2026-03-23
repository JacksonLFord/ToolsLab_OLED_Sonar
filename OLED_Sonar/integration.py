from machine import Pin, ADC, I2C
import framebuf
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
SOUNDVELOCITY       = 340                     # Speed of sound in m/s
MAXIMUM_DISTANCE_CM = 200                     # Max measurable distance in cm
MAXIMUM_TIME        = MAXIMUM_DISTANCE_CM * 2 * 10000 // SOUNDVELOCITY  # Timeout in microseconds

# =============================================================
# --- I2C + OLED Setup ---
# =============================================================
i2c     = I2C(0, sda=Pin(20), scl=Pin(21), freq=400000)  # I2C bus on GP20/GP21 at 400kHz
devices = i2c.scan()                          # Scan for connected I2C devices
print("I2C devices found:", [hex(d) for d in devices])

if not devices:
    # No I2C device found — print troubleshooting steps and disable OLED
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
    from sh1106 import SH1106_I2C                 # Import OLED driver only if device is found
    addr = devices[0]                             # Use the first detected I2C address
    print("Using device at address:", hex(addr))
    oled = SH1106_I2C(128, 64, i2c, addr=addr)   # Initialize 128x64 OLED display

    # --- Startup Screen 1: Greeting ---
    oled.fill(0)                                  # Clear display buffer
    oled.text("Good evening,", 0, 0)
    oled.text("sir.", 0, 12)
    oled.show()                                   # Push buffer to screen
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
    # Send a 10us HIGH pulse on Trig to start measurement
    Trig.value(1)
    time.sleep_us(10)
    Trig.value(0)

    # Wait for Echo to go HIGH (pulse start), with timeout guard
    startWait = time.ticks_us()
    while not Echo.value():
        if time.ticks_diff(time.ticks_us(), startWait) > MAXIMUM_TIME:
            return None                           # Object out of range or no echo received

    # Measure how long Echo stays HIGH — this is the round-trip time
    pingStart = time.ticks_us()
    while Echo.value():
        pass
    pingStop = time.ticks_us()

    # Convert round-trip time to distance in cm
    distanceTime = time.ticks_diff(pingStop, pingStart) // 2
    return int(distanceTime * SOUNDVELOCITY / 10000)

time.sleep(2)                                     # Brief pause before starting main loop

# =============================================================
# --- Main Loop ---
# =============================================================
while True:
    # --- Read Sensors ---
    reading  = analog.read_u16()                  # Raw 16-bit ADC reading (0–65535)
    voltage  = round(reading * 3.3 / 65535, 2)   # Convert to voltage (0–3.3V)
    distance = get_distance()                     # Get ultrasonic distance in cm

    # --- Line Sensor Logic ---
    # High voltage means the sensor sees a dark/black surface
    if voltage > 1.5:
        line_str = "Line: BLACK"
        led.value(1)                              # Turn LED on for black line
    else:
        line_str = "Line: WHITE"
        led.value(0)                              # Turn LED off for white surface

    # --- Distance String ---
    if distance is None:
        dist_str = "Dist: Out of Range"           # No valid echo received
        dist_bar = 0
    else:
        dist_str = "Dist: " + str(distance) + " cm"
        dist_bar = min(distance, 30)              # Cap bar at 30cm max

    # --- Print to Terminal ---
    print(line_str, "|", dist_str, "| Voltage:", voltage, "V")

    # --- OLED Display ---
    if oled:
        oled.fill(0)                              # Clear screen before redrawing

        # Draw sensor readings as text
        oled.text(line_str, 0, 0)
        oled.text("Voltage: " + str(voltage) + "V", 0, 12)
        oled.text(dist_str, 0, 24)

        # Draw distance bar graph scaled to 128px wide for 0–30cm range
        dist_bar  = min(distance, 30) if distance else 0
        bar_width = dist_bar * 128 // 30
        oled.text("0cm",  0,  38)
        oled.text("30cm", 88, 38)
        oled.hline(0, 50, 128, 1)                 # Baseline for bar graph
        oled.fill_rect(0, 52, bar_width, 8, 1)    # Filled bar representing distance

        # --- Rotated "FORD" text on right edge ---
        # Draw "FORD" into a small framebuffer, then blit it rotated 90 degrees
        word = "FORD"
        fw = len(word) * 8                        # Width of text in pixels (8px per char)
        fh = 8                                    # Height of one text row in pixels

        # Allocate a byte buffer large enough to hold the word as a 1-bit bitmap
        # +1 ensures no off-by-one underflow if fw*fh isn't divisible by 8
        buf = bytearray(fw * fh // 8 + 1)

        # Wrap buffer in a FrameBuffer so we can use .text() to draw into it
        fb  = framebuf.FrameBuffer(buf, fw, fh, framebuf.MONO_HLSB)
        fb.fill(0)                                # Clear the temp buffer before drawing
        fb.text(word, 0, 0, 1)                    # Render "FORD" at top-left of temp buffer

        # --- Blit rotated 90 degrees clockwise, anchored to top-right corner ---
        # Normal orientation: word runs left→right, pixels at (x, y)
        # After 90° CW rotation: x becomes the new row (dy), y becomes the new col from right (dx)
        # So: dx = 127 - y  (y=0 maps to col 127, the rightmost column)
        #     dy = x         (x=0 maps to row 0, the top of the screen)
        for x in range(fw):                       # x walks along the word left→right
            for y in range(fh):                   # y walks down the 8px tall glyph row

                # --- Extract the pixel at (x, y) from the flat MONO_HLSB buffer ---
                # MONO_HLSB packs pixels left-to-right, MSB first, row by row
                byte_index = (y * fw + x) // 8        # Which byte this pixel lives in
                bit_index  = 7 - ((y * fw + x) % 8)  # Which bit within that byte (MSB=left)
                pixel = (buf[byte_index] >> bit_index) & 1  # Extract the bit (0 or 1)

                if pixel:                         # Skip dark/off pixels — only draw lit ones
                    dx = 127 - y                  # Map glyph row → screen column (right edge)
                    dy = x                        # Map glyph column → screen row (top of screen)
                    oled.pixel(dx, dy, 1)         # Plot the rotated pixel onto the main display

        oled.show()                               # Push updated frame to display

    time.sleep_ms(500)                            # Wait 500ms before next reading