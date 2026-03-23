from machine import Pin, ADC, I2C, PWM
import framebuf
from utime import sleep, ticks_ms, ticks_diff
import time
# Importing all of the dependency modules at the top for better organization and readability

#Pins for sensors and actuators
analog  = ADC(Pin(28))
digital = Pin(15, Pin.IN, Pin.PULL_DOWN)
led     = Pin(22, Pin.OUT, 0)
buzzer = PWM(Pin(7))

#Pins of I2C
Trig = Pin(16, Pin.OUT, 0)
Echo = Pin(17, Pin.IN, 0)

#These are constants used to calculate distanc on the sensor.
SOUNDVELOCITY       = 340
MAXIMUM_DISTANCE_CM = 200
MAXIMUM_TIME        = MAXIMUM_DISTANCE_CM * 2 * 10000 // SOUNDVELOCITY

#This is the stup for the I2C communication system. It declares the pins where its listening on and on what frequency is scans on.
i2c     = I2C(0, sda=Pin(20), scl=Pin(21), freq=400000)
devices = i2c.scan() #It begins scanning for devices.
print("I2C devices found:", [hex(d) for d in devices]) #Its a confirmation message for the I2C setup.

if not devices:
    print("FAILED to scan the I2C")
    oled = None #A catch error style of handling failure of the I2C setup.
else: #If the I2C setup is successful.
    try:
        from sh1106 import SH1106_I2C #Importing the sh1106 library we ported onto th pi
        addr = devices[0] #The only device on I2C is the OLED so we just grab the only address that we find on the I2C
        oled = SH1106_I2C(128, 64, i2c, addr=addr) #The I2C address. If the address doesnt exist these lines of code should throw an error and b caught.

        oled.fill(0)#Clears the screen to black before we start writing to it.
        oled.text("Starting up...", 0, 0) #Writes a startup messag. 
        oled.show()# Displays the mssage to the LCD
        time.sleep(3) # Waits to to continue so that the user can read the message
    except Exception as e:
        #This should only throw an error if the I2C setup was successful but the OLED display failed to initialize for some reason. It catches the error and prints it to the console for debugging.
        print("OLED startup failed:", e)
        oled = None

def get_distance(): #Gets distance function tht will be used to read the distance from the ultrasonic sensor. It uses the trig and echo pins to send out a ping and listen for the echo and then calculates the distance based on the time it took for the echo to return.
    Trig.value(1) #This is sending out a trigger signal to be read to gauge distance.
    time.sleep_us(10)
    Trig.value(0) #This is th end of the trigger signal, it only ran for 10 microseconds.

    startWait = time.ticks_us()
    while not Echo.value():
        if time.ticks_diff(time.ticks_us(), startWait) > MAXIMUM_TIME:
            return None
    #This code above sets a benchmark wait time and then checks to see if it exceeds the maximum time it should take for the echo to return. If it does exceed that time then it returns None to signify that the distance is out of range.
    pingStart = time.ticks_us()
    #This starts th timer.
    while Echo.value():
        pass
    pingStop = time.ticks_us() #This stops the timer and is triggred by the while pass statmeent
    distanceTime = time.ticks_diff(pingStop, pingStart) // 2 #This gets the time elapsed
    return int(distanceTime * SOUNDVELOCITY / 10000) #This returns the distance in cm by multiplying the time by the speed of sound and dividing by 10000 to convert from microseconds to seconds and to account for the fact that the sound has to travel to the object and back.

note_freqs = { #This is just an array with all of the notes and their corresponding frequencies 
    'E':  329.63,
    'F':  349.23,
    'G':  392.00,
    'A':  440.00,
    'Bb': 466.16,
    'C':  523.25,
    'D':  293.66
}
#This is all of the tempos
BPM = 180
Q   = 60 / BPM
E   = Q / 2
H   = Q * 2
DQ  = Q * 1.5

