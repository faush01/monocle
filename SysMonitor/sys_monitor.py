from configparser import ConfigParser
import psycopg2
import psutil
from datetime import datetime
import time
from pytz import timezone
import requests
import threading
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# https://psutil.readthedocs.io/en/latest/

class HttpStatsLoggerHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # log_line = format % args
        # print(log_line)
        return

    def do_GET(self):
        #print("HttpStatsLoggerHandler:do_GET()")
        self.send_response(200)
        return

    def do_POST(self):
        #print("HttpStatsLoggerHandlerdo_POST()")
        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len)
        json_string = post_body.decode("utf-8")
        json_request = json.loads(json_string)
        #print(json_request)

        try:
            for table in json_request:
                event_data = []
                for log_item in json_request[table]:
                    event_data.append([log_item["event_date"], log_item["event_type"], log_item["event_data"]])
                log_data(table, event_data)
        except Exception as err:
            print(err)

        response_message = {
            "message": "worked"
        }
        message_string = json.dumps(response_message)
        message_bytes = message_string.encode("utf-8")
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(message_bytes)))
        self.end_headers()
        self.wfile.write(message_bytes)


class HttpStatsLoggingServerThread(threading.Thread):

    keep_running = True
    PORT_NUMBER = 3456

    def __init__(self):
        server_config = config(section="server")
        self.PORT_NUMBER = int(server_config["port"])
        threading.Thread.__init__(self)

    def run(self):
        print("HttpStatsLoggingServerThread:started on port: %s" % self.PORT_NUMBER)
        server = HTTPServer(('', self.PORT_NUMBER), HttpStatsLoggerHandler)

        while self.keep_running:
            server.handle_request()

        print("HttpStatsLoggingServerThread:exiting")

    def stop(self):
        print("HttpStatsLoggingServerThread:stop called")
        self.keep_running = False
        try:
            conn = http.client.HTTPConnection("localhost:%d" % self.PORT_NUMBER)
            conn.request("GET", "/")
            conn.getresponse()
        except:
            pass


def config(filename='config.ini', section=''):
    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db


def create_table(cur, table_name):
    sql_create = "CREATE TABLE IF NOT EXISTS "
    sql_create += "public." + table_name + " ("
    sql_create += "event_date timestamp with time zone NOT NULL, "
    sql_create += "data_type character varying(256) COLLATE pg_catalog.default NOT NULL, "
    sql_create += "data jsonb, "
    sql_create += "CONSTRAINT " + table_name + "_pkey PRIMARY KEY (event_date, data_type)"
    sql_create += ")"
    print(sql_create)
    cur.execute(sql_create)


retention = config(section="retention")
last_retention_check = {}


def remove_old(cur, table_name):
    if retention.get(table_name):
        last_check = last_retention_check.get(table_name)
        if last_check is None or time.time() - last_check > (60 * 60 * 24):
            last_retention_check[table_name] = time.time()
            days = retention[table_name]
            print(table_name + " retention " + days + " days")
            sql_delete = "delete from public." + table_name + " where event_date < now() - INTERVAL '" + days + " DAY'"
            print(sql_delete)
            cur.execute(sql_delete)


def log_data(table, data_set):
    print(table + " : " + str(len(data_set)))
    # print(table + " : " + str(data_set))
    params = config(section="postgresql")
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    data_tuples = []
    # convert json to string
    for data_row in data_set:
        data_tuples.append((data_row[0], data_row[1], json.dumps(data_row[2])))
    #print(data_tuples)

    insert_sql = "INSERT INTO " + table + " (event_date, data_type, data) VALUES (%s, %s, %s)"
    # data_set = [(event_date, "env", '{"data_value": 100}'), (event_date, "system", '{"some_data": 10.5}')]

    try:
        cur.executemany(insert_sql, data_tuples)
    except Exception as ex:
        if "UndefinedTable" == type(ex).__name__:
            print("Trying to create missing table")
            cur.close()
            conn.close()
            conn = psycopg2.connect(**params)
            cur = conn.cursor()
            create_table(cur, table)
            cur.executemany(insert_sql, data_tuples)
        else:
            raise

    remove_old(cur, table)

    conn.commit()
    cur.close()
    conn.close()


