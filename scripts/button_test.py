import RPi.GPIO as GPIO
import datetime
import time

# 3200 imp/KwH
# (3600 / (3200 / 1000)) / seconds = watts
# time = (3600 / (3200 / 1000)) / watts
# (3600 / (3200 / 1000)) / 5500 =

gpio_input_pin = 7
count = 0
last = 0

def button_callback(channel):
    global count
    global last

    pinval = GPIO.input(channel)
    print ("Pin %s %s" % (channel, pinval))
    if pinval == 1:
        return

    now = time.time()
    diff = now - last
    print("Button was pushed : " + str(count) + " " + str(now) + " " + str(diff))
    count += 1
    last = now

GPIO.setmode(GPIO.BOARD)
GPIO.setup(gpio_input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(gpio_input_pin, GPIO.FALLING, callback=button_callback, bouncetime=20)

message = input("Press enter to quit\n\n")
GPIO.cleanup()
