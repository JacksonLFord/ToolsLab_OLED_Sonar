# Import hardware abstraction classes from MicroPython's machine module
from machine import Pin, ADC, PWM, I2C, Timer
# time module provides sleep and microsecond tick functions
import time

# ── IR Sensors ──
# ADC reads the analog voltage output of each IR reflectance sensor
# Pin 26 = left sensor, Pin 27 = right sensor
ir_left  = ADC(Pin(26))
ir_right = ADC(Pin(27))

# ── Motors ──
# gp10 and gp13 are PWM channels that set each motor's speed
gp10 = PWM(Pin(10))
gp11 = Pin(11, Pin.OUT)
# gp11 and gp12 are direction control pins for the left motor H-bridge
gp12 = Pin(12, Pin.OUT)
gp13 = PWM(Pin(13))
# 1 kHz PWM frequency gives smooth motor control without audible whine
gp10.freq(1000)
gp13.freq(1000)

# ── Buzzer ──
# PWM on the buzzer pin allows the frequency to be set per musical note
buzzer = PWM(Pin(22))

# ── Sonar ──
# trig is an output that sends the ultrasonic pulse
trig = Pin(14, Pin.OUT)
# echo is an input that goes high for the duration of the return pulse
echo = Pin(15, Pin.IN)

# ── LEDs ──
# Four LEDs on consecutive pins; used as a running chaser to show activity
leds = [Pin(6, Pin.OUT), Pin(7, Pin.OUT), Pin(8, Pin.OUT), Pin(9, Pin.OUT)]

# ── OLED ──
# I2C bus 1 uses SDA on pin 2 and SCL on pin 3 at 400 kHz (fast mode)
i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)
# Scan the bus to find the OLED's I2C address automatically
devices = i2c.scan()
# Print found addresses to the REPL so the address can be verified during setup
print(devices)
# Only import the driver and create the display object if a device was detected
if devices:
    from sh1106 import SH1106_I2C
    # 128x64 pixel SH1106 display; address taken from the scan result
    oled = SH1106_I2C(128, 64, i2c, addr=devices[0])
else:
    # If no display is connected, set oled to None so callers can guard against it
    oled = None

# ── TUNE THESE ──
# SPEED sets the robot's forward drive level as a percentage of full power
SPEED        = 83
# BALANCE compensates for motors that run at different speeds; >50 biases left
BALANCE      = 57
# TURN is the angular offset added/subtracted from 90° when correcting direction
TURN         = 85
# THRESHOLD is the IR voltage (V) above which the surface is considered black
THRESHOLD    = 3.3
# SLOW_FACTOR reduces speed during turns so the robot doesn't overshoot the line
SLOW_FACTOR  = 0.9
# STOP_CONFIRM is how many consecutive ticks both sensors must be black to stop
STOP_CONFIRM = 3
# SONAR_STOP is the obstacle distance in cm that triggers an emergency halt
SONAR_STOP   = 20
# Set MUSIC = False to disable the buzzer without affecting loop timing
MUSIC        = True

# ── Song of Storms ──
# Dictionary mapping note letter names to their frequencies in Hz
notes = {
    'D':  293.66,
    'E':  329.63,
    # F is 349.23 Hz, approximately F4 on a standard piano
    'F':  349.23,
    'G':  392.00,
    'A':  440.00,
    # Bb (B-flat) sits between A and B
    'Bb': 466.16,
    'C':  523.25,
}

# BPM controls the overall playback speed of the melody
BPM = 80
# Q is one beat (quarter note) expressed in seconds
Q   = 60 / BPM   # Quarter note duration in seconds
# E is half a beat; eighth notes are the most common duration in this melody
E   = Q / 2      # Eighth note
# H is two beats; used for held notes at phrase endings
H   = Q * 2      # Half note
# DQ is one-and-a-half beats; a dotted quarter note
DQ  = Q * 1.5    # Dotted quarter note

# melody lists note names in the order they are played
# Each entry corresponds to the same index in the lengths list
melody = [
    'D',  'F',  'D',
    # Opening motif repeated
    'D',  'F',  'D',
    'E',  'E',
    'C',  'C',
    # Long held A marks the end of the first phrase
    'A',
    'D',  'F',  'D',
    'D',  'F',  'D',
    # Second phrase introduces G
    'E',  'G',  'E',
    'C',  'C',
    'A',
    # Third phrase: faster running passage
    'F',  'F',  'G',  'F',  'E',
    'D',  'E',  'F',  'A',
    'D',  'C',  'A',
    # Fourth phrase mirrors the third
    'F',  'F',  'G',  'F',  'E',
    'D',  'E',  'F',  'A',
    'D',  'C',  'A',
]