melody = [#This is the array of melodys and their position.
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

lengths = [#This array coresponds to the melody array and it shows each length for each note.
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

# This is the software flag that acts as our pseudo-interrupt signal.
# play_note() sets it to True during the silent gap between notes, which
# is the benchmark moment the main loop watches for to trigger updates.
do_update = False

def play_note(freq, duration): #This is the music function that plays notes
    global do_update

    buzzer.freq(int(freq))
    buzzer.duty_u16(32768)
    #The above lines of code declare what the frequency and duty cycle are. This is the volume and frequency
    time.sleep(duration * 0.9)
    buzzer.duty_u16(0)

    # Raise the software flag during the silent gap between notes.
    # This gap is the benchmark window where sensor reads and display
    # updates are allowed to run — the music drives the timing.
    do_update = True
    time.sleep(duration * 0.1)
    #The above three lines of code are short breaks wher there is no music played

def update_display(line_str, voltage, distance):
    if not oled:
        return

    oled.fill(0)

    oled.text(line_str, 0, 0)
    oled.text("Voltage: " + str(voltage) + "V", 0, 12)

    if distance is None:
        dist_str = "Dist: Out of Range"
        dist_bar = 0
    else:
        dist_str = "Dist: " + str(distance) + " cm"
        dist_bar = min(distance, 30)
    oled.text(dist_str, 0, 24)

    bar_width = dist_bar * 128 // 30
    oled.text("0cm",  0,  38)
    oled.text("30cm", 88, 38)
    oled.hline(0, 50, 128, 1)
    oled.fill_rect(0, 52, bar_width, 8, 1)

    word = "FORD"
    fw = len(word) * 8
    fh = 8

    buf = bytearray(fw * fh // 8 + 1)
    fb  = framebuf.FrameBuffer(buf, fw, fh, framebuf.MONO_HLSB)
    fb.fill(0)
    fb.text(word, 0, 0, 1)

    for x in range(fw):
        for y in range(fh):
            byte_index = (y * fw + x) // 8
            bit_index  = 7 - ((y * fw + x) % 8)
            pixel = (buf[byte_index] >> bit_index) & 1

            if pixel:
                dx = 127 - y
                dy = x
                oled.pixel(dx, dy, 1)

    oled.show()

def read_sensors():
    reading  = analog.read_u16()
    voltage  = round(reading * 3.3 / 65535, 2)
    distance = get_distance()

    if voltage > 1.5:
        line_str = "Line: BLACK"
        led.value(1)
    else:
        line_str = "Line: WHITE"
        led.value(0)

    print(line_str, "|", "Dist:", distance, "| Voltage:", voltage, "V")
    return line_str, voltage, distance

time.sleep(2)

note_index = 0

# Cache the last known sensor values so the display always has something
# to show even when an update cycle is skipped to protect music timing.
last_line_str = "Line: ..."
last_voltage  = 0.0
last_distance = None

while True:
    note_name = melody[note_index]
    duration  = lengths[note_index]
    freq      = note_freqs[note_name]
    play_note(freq, duration)

    note_index = (note_index + 1) % len(melody)

    # Check the software flag — play_note() raised it during the silent gap,
    # meaning this is the benchmarked window to do sensor work.
    if do_update:
        do_update = False  # Clear the flag immediately so it's ready for the next note.

        # Record how much of the inter-note gap has already elapsed so we
        # can bail out if the sensor work is running long and would eat into
        # the next note's start time.
        update_start = time.ticks_ms()
        gap_budget_ms = int(duration * 0.1 * 1000)  # The silent gap in milliseconds is our time budget.

        # Only proceed with the sensor read if there is still budget remaining.
        # This keeps the music tight by skipping the update rather than delaying the next note.
        if time.ticks_diff(time.ticks_ms(), update_start) < gap_budget_ms:
            last_line_str, last_voltage, last_distance = read_sensors()
            update_display(last_line_str, last_voltage, last_distance)