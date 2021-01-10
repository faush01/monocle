import Adafruit_DHT
from time import sleep
from datetime import datetime
import requests

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4


def send_log_data(event_date, event_data, event_type):
    try:
        request_data = {
            "table": "environment",
            "event_date": event_date,
            "event_type": event_type,
            "event_data": event_data
        }
        print ("Sending Data: " + str(request_data))
        r = requests.post("http://192.168.0.16:3456", json=request_data)
        print ("New Data Notification Request : " + r.text)

    except Exception as err:
        print("call_notify_thread - " + event_date + " - " + str(err))


while True:

    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

    if humidity is not None and temperature is not None:
        print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))

        date_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        send_log_data(date_string, temperature, "t")
        send_log_data(date_string, humidity, "rh")

    else:
        print("Failed to retrieve data from humidity sensor")

    sleep(300)
