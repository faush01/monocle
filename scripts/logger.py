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
# (pulses / 3200) * (3600 / seconds) = Kw/h
# ((pulses / 3200) * (3600 / seconds) * 1000) / 3600 = w/s
# ((pulses / 3200) * (3600 / seconds)) / 3.6 = w/s
# 9 * Pulse / 8 * Sec / 3.6 = w/s
# ((9 * Pulse) / (8 * Sec)) / 3.6 = w/s
# convert to watts per second


def call_notify_thread(event_data):
    try:
        request_data = {"power_usage": event_data}

        print("Sending Data: " + str(request_data))
        r = requests.post("http://192.168.0.16:3456", json=request_data)
        print("New Data Notification Request : " + r.text)

    except Exception as err:
        print("call_notify_thread")
        print(event_data)
        print(str(err))


def log_data(time_stamp, pulse_count, time_span):

    # print ("Log Data Point")

    '''
    try:
        sql = "INSERT INTO log('timestamp', 'pulse_count', 'time_span') VALUES (?, ?, ?)"
        conn = sqlite3.connect("data.db")
        conn.execute(sql, (datetime.fromtimestamp(mktime(time.localtime(time_stamp/1000000000))), pulse_count, time_span))
        conn.commit()
        conn.close()
    except Exception as err:
        print (str(err))
    '''

    '''
    try:
        file_name_stamp = time_stamp / 1000000000 # to seconds
        file_name_stamp = time.localtime(file_name_stamp)
        file_name = "log_files/" + time.strftime('%Y-%m-%d', file_name_stamp) + ".log"
        with open(file_name, "a") as myfile:
            myfile.write(str(time_stamp) + "\t" + str(pulse_count) + "\t" + str(time_span) + "\r\n")
    except Exception as err:
        print (str(err))
    '''

    try:
        event_date_seconds = time_stamp / 1000000000 # to seconds
        file_name_stamp = time.localtime(event_date_seconds)
        event_date = time.strftime('%Y-%m-%d %H:%M:%S', file_name_stamp)
        ws = ((9 * int(pulse_count)) / (8 * (int(time_span) / 1000000000))) / 3.6

        log_power = {
            "event_date": event_date,
            "event_type": "ws",
            "event_data": ws
        }
        data_to_log = [log_power]

        t = Thread(target=call_notify_thread, args=([data_to_log]))
        t.start()
    except Exception as err:
        print("data_to_log - " + str(data_to_log) + " - " + str(err))


log_interval = 1000000000 * 60 # 60 seconds
count = 1
last_log_stamp = -1
gpio_input_pin = 7
last_pulse_detected = time.time()

def button_callback(channel):
    global count
    global last_log_stamp
    global last_pulse_detected

    pinval = GPIO.input(channel)
    if pinval == 1:
        return

    now_stamp = time.time_ns()

    if last_log_stamp == -1:
        last_log_stamp = now_stamp

    time_diff = now_stamp - last_log_stamp

    if time_diff > log_interval:
        # print ("Logging Triggered : " + str(now_stamp) + " - " + str(count) + " - " + str(time_diff))
        log_data(now_stamp, count, time_diff)
        last_log_stamp = now_stamp
        last_pulse_detected = time.time()
        count = 0
    else:
        count += 1

    # print("Button was pushed : " + str(count) + " - " + str(time_diff) + " - " + str(datetime.datetime.now()))


# if not os.path.exists('log_files'):
#     os.makedirs('log_files')

initial_setup = """
CREATE TABLE IF NOT EXISTS log(
    'timestamp' timestamp NOT NULL PRIMARY KEY,
    'pulse_count' INTEGER NOT NULL,
    'time_span' INTEGER NOT NULL
)
"""

'''
conn = sqlite3.connect("data.db")
conn.execute(initial_setup)
conn.commit()
conn.close()
'''

GPIO.setmode(GPIO.BOARD)
GPIO.setup(gpio_input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(gpio_input_pin, GPIO.FALLING, callback=button_callback, bouncetime=20)

while True:

    seconds_since_last_update = time.time() - last_pulse_detected
    # print (str(datetime.now()) + " - Time since last update: %s" % seconds_since_last_update)
    if seconds_since_last_update > 90:
        print (str(datetime.now()) + " - No new data for %s seconds" % seconds_since_last_update)
    time.sleep(60)

# message = input("Press enter to quit\n\n")

GPIO.cleanup()


