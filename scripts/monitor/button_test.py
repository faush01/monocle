import RPi.GPIO as GPIO
import datetime


# 3200 imp/KwH
# (3600 / (3200 / 1000)) / seconds = watts
# time = (3600 / (3200 / 1000)) / watts
# (3600 / (3200 / 1000)) / 5500 = 


count = 1
now = datetime.datetime.now()

def button_callback(channel):
    global count

    pinval = GPIO.input(10)
    if pinval == 1:
        return

    print("Button was pushed : " + str(count) + " " + str(datetime.datetime.now()))
    count += 1


GPIO.setmode(GPIO.BOARD)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(10, GPIO.RISING, callback=button_callback)
#, bouncetime=20)

message = input("Press enter to quit\n\n")
GPIO.cleanup()