def get_session_info():
    params = config(section="emby")
    sessions_url = params["sessions_url"]

    session_info = {}
    session_info["a"] = 0
    session_info["t"] = 0
    session_info["p"] = 0
    session_info["vt"] = 0
    session_info["at"] = 0

    try:
        response = requests.get(sessions_url)
        if response.status_code != 200:
            raise Exception("bad response code from emby call : " + str(response.status_code))
        session_list = response.json()
        # print(session_list)
        for session in session_list:
            if session["DeviceId"] == session["ServerId"]:
                continue

            session_info["t"] += 1

            last_active = session["LastActivityDate"]  # "2020-07-18T04:08:53.1184838Z"
            last_active = last_active[0:-2] + "+0000"
            last_active_date_time_obj = datetime.strptime(last_active, '%Y-%m-%dT%H:%M:%S.%f%z')
            last_active_ago = (datetime.now(timezone('UTC')) - last_active_date_time_obj).total_seconds()
            # print(last_active_ago)

            if last_active_ago < (5 * 60):
                session_info["a"] += 1

            if session.get("NowPlayingItem"):
                play_state = session["PlayState"]
                if play_state["IsPaused"] is False:
                    session_info["p"] += 1

                    # VideoDecoderIsHardware
                    # VideoEncoderIsHardware
                    transcoding_info = session.get("TranscodingInfo")
                    if transcoding_info:
                        if transcoding_info.get("IsVideoDirect") is False:
                            session_info["vt"] += 1
                        if transcoding_info.get("IsAudioDirect") is False:
                            session_info["at"] += 1

    except Exception as err:
        print(err)

    return session_info


# start loggin service
logging_service = HttpStatsLoggingServerThread()
logging_service.start()

network_last_bytes_sent = 0
network_last_bytes_recv = 0
disk_last_bytes_read = 0
disk_last_bytes_written = 0
last_time_sample = datetime.now()

while True:
    time_now = datetime.now()

    # cpu usage
    cpu_usage = psutil.cpu_percent(interval=None, percpu=False)
    # print(cpu_usage)

    # mem usage
    mem_usage = psutil.virtual_memory()
    # print(mem_usage.percent)

    time_diff = (time_now - last_time_sample).total_seconds()

    # network usage
    network_usage = psutil.net_io_counters(pernic=False)
    # print(network_usage)
    if time_diff > 0:
        network_bits_out_sec = ((network_usage.bytes_sent - network_last_bytes_sent) * 8) / time_diff
        network_bits_in_sec = ((network_usage.bytes_recv - network_last_bytes_recv) * 8) / time_diff
    else:
        network_bits_out_sec = 0
        network_bits_in_sec = 0

    network_last_bytes_sent = network_usage.bytes_sent
    network_last_bytes_recv = network_usage.bytes_recv
    # print("Send: " + str(network_bits_out_sec) + " Recv: " + str(network_bits_in_sec))

    # disk usage
    disk_usage = psutil.disk_io_counters()
    # print(disk_usage)
    if time_diff > 0:
        disk_bytes_read_sec = (disk_usage.read_bytes - disk_last_bytes_read) / time_diff
        disk_bytes_written_sec = (disk_usage.write_bytes - disk_last_bytes_written) / time_diff
    else:
        disk_bytes_read_sec = 0
        disk_bytes_written_sec = 0

    disk_last_bytes_read = disk_usage.read_bytes
    disk_last_bytes_written = disk_usage.write_bytes
    # print("Read: " + str(disk_bytes_read_sec) + " Written: " + str(disk_bytes_written_sec))

    # extract Emby Info
    emby_session_info = get_session_info()
    # print(emby_session_info)

    # log event data
    event_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    server_stats = {"c": cpu_usage,
                    "vm": mem_usage.percent,
                    "ni": network_bits_in_sec,
                    "no": network_bits_out_sec,
                    "dr": disk_bytes_read_sec,
                    "dw": disk_bytes_written_sec}
    events = [
        [event_date, "server", server_stats],
        [event_date, "emby", emby_session_info]
    ]
    #print(events)
    log_data("events", events)

    last_time_sample = time_now
    try:
        time.sleep(60)
    except KeyboardInterrupt as err:
        print ("Interrupted")
        logging_service.stop()
        break
