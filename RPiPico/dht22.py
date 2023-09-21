import dht
import machine
import time

d = dht.DHT22(machine.Pin(4))

while True:
    d.measure()
    print("Temp : %s\t Hum : %s" % (d.temperature(), d.humidity()))
    time.sleep(120)
    