# lengths holds the duration of each note in seconds, index-matched to melody
lengths = [
    E,  E,  Q,
    E,  E,  Q,
    # Two eighth notes
    E,  E,
    E,  E,
    # Half note — held
    H,
    E,  E,  Q,
    E,  E,  Q,
    E,  E,  E,
    E,  E,
    H,
    # Running eighth notes in the third phrase
    E,  E,  E,  E,  E,
    # Dotted quarter creates a lilting rhythm
    E,  E,  E,  DQ,
    E,  E,  H,
    E,  E,  E,  E,  E,
    E,  E,  E,  DQ,
    # Final half note ends the loop
    E,  E,  H,
]

# ── Shared state ──
# STEERING holds the current servo/drive angle; 90 = dead ahead
STEERING      = 90
# stop_count accumulates ticks where both sensors see black simultaneously
stop_count    = 0
# status is a short string written to the OLED to show the current behaviour
status        = "STRAIGHT"
# arrow is a text-art direction indicator shown at the top of the OLED
arrow         = "  ^  "
# left_v and right_v store the most recent IR sensor readings in volts
left_v        = 0.0
right_v       = 0.0
# left_on / right_on are True when the corresponding sensor is over a black line
left_on       = False
right_on      = False
# stopped becomes True once the robot has confirmed a stop line and halted
stopped       = False
# sonar_stopped is set by the main loop when an obstacle is within SONAR_STOP cm
sonar_stopped = False
# oled_busy prevents the ISR from running while the main loop writes to the display
oled_busy     = False          # ── NEW ──
# led_index cycles 0-3 to select which LED in the chaser is currently lit
led_index     = 0

def get_distance():
    # Ensure trig starts low so the rising edge is clean
    trig.value(0)
    # 2 µs low settle time recommended by the HC-SR04 datasheet
    time.sleep_us(2)
    # A 10 µs high pulse on trig fires the ultrasonic burst
    trig.value(1)
    time.sleep_us(10)
    # Return trig low; the sensor now listens for the echo
    trig.value(0)

    # Record the time we start waiting for the echo to go high
    timeout = time.ticks_us()
    # Loop until echo rises, but bail out after 30 ms to prevent a hard hang
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), timeout) > 30000:
            # 999 cm is used as a sentinel meaning "no object detected"
            return 999

    # Capture the timestamp at the moment the echo pulse begins
    start = time.ticks_us()
    # Wait for echo to fall; the pulse width encodes the round-trip travel time
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), start) > 30000:
            return 999

    # Capture the timestamp when the echo pulse ends
    end = time.ticks_us()
    # Distance = (time × speed of sound) / 2; 0.034 cm/µs is the speed of sound
    return (time.ticks_diff(end, start) * 0.034) / 2

def leds_solid():
    # Iterate over all four LED pins and set them high simultaneously
    for led in leds:
        # All LEDs on indicates the robot is stopped or blocked
        led.value(1)

def leds_off():
    # Clear all LEDs before the chaser selects a new active position
    for led in leds:
        led.value(0)

def drive(steering, balance, speed=None):
    # Use the global SPEED constant when the caller does not supply a speed
    if speed is None:
        speed = SPEED
    # Scale the 0-100% speed to the 0-65535 range expected by duty_u16()
    base  = int(speed / 100 * 65535)
    # shift maps balance (0-100) to a correction factor between -1.0 and +1.0
    shift = (balance - 50) / 50.0

    # Positive shift means the left motor is faster so reduce the right
    if shift > 0:
        left_speed  = base
        right_speed = int(base * (1.0 - shift))
    # Negative shift means the right motor is faster so reduce the left
    elif shift < 0:
        left_speed  = int(base * (1.0 + shift))
        right_speed = base
    else:
        # No correction needed; both motors get the same base speed
        left_speed  = base
        right_speed = base

    # normalized maps the steering angle to -1.0 (hard left) to +1.0 (hard right)
    normalized = (steering - 90) / 90.0

    # Turning right: boost the left (outer) motor and slow the right (inner) motor
    if normalized > 0:
        left_speed  = min(65535, int(left_speed * 1.2))
        right_speed = int(right_speed * (1.0 - normalized))
    # Turning left: boost the right (outer) motor and slow the left (inner) motor
    elif normalized < 0:
        right_speed = min(65535, int(right_speed * 1.2))
        left_speed  = int(left_speed  * (1.0 + normalized))

    # Clamp to prevent overflow; duty_u16() requires values in 0-65535
    left_speed  = max(0, min(65535, left_speed))
    right_speed = max(0, min(65535, right_speed))

    # gp11 and gp12 both low sets the H-bridge for forward motion
    gp11.value(0)
    gp12.value(0)
    # Write the calculated duty cycles to drive the motors at the target speed
    gp10.duty_u16(left_speed)
    gp13.duty_u16(right_speed)

