from machine import Pin, ADC, I2C, PWM
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

buzzer = PWM(Pin(7))                          # Passive buzzer on GP7 for song playback

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
    try:
        from sh1106 import SH1106_I2C                 # Import OLED driver only if device is found
        addr = devices[0]                             # Use the first detected I2C address
        print("Using device at address:", hex(addr))
        oled = SH1106_I2C(128, 64, i2c, addr=addr)   # Initialize 128x64 OLED display

        # --- Startup Screen 1: Greeting ---
        oled.fill(0)                                  # Clear display buffer
        oled.text("Good evening,", 0, 0)
        oled.text("sir.", 0, 12)
        oled.show()                                   # Push buffer to screen
        time.sleep(2)

        # --- Startup Screen 2: System Status ---
        oled.fill(0)
        oled.text("JARVIS online.", 0, 0)
        oled.text("All systems", 0, 16)
        oled.text("gucchi.", 0, 28)
        oled.show()
        time.sleep(2)

        # --- Startup Screen 3: Mode Announcement ---
        oled.fill(0)
        oled.text("Debugging mode", 0, 0)
        oled.text("engaged.", 0, 12)
        oled.text("Loading... >:)", 0, 28)
        oled.show()
        time.sleep(3)

    except Exception as e:
        print("OLED startup failed:", e)              # Reveals silent crash reason
        oled = None

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

# =============================================================
# --- Song of Storms: Note Definitions ---
# =============================================================
note_freqs = { 
    'D':  293.66,
    'E':  329.63,
    'F':  349.23,
    'G':  392.00,
    'A':  440.00,
    'Bb': 466.16,
    'C':  523.25,
}

# --- Tempo definitions based on 180 BPM ---
BPM = 180
Q   = 60 / BPM                                   # Quarter note duration in seconds
E   = Q / 2                                       # Eighth note
H   = Q * 2                                       # Half note
DQ  = Q * 1.5                                     # Dotted quarter note

# --- Melody and matching durations for Song of Storms ---
melody = [
    'D',  'F',  'D',                              # Main motif
    'D',  'F',  'D',                              # Repeat of motif
    'E',  'E',                                    # Rising step
    'C',  'C',                                    # Falling step
    'A',                                          # Anchor note held
    'D',  'F',  'D',                              # Motif again
    'D',  'F',  'D',                              # Repeat
    'E',  'G',  'E',                              # Second phrase rising
    'C',  'C',                                    # Falling back
    'A',                                          # Anchor held
    'F',  'F',  'G',  'F',  'E',                 # Running melody passage
    'D',  'E',  'F',  'A',                        # Ascending run
    'D',  'C',  'A',                              # Descending resolution
    'F',  'F',  'G',  'F',  'E',                 # Running passage repeat
    'D',  'E',  'F',  'A',                        # Ascending run repeat
    'D',  'C',  'A',                              # Final resolution
]

lengths = [
    E,  E,  Q,                                    # Main motif
    E,  E,  Q,                                    # Repeat
    E,  E,                                        # Rising
    E,  E,                                        # Falling
    H,                                            # Anchor held
    E,  E,  Q,                                    # Motif again
    E,  E,  Q,                                    # Repeat
    E,  E,  E,                                    # Second phrase
    E,  E,                                        # Falling
    H,                                            # Anchor held
    E,  E,  E,  E,  E,                           # Running passage
    E,  E,  E,  DQ,                              # Ascending run
    E,  E,  H,                                    # Resolution
    E,  E,  E,  E,  E,                           # Running repeat
    E,  E,  E,  DQ,                              # Ascending repeat
    E,  E,  H,                                    # Final resolution
]

# =============================================================
# --- Play a Single Note ---
# =============================================================
def play_note(freq, duration):
    buzzer.freq(int(freq))                        # Set PWM to note frequency
    buzzer.duty_u16(32768)                        # 50% duty cycle for clean tone
    time.sleep(duration * 0.9)                    # Play for 90% of duration
    buzzer.duty_u16(0)                            # Silence between notes
    time.sleep(duration * 0.1)                    # 10% gap so notes don't blur together

