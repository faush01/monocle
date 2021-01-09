import requests

request_data = {
    "table": "power_usage",
    "event_date": "2020-07-26 11:11:01.1234",
    "event_type": "test",
    "event_data": 101.1234
}

r = requests.post("http://192.168.0.16:3456", json=request_data)
print ("New Data Notification Request : %s - %s" % (r.status_code,  r.json()))
