import RPi.GPIO as GPIO
import os
import time
import sqlite3
from datetime import datetime
from time import mktime
import requests
from threading import Thread

# 3200 imp/KwH
# (3600 / (3200 / 1000)) / seconds = watts
# time = (3600 / (3200 / 1000)) / watts
# (3600 / (3200 / 1000)) / 5500 = 


def call_notify_thread():
    r = requests.get("http://localhost:5000/new_data_available")
    print ("New Data Notification Request : " + r.text)


def log_data(time_stamp, pulse_count, time_span):

    print ("Log Data Point")

    try:
        sql = "INSERT INTO log('timestamp', 'pulse_count', 'time_span') VALUES (?, ?, ?)"
        conn = sqlite3.connect("data.db")
        conn.execute(sql, (datetime.fromtimestamp(mktime(time.localtime(time_stamp/1000000000))), pulse_count, time_span))
        conn.commit()
        conn.close()
    except Exception as err:
        print (str(err))

    try:
        file_name_stamp = time_stamp / 1000000000 # to seconds
        file_name_stamp = time.localtime(file_name_stamp)
        file_name = "log_files/" + time.strftime('%Y-%m-%d', file_name_stamp) + ".log"
        with open(file_name, "a") as myfile:
            myfile.write(str(time_stamp) + "\t" + str(pulse_count) + "\t" + str(time_span) + "\r\n")
    except Exception as err:
        print (str(err))

    try:
        t = Thread(target=call_notify_thread)
        t.start()
    except Exception as err:
        print(str(err))


log_interval = 1000000000 * 60 # 60 seconds
count = 1
last_log_stamp = -1
gpio_input_pin = 7


def button_callback(channel):
    global count
    global last_log_stamp

    pinval = GPIO.input(channel)
    if pinval == 1:
        return

    now_stamp = time.time_ns()

    if last_log_stamp == -1:
        last_log_stamp = now_stamp

    time_diff = now_stamp - last_log_stamp

    if time_diff > log_interval:
        print ("Logging Triggered : " + str(now_stamp) + " - " + str(count) + " - " + str(time_diff))
        log_data(now_stamp, count, time_diff)
        last_log_stamp = now_stamp
        count = 0
    else:
        count += 1

    #print("Button was pushed : " + str(count) + " - " + str(time_diff) + " - " + str(datetime.datetime.now()))


if not os.path.exists('log_files'):
    os.makedirs('log_files')

initial_setup = """
CREATE TABLE IF NOT EXISTS log(
    'timestamp' timestamp NOT NULL PRIMARY KEY,
    'pulse_count' INTEGER NOT NULL,
    'time_span' INTEGER NOT NULL
)
"""

conn = sqlite3.connect("data.db")
conn.execute(initial_setup)
conn.commit()
conn.close()

GPIO.setmode(GPIO.BOARD)
GPIO.setup(gpio_input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(gpio_input_pin, GPIO.FALLING, callback=button_callback, bouncetime=20)

message = input("Press enter to quit\n\n")
GPIO.cleanup()


