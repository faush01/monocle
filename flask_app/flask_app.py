from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_sockets import Sockets
from datetime import datetime, timedelta
import time
import sqlite3
import os
import sys
import os.path
import gevent

app = Flask(__name__)

app = Flask(__name__)
sockets = Sockets(app)

db_path = "data.db"
if len(sys.argv) > 1:
    db_path = sys.argv[1]

if not os.path.isfile(db_path):
    print ("Database file not found : " + db_path)
    exit(-1)

last_data_trigger = 0
new_data_timestamp = 0
data_count = 0

@sockets.route('/echo')
def echo_socket(ws):

    while not ws.closed:

        global last_data_trigger
        global data_count
        if last_data_trigger != new_data_timestamp:
            last_data_trigger = new_data_timestamp
            data = "New Data Available : " + str(data_count)
            data_count += 1
            ws.send(data)
            print (data)

        gevent.sleep(1)

        '''
        message = ws.receive()
        print (str(message))
        ws.send(message)
        '''


@app.route("/new_data_available")
def new_data_available():
    global new_data_timestamp
    new_data_timestamp = time.time()
    return str(new_data_timestamp)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'fav.png', mimetype='image/png')


@app.route("/")
def home():
    data = {}
    data["server_time"] = str(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    return render_template('home.html', data=data)


@app.route("/get_current_data")
def get_current_data():

    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    cur = conn.cursor()

    sql = """
    SELECT timestamp,
           --pulse_count,
           --time_span,
           --((CAST(time_span AS FLOAT) / pulse_count) / 1000000000) AS avg_pps,
           (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000) AS watts
           --((CAST(time_span AS FLOAT) / 1000000000.0) / 3600.0) * (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000) AS whours
    FROM log 
    ORDER BY timestamp DESC
    LIMIT 1
    """
    cur.execute(sql)
    rows = cur.fetchall()

    current_usage = {}
    if len(rows) == 1:
        age = datetime.now() - rows[0][0]
        are_bits = str(age).split(".")
        current_usage["age"] = are_bits[0]
        current_usage["age_seconds"] = age.total_seconds()
        current_usage["watts"] = round(rows[0][1], 2)
        current_usage["time"] = str(datetime.now())
    else:
        current_usage["age"] = "-"
        current_usage["age_seconds"] = "-"
        current_usage["watts"] = "-"
        current_usage["time"] = str(datetime.now())

    cur.close()
    conn.close()

    return jsonify(current_usage)


@app.route("/get_history_data")
def get_history_data():

    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    cur = conn.cursor()

    interval = request.args.get('interval')
    span = request.args.get('span')
    start = request.args.get('start')

    span_minutes = int(span)
    start_timestamp = None
    end_timestamp = None

    start_split = start.split("T")
    if len(start_split) == 2 and start_split[0] != "":
        date_bits = start_split[0].split("-")
        if len(date_bits) == 3:
            year = int(date_bits[0])
            month = int(date_bits[1])
            day = int(date_bits[2])
            hour = 0
            minute = 0
            second = 0
            if start_split[1] != "":
                time_bits = start_split[1].split(":")
                if len(time_bits) >= 2:
                    hour = int(time_bits[0])
                    minute = int(time_bits[1])
            start_timestamp = datetime(year, month, day, hour, minute, second)
            end_timestamp = start_timestamp + timedelta(minutes=span_minutes)

    if start_timestamp is None:
        start_timestamp = datetime.now() - timedelta(minutes=span_minutes)
        end_timestamp = datetime.now()

    #print (str(start_timestamp))
    #print(str(end_timestamp))

    query_time_string = ""
    if interval == "1min":
        query_time_string = "strftime('%Y-%m-%dT%H:%M:%S', timestamp)"
    elif interval == "10min":
        query_time_string = "strftime('%Y-%m-%dT%H:', timestamp) || CAST((CAST(strftime('%M', timestamp) AS INT) / 10) AS TEXT) || '0:00'"
    elif interval == "hourly":
        query_time_string = "strftime('%Y-%m-%dT%H:00:00', timestamp)"
    elif interval == "daily":
        query_time_string = "strftime('%Y-%m-%d', timestamp)"

    sql = ""
    sql += "SELECT " + query_time_string + " AS timestamp, "
    sql += "(3600.0 / (3200.0 / 1000.0)) / ((CAST(SUM(time_span) AS FLOAT) / SUM(pulse_count)) / 1000000000) AS whours "
    sql += "FROM log "
    sql += "where timestamp >=  ? and timestamp < ? "
    sql += "GROUP BY " + query_time_string + " "
    sql += "ORDER BY " + query_time_string + " ASC"

    cur.execute(sql, (start_timestamp,end_timestamp,))
    rows = cur.fetchall()

    data_set = []
    for row in rows:
        row_data = []
        row_data.append(row[0])
        row_data.append(round(row[1], 2))
        data_set.append(row_data)

    cur.close()
    conn.close()

    return jsonify(data_set)


@app.route("/data_report")
def data_report():

    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    cur = conn.cursor()

    sql = """
    select
        strftime('%Y-%m-%d', timestamp) as day,
        count(1) AS data_count,
        sum(pulse_count) as pulses,
        sum(time_span) as total_time,
        min(time_span) as min_span,
        max(time_span) as max_span
    from log
    group by day
    order by day asc
    """

    cur.execute(sql)
    rows = cur.fetchall()

    data_set = []
    for row in rows:
        data = {}
        data["date"] = row[0]
        data["data_count"] = row[1]
        data["pulses"] = row[2]
        data["total_time"] = row[3]
        data["min_span"] = row[4]
        data["max_span"] = row[5]
        data_set.append(data)

    cur.close()
    conn.close()

    return render_template('data_report.html', data=data_set)


# app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
