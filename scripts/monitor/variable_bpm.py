import RPi.GPIO as GPIO
from time import sleep
import datetime

GPIO.setmode(GPIO.BOARD)
GPIO.setup(8, GPIO.OUT, initial=GPIO.LOW)

print ("Sending pulses...")

while True:

    GPIO.output(8, GPIO.HIGH)
    sleep(0.01)
    GPIO.output(8, GPIO.LOW)

    now = datetime.datetime.now()
    sleep_for = 5.0 / (float((now.minute + 1)) / 3.0)

    #print (str(sleep_for))

    sleep(sleep_for)

