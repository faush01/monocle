import network
import time
import rp2
from machine import Pin
import urequests as requests
import micropython
import dht

led = machine.Pin("LED", machine.Pin.OUT)
led.off()

sensor = dht.DHT22(machine.Pin(4))

rp2.country("AU")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

ssid = '' # ssid of wifi
password = '' # password of wifi
wlan.disconnect()
wlan.connect(ssid, password)

while wlan.status() != 3:
    print("Waiting for connection : " + str(wlan.status()))
    led.on()
    time.sleep(0.3)
    led.off() 
    time.sleep(5)

led.on()
print("connected")

host = "http://192.168.0.17:3456"

while True:   
    try:
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()
        print("Temp : %s\t Hum : %s" % (temperature, humidity))
    
        log_data = {
            "event_date": "",
            "event_type": "s1",
            "event_data": {"t": temperature, "rh": humidity}
        }
        all_log_data = [log_data]
        payload = {"environment": all_log_data}
        
        response = requests.post(host, json=payload)
        print("sent : " + str(response.status_code))
        response.close()
        
        led.off()
        time.sleep(0.3)
        led.on()
        time.sleep(0.3)
        led.off()
        time.sleep(0.3)
        led.on()
        
    except Exception as err:
        print(err)
        led.off()
        time.sleep(0.3)        
        led.on()
        time.sleep(0.3)
        led.off()
        time.sleep(0.3)
        led.on()
        time.sleep(0.3)
        led.off()
        
        if wlan.status() == 3:
            time.sleep(0.3)
            led.on()
            time.sleep(0.3)
            led.off()
    
    time.sleep(120)
    
