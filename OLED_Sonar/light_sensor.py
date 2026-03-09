from machine import Pin, ADC
import time

analog = ADC(Pin(28))
digital = Pin(15, Pin.IN, Pin.PULL_DOWN)
led = Pin(22, Pin.OUT, 0)

while True:
    reading = analog.read_u16()
    voltage = round(reading * 3.3 / 65535, 2)
    
    if voltage > 1.5:
        print("BLACK LINE DETECTED:", voltage, "V")
        led.value(1)
    else:
        print("WHITE LINE DETECTED:", voltage, "V")
    
    time.sleep_ms(500)
    led.value(0)