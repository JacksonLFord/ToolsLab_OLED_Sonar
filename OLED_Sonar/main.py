from machine import Pin, I2C
from utime import sleep


i2c = I2C(1, sda=Pin(26), scl=Pin(27), freq=400000) #identifying the SDA and SCL pins for the I2C communications.

devices = i2c.scan() #This begins scanning for devices
print("I2C devices found:", [hex(d) for d in devices])#If devices are found
if not devices:#If no devices are found, it will print an error message and a troubleshooting checklist.
    print()
    print("ERROR: No I2C devices detected!")
    print()
    print("Troubleshooting checklist:")
    print("  1. Check wiring:")
    print("     VCC -> 3V3 (pin 36)")
    print("     GND -> GND (pin 38)")
    print("     SDA -> GP26 (pin 31)")
    print("     SCL -> GP27 (pin 32)")
    print("  2. Make sure connections are solid (not loose)")
    print("  3. Some displays use 5V, try VCC -> VBUS (pin 40)")
    print("  4. Check if SDA/SCL labels are swapped on your board")
else: #This is executed if devices are found
    from sh1106 import SH1106_I2C
    #These three lines of code initialize the SH1106 OLED display using the I2C interface. It uses the first detected device address from the scan results.
    addr = devices[0]
    print("Using device at address:", hex(addr))
    oled = SH1106_I2C(128, 64, i2c, addr=addr)

    # This is the test code that gives a display
    oled.fill(0)                          # clear screen
    oled.text("Hello!", 0, 0)             # line 1
    oled.text("Pico 2W + SH1106", 0, 16)  # line 2
    oled.text("I2C LCD Ready", 0, 32)     # line 3
    oled.show()
    sleep(5) #I wait 5 seconds before updating from the test display to my custom display.
    oled.fill(0)                          # clear screen
    oled.text("This is my code!", 0, 0)       # line 1
    oled.text("I hate physics", 0, 16)       # line 2
    oled.show()
    print("Display initialized!")
