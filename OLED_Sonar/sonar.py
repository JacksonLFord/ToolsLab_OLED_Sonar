from machine import Pin, time_pulse_us
import time
 
Trig = Pin(26, Pin.OUT, 0)
Echo = Pin(27, Pin.IN, 0)
led = Pin(22, Pin.OUT, 0) #Pin for an LED
DISTANCE = 0
SOUNDVELOCITY = 340
MAXIMUM_DISTANCE_CM = 200
MAXIMUM_TIME = MAXIMUM_DISTANCE_CM * 2 * 10000 // SOUNDVELOCITY


def get_distance():#returns the distance in cm
    #These three lines of code are used to send out the triggr signal that will be used to calculate the distnce
    Trig.value(1)
    time.sleep_us(10)
    Trig.value(0)
    #These three lines of code wait for the echo input to recieve a signal and records the amount of time before it records it.
    startWait = time.ticks_us()
    while not Echo.value():#The code below is to prevent the cod from locking up. If the echo signal reaches the maxmium rated distance then the code will stop waiting and return a timeout error. This is important because if the code locks up then it will not be able to run the rest of the code and it will not be able to get the distance of 200cm per the lecture slide, it just exits.
        if time.ticks_diff(time.ticks_us(), startWait) > MAXIMUM_TIME:
            return None
    pingStart = time.ticks_us()
    while Echo.value():
        pass    
    pingStop = time.ticks_us()
    #After the times are recorded these three times of code use the time differences to calculate the distance and then returns the distance.
    distanceTime = time.ticks_diff(pingStop, pingStart)//2
    DISTANCE = int(distanceTime * SOUNDVELOCITY / 10000)
    return DISTANCE
#This part of the code is used to call the get_distance function and loop.
time.sleep(2)
while True:
    time.sleep_ms(500)#waits 500ms before repeating the get_distance function  
    DISTANCE = get_distance() #Calls the get_distance funciton 
    if(DISTANCE is None):
        print("Distance: Out of Range") #if the distance is out of range then it will print out of range
    else:
        print("Distance", DISTANCE, "cm")
        if(DISTANCE < 10):
            led.value(1) #turns on the LED if the distance is less than 10cm
            time.sleep_ms(50)
            led.value(0)
        else:
            led.value(0) #turns off the LED if the distance is greater than 10cm
           
            
     #records the distance to the terminal.