def stop_motors():
    # Setting duty to 0 removes all power from both motors
    gp10.duty_u16(0)
    gp13.duty_u16(0)
    # Clearing direction pins ensures the H-bridge outputs are fully inactive
    gp11.value(0)
    gp12.value(0)

def update_oled(status, arrow, left_on, right_on, left_v, right_v, steering):
    # Skip drawing entirely if no display was found during startup
    if not oled:
        return
    # Fill the entire framebuffer with black (0) to erase the previous frame
    oled.fill(0)
    # Draw the direction arrow centered at the top of the screen
    oled.text(arrow, 52, 0)
    # Draw the status label (e.g. "LEFT", "STOPPED") below the arrow
    oled.text(status, 0, 10)
    # Show the live SPEED and BALANCE values for on-the-fly tuning reference
    oled.text("Spd:" + str(int(SPEED)) + " Bal:" + str(int(BALANCE)), 0, 20)

    # Draw a rectangle outline for the left sensor indicator box
    oled.rect(10, 32, 20, 16, 1)
    if left_on:
        # Solid fill indicates the left sensor is over a black line
        oled.fill_rect(10, 32, 20, 16, 1)
        # White "B" on black fill labels the sensor state as Black
        oled.text("B", 16, 35, 0)
    else:
        # Dark "W" on white background labels the sensor state as White
        oled.text("W", 16, 35, 1)
    # Print the actual voltage reading underneath the left sensor box
    oled.text(str(left_v), 0, 50)

    # Mirror the same indicator layout for the right sensor on the other side
    oled.rect(98, 32, 20, 16, 1)
    if right_on:
        oled.fill_rect(98, 32, 20, 16, 1)
        oled.text("B", 104, 35, 0)
    else:
        oled.text("W", 104, 35, 1)
    # Print the right sensor voltage in the lower-right area of the screen
    oled.text(str(right_v), 72, 50)

    # Draw a horizontal rule across the very bottom of the display
    oled.hline(0, 62, 128, 1)
    # Map the steering angle (0-180) to a pixel x-position across the 128px width
    bar_x = steering * 128 // 180
    # Draw a small filled square as the steering position marker
    oled.fill_rect(max(0, bar_x - 2), 59, 4, 4, 1)

    # Flush the completed framebuffer to the physical OLED panel
    oled.show()

