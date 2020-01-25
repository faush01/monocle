from flask import Flask, render_template, send_from_directory, jsonify, request
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'fav.png', mimetype='image/png')


@app.route("/")
def home():
    data = {}
    data["server_time"] = str(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    return render_template('home.html', data=data)


@app.route("/get_history_data")
def get_data():

    conn = sqlite3.connect("../scripts/monitor/data.db", detect_types=sqlite3.PARSE_DECLTYPES)
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

    print (str(start_timestamp))
    print(str(end_timestamp))

    if interval == "1min":
        sql = """
        SELECT timestamp,
               --pulse_count,
               --time_span,
               --((CAST(time_span AS FLOAT) / pulse_count) / 1000000000) AS avg_pps,
               --(3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000) AS watts,
               ((CAST(time_span AS FLOAT) / 1000000000.0) / 3600.0) * (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000) AS whours
        FROM log 
        where timestamp >=  ? and timestamp < ?
        """

    elif interval == "10min":
        sql = """
        SELECT strftime('%Y-%m-%dT%H:', timestamp) || CAST((CAST(strftime('%M', timestamp) AS INT) / 10) AS TEXT) || "0:00" AS minuet_bucket,
        SUM(((CAST(time_span AS FLOAT) / 1000000000.0) / 3600.0) * (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000)) AS whours
        FROM log
        where timestamp >=  ? and timestamp < ?
        GROUP BY strftime('%Y-%m-%dT%H:', timestamp) || CAST((CAST(strftime('%M', timestamp) AS INT) / 10) AS TEXT) || "0:00"
        """

    elif interval == "hourly":
        sql = """
        SELECT strftime('%Y-%m-%dT%H:00:00', timestamp) AS log_time,
               SUM(((CAST(time_span AS FLOAT) / 1000000000.0) / 3600.0) * (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000)) AS whours
        FROM log
        where timestamp >=  ? and timestamp < ?
        GROUP BY strftime('%Y-%m-%dT%H:00:00', timestamp)
        """

    elif interval == "daily":
        sql = """
        SELECT strftime('%Y-%m-%d', timestamp) AS log_time,
               SUM(((CAST(time_span AS FLOAT) / 1000000000.0) / 3600.0) * (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000)) AS whours
        FROM log
        where timestamp >=  ? and timestamp < ?
        GROUP BY strftime('%Y-%m-%d', timestamp)
        """

    elif interval == "daily":
        sql = """
        SELECT strftime('%Y-%m-%d', timestamp) AS log_time,
               SUM(((CAST(time_span AS FLOAT) / 1000000000.0) / 3600.0) * (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000)) AS whours
        FROM log
        where timestamp >=  ? and timestamp < ?
        GROUP BY strftime('%Y-%m-%d', timestamp)
        """

    cur.execute(sql, (start_timestamp,end_timestamp,))
    rows = cur.fetchall()

    data_set = []
    for row in rows:
        row_data = []
        row_data.append(row[0])
        row_data.append(row[1])
        data_set.append(row_data)

    cur.close()
    conn.close()

    return jsonify(data_set)


app.run()
