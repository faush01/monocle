import time
import sqlite3
from datetime import datetime
from time import mktime
import sys
import os.path

db_path = "data.db"
if len(sys.argv) > 1:
    db_path = sys.argv[1]

if not os.path.isfile(db_path):
    print("Database file not found : " + db_path)
    exit(-1)

conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
cur = conn.cursor()

sql = """
SELECT strftime('%Y-%m-%d-%H', timestamp) AS timestamp_string, 
(3600.0 / (3200.0 / 1000.0)) / ((CAST(SUM(time_span) AS FLOAT) / SUM(pulse_count)) / 1000000000) AS whours 
FROM log 
GROUP BY timestamp_string 
ORDER BY timestamp_string ASC
"""



sql = """
SELECT 
   timestamp_day AS timestamp_string,
   SUM(whours) AS whours
FROM (
SELECT 
   strftime('%Y-%m-%d', timestamp) AS timestamp_day, 
   strftime('%Y-%m-%d-%H', timestamp) AS timestamp_hour, 
   (3600.0 / (3200.0 / 1000.0)) / ((CAST(SUM(time_span) AS FLOAT) / SUM(pulse_count)) / 1000000000) AS whours 
FROM log 
GROUP BY timestamp_hour
)
GROUP BY timestamp_day
ORDER BY timestamp_day ASC
"""



cur.execute(sql)

rows = cur.fetchall()
for row in rows:

    timestamp = row[0]
    whours = row[1]

    print ("{0}\t{1:.3f}".format(row[0], row[1]))

cur.close()
conn.close()