# =============================================================
# --- Update OLED Display ---
# =============================================================
def update_display(line_str, voltage, distance):
    if not oled:
        return                                    # Skip if no OLED detected

    oled.fill(0)                                  # Clear screen before redrawing

    # Draw sensor readings as text
    oled.text(line_str, 0, 0)
    oled.text("Voltage: " + str(voltage) + "V", 0, 12)

    # Build and draw distance string
    if distance is None:
        dist_str = "Dist: Out of Range"           # No valid echo received
        dist_bar = 0
    else:
        dist_str = "Dist: " + str(distance) + " cm"
        dist_bar = min(distance, 30)              # Cap bar at 30cm max
    oled.text(dist_str, 0, 24)

    # Draw distance bar graph scaled to 128px wide for 0–30cm range
    bar_width = dist_bar * 128 // 30
    oled.text("0cm",  0,  38)
    oled.text("30cm", 88, 38)
    oled.hline(0, 50, 128, 1)                     # Baseline for bar graph
    oled.fill_rect(0, 52, bar_width, 8, 1)        # Filled bar representing distance

    # --- Rotated "FORD" text anchored to top-right corner ---
    word = "FORD"
    fw = len(word) * 8                            # Width of text in pixels (8px per char)
    fh = 8                                        # Height of one text row in pixels

    # Allocate buffer and wrap in FrameBuffer to render text into
    buf = bytearray(fw * fh // 8 + 1)
    fb  = framebuf.FrameBuffer(buf, fw, fh, framebuf.MONO_HLSB)
    fb.fill(0)                                    # Clear temp buffer
    fb.text(word, 0, 0, 1)                        # Render word into temp buffer

    # Blit pixel by pixel rotated 90 degrees clockwise onto main display
    for x in range(fw):                           # x walks along the word left to right
        for y in range(fh):                       # y walks down the 8px glyph height
            byte_index = (y * fw + x) // 8        # Which byte this pixel lives in
            bit_index  = 7 - ((y * fw + x) % 8)  # Which bit within that byte
            pixel = (buf[byte_index] >> bit_index) & 1  # Extract the bit

            if pixel:                             # Only plot lit pixels
                dx = 127 - y                      # Right edge column
                dy = x                            # Top of screen row
                oled.pixel(dx, dy, 1)             # Plot rotated pixel

    oled.show()                                   # Push frame to display

# =============================================================
# --- Read Sensors and Update LED ---
# =============================================================
def read_sensors():
    reading  = analog.read_u16()                  # Raw 16-bit ADC reading (0-65535)
    voltage  = round(reading * 3.3 / 65535, 2)   # Convert to voltage (0-3.3V)
    distance = get_distance()                     # Get ultrasonic distance in cm

    # High voltage means sensor sees a dark/black surface
    if voltage > 1.5:
        line_str = "Line: BLACK"
        led.value(1)                              # Turn LED on for black line
    else:
        line_str = "Line: WHITE"
        led.value(0)                              # Turn LED off for white surface

    print(line_str, "|", "Dist:", distance, "| Voltage:", voltage, "V")
    return line_str, voltage, distance

time.sleep(2)                                     # Brief pause before starting main loop

# =============================================================
# --- Main Loop ---
# --- Plays one note per iteration so sensors stay responsive ---
# =============================================================
note_index = 0                                    # Track position in melody across loop iterations

while True:
    # --- Play one note per loop iteration ---
    note_name = melody[note_index]                # Get current note name
    duration  = lengths[note_index]               # Get matching duration
    freq      = note_freqs[note_name]             # Look up frequency in Hz
    play_note(freq, duration)                     # Play the note on the buzzer

    # --- Advance to next note, loop back to start when melody finishes ---
    note_index = (note_index + 1) % len(melody)

    # --- Read sensors and update display after each note ---
    line_str, voltage, distance = read_sensors()
    update_display(line_str, voltage, distance)