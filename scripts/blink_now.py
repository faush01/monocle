import RPi.GPIO as GPIO
from time import sleep


GPIO.setmode(GPIO.BOARD)

GPIO.setup(8, GPIO.OUT, initial=GPIO.LOW)

count = 1

while count <= 100:
    GPIO.output(8, GPIO.HIGH)
    sleep(0.01)
    GPIO.output(8, GPIO.LOW)
    sleep(0.1)
    count += 1