def robot_tick(timer):
    # Declare all shared variables as global so the ISR can modify them
    global STEERING, stop_count, status, arrow
    global left_v, right_v, left_on, right_on
    global stopped, sonar_stopped, led_index, oled_busy

    # Guard: if the main loop is writing to the OLED, skip this entire tick
    if oled_busy:                          # ── NEW ──
        return

    # Guard: if an obstacle was detected, keep motors stopped and LEDs on
    if sonar_stopped:
        stop_motors()
        leds_solid()
        return

    # Sample both IR sensors; read_u16() returns 0-65535 proportional to voltage
    lv = ir_left.read_u16()  * 3.3 / 65535
    rv = ir_right.read_u16() * 3.3 / 65535
    # Round to 3 decimal places for readable display on the OLED
    left_v   = round(lv, 3)
    right_v  = round(rv, 3)
    # Compare against THRESHOLD to produce simple boolean line-detection flags
    left_on  = lv >= THRESHOLD
    right_on = rv >= THRESHOLD

    if left_on and right_on:
        # Both sensors black: increment the confirmation counter
        stop_count += 1
        if stop_count >= STOP_CONFIRM:
            # Counter reached the limit — this is a real stop line, not a crossing
            stop_motors()
            stopped = True
            status  = "STOPPED"
            arrow   = "  X  "
            # All LEDs on signals that the robot has intentionally halted
            leds_solid()
        else:
            # Counter not yet reached; keep driving straight through the crossing
            status = "STRAIGHT"
            arrow  = "  ^  "
            drive(90, BALANCE)

    elif stopped:
        # Robot is in the stopped state; only resume if a sensor clears the line
        if not left_on or not right_on:
            # At least one sensor has gone white — safe to start moving again
            stopped    = False
            stop_count = 0
            drive(90, BALANCE)

    elif not left_on and not right_on:
        # Both sensors white: the robot has lost the line entirely
        stop_count = 0
        status     = "LOST"
        # Question mark arrow indicates uncertainty about direction
        arrow      = "  ?  "
        # Drive straight at reduced speed to search for the line
        drive(90, BALANCE, speed=int(SPEED * 0.6))

    elif left_on and not right_on:
        # Left sensor only: the line is to the left, so steer left
        stop_count = 0
        # Subtract TURN from 90° to produce a left-biased steering angle
        STEERING   = 90 - TURN
        status     = "LEFT"
        arrow      = " <   "
        # Reduce speed during the turn to prevent the robot overshooting
        drive(STEERING, BALANCE, speed=int(SPEED * SLOW_FACTOR))

    elif right_on and not left_on:
        # Right sensor only: the line is to the right, so steer right
        stop_count = 0
        # Add TURN to 90° to produce a right-biased steering angle
        STEERING   = 90 + TURN
        status     = "RIGHT"
        arrow      = "   > "
        drive(STEERING, BALANCE, speed=int(SPEED * SLOW_FACTOR))

    else:
        # Fallthrough: robot is centred on the line, drive straight ahead
        stop_count = 0
        STEERING   = 90
        status     = "STRAIGHT"
        arrow      = "  ^  "
        drive(STEERING, BALANCE)

    # Update the LED chaser only while the robot is moving, not while stopped
    if not stopped:
        # Turn all LEDs off first so only one is ever lit at a time
        leds_off()
        # Light the LED at the current index position
        leds[led_index].value(1)
        # Advance the index, wrapping from 3 back to 0
        led_index = (led_index + 1) % 4

# Timer(-1) creates a virtual (software) timer not tied to a specific hardware peripheral
timer = Timer(-1)
# period=20 fires the callback every 20 ms; PERIODIC keeps it repeating indefinitely
timer.init(period=20, mode=Timer.PERIODIC, callback=robot_tick)

# Confirm successful startup on the REPL console
print("=== LINE FOLLOWER ===")

# note_index tracks the current position in the melody and lengths arrays
note_index = 0
# oled_cycle counts main-loop iterations so the display refreshes every 3rd note
oled_cycle = 0

while True:
    # Measure the distance to any object in front of the robot
    dist = get_distance()
    if dist <= SONAR_STOP:
        # Object is too close — set the shared flag so the ISR stops the motors
        sonar_stopped = True
        stop_motors()
        status = "OBSTACLE"
        # Exclamation arrow warns that forward motion is blocked
        arrow  = "  !  "
        leds_solid()
    else:
        # Path is clear — clear the flag so the ISR resumes normal operation
        sonar_stopped = False

    # Retrieve the note name and duration for this step in the melody
    note_name = melody[note_index]
    duration  = lengths[note_index]
    # Look up the frequency in Hz for the current note name
    freq      = notes[note_name]
    if MUSIC:
        # Set the buzzer to the note frequency
        buzzer.freq(int(freq))
        # 50% duty cycle (32768 of 65535) gives a clear square-wave tone
        buzzer.duty_u16(32768)
        # Hold the note for 90% of its duration
        time.sleep(duration * 0.9)
        # Silence the buzzer for the remaining 10% to create note separation
        buzzer.duty_u16(0)
        time.sleep(duration * 0.1)
    else:
        # Keep the buzzer silent but preserve the same timing as when music is on
        buzzer.duty_u16(0)
        # 90% + 10% sleep keeps the loop cadence identical regardless of MUSIC flag
        time.sleep(duration * 0.9)
        time.sleep(duration * 0.1)

    # Move to the next note; modulo wraps back to 0 after the last note
    note_index = (note_index + 1) % len(melody)

    # Increment the OLED refresh counter each time a note finishes
    oled_cycle += 1
    if oled_cycle >= 3:
        # Signal to the ISR that the display bus is about to be used
        oled_busy = True                   # ── NEW ──
        # Redraw the full OLED display with the latest shared state values
        update_oled(status, arrow, left_on, right_on, left_v, right_v, STEERING)
        # Release the flag so the ISR can resume normal operation
        oled_busy = False                  # ── NEW ──
        # Reset the counter to schedule the next refresh in 3 notes' time
        oled_cycle = 0