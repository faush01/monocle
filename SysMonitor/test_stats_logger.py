import requests
from datetime import datetime

date_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

data_01 = {
    "event_date": date_string,
    "event_type": "type01",
    "event_data": {"cpu": 29.523, "mem": 86.4}
}
data_02 = {
    "event_date": date_string,
    "event_type": "type02",
    "event_data": {"sessions": 1001, "ws": 234}
}
event_data = [data_01, data_02]
message_data = {"test_event_table": event_data}
print(message_data)

#stats_server = "http://192.168.0.16:3456"
stats_server = "http://localhost:3456"

r = requests.post(stats_server, json=message_data)
print ("New Data Notification Request : %s - %s" % (r.status_code,  r.json()))
