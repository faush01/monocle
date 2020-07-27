
import psycopg2

conn_info = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "admin"
}

conn = psycopg2.connect(**conn_info)
cur = conn.cursor()

with open("data.csv", "r") as file:

    line = file.readline()
    while line:
        line = line.strip()
        row = line.split(",")
        event_date = row[0] + ".0000"

        # (pulses / 3200) * (3600 / seconds) = Kw/h
        # ((pulses / 3200) * (3600 / seconds) * 1000) / 3600 = w/s
        # ((pulses / 3200) * (3600 / seconds)) / 3.6 = w/s
        # 9 * Pulse / 8 * Sec / 3.6 = w/s
        # ((9 * Pulse) / (8 * Sec)) / 3.6 = w/s
        # convert to watts per second
        ws = ((9 * int(row[1])) / (8 * (int(row[2])/1000000000))) / 3.6

        insert_sql = "INSERT INTO power_usage (event_date, data_type, data) VALUES (%s, %s, %s)"
        # cur.execute(insert_sql, (event_date, "ws", ws))

        line = file.readline()

conn.commit()
cur.close()
conn.close()
