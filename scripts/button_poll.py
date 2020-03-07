import RPi.GPIO as GPIO
import time


gpio_input_pin = 7

GPIO.setmode(GPIO.BOARD)
GPIO.setup(gpio_input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

last_val = 0

while True:
    pinval = GPIO.input(gpio_input_pin)
    if last_val != pinval:
        last_val = pinval
        print ("Val : " + str(pinval))
    time.sleep(0.01)

