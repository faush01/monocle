import sqlite3

db_path = "C:\\Development\\GitHub\\monocle\\scripts\\data2.db"

conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
cur = conn.cursor()

sql = """
SELECT strftime('%Y-%m-%d %H:%M:%S', timestamp) AS log_time, pulse_count, time_span
FROM log
"""

cur.execute(sql)

with open("data.csv", "w") as file:

    row = cur.fetchone()
    while row:
        row_data = "%s,%s,%s\n" % (row[0], row[1], row[2])
        file.write(row_data)
        row = cur.fetchone()

cur.close()


