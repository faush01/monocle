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
    print ("Database file not found : " + db_path)
    exit(-1)
	
# 3200 imp/KwH
# (3600 / (3200 / 1000)) / seconds = watts
# time = (3600 / (3200 / 1000)) / watts
# (3600 / (3200 / 1000)) / 5500 =

conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
cur = conn.cursor()

'''
sql = """
SELECT strftime('%Y-%m-%dT%H:', timestamp) || CAST((CAST(strftime('%M', timestamp) AS INT) / 10) AS TEXT) || "0:00" AS minuet_bucket,
       SUM(((CAST(time_span AS FLOAT) / 1000000000.0) / 3600.0) * (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000)) AS whours
FROM log
GROUP BY strftime('%Y-%m-%dT%H:', timestamp) || CAST((CAST(strftime('%M', timestamp) AS INT) / 10) AS TEXT) || "0:00"
"""
cur.execute(sql)

rows = cur.fetchall()
for row in rows:

    print (row)
'''


'''
sql = """
SELECT strftime('%Y-%m-%dT%H:00:00', timestamp) AS log_time,
       SUM(((CAST(time_span AS FLOAT) / 1000000000.0) / 3600.0) * (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000)) AS whours
FROM log
GROUP BY strftime('%Y-%m-%dT%H:00:00', timestamp)
"""
cur.execute(sql)

rows = cur.fetchall()
for row in rows:

    print (row)
'''


cur.execute("""
SELECT timestamp,
       pulse_count,
       time_span,
       ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000) AS avg_pps,
       (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000) AS watts,
       ((CAST(time_span AS FLOAT) / 1000000000.0) / 3600.0) * (3600.0 / (3200.0 / 1000.0)) / ((CAST(time_span AS FLOAT) / pulse_count) / 1000000000) AS whours
FROM log 
where timestamp > ?
""", (datetime(2020,3,7,18,0,0),))

'''
cur.execute("""
SELECT strftime('%Y-%m-%dT%H:', timestamp) || CAST((CAST(strftime('%M', timestamp) AS INT) / 10) AS TEXT) || "0:00" AS timestamp,
       pulse_count,
       time_span,
       ((CAST(SUM(time_span) AS FLOAT) / SUM(pulse_count)) / 1000000000) AS avg_pps,
       (3600.0 / (3200.0 / 1000.0)) / ((CAST(SUM(time_span) AS FLOAT) / SUM(pulse_count)) / 1000000000) AS watts,
       ((CAST(SUM(time_span) AS FLOAT) / 1000000000.0) / 3600.0) * (3600.0 / (3200.0 / 1000.0)) / ((CAST(SUM(time_span) AS FLOAT) / SUM(pulse_count)) / 1000000000) AS whours
FROM log 
where timestamp > ?
GROUP BY strftime('%Y-%m-%dT%H:', timestamp) || CAST((CAST(strftime('%M', timestamp) AS INT) / 10) AS TEXT) || "0:00"
""", (datetime(2020,3,07,18,00,00),))
'''


rows = cur.fetchall()
for row in rows:

    timestamp = row[0]#.strftime("%m/%d/%Y, %H:%M:%S")
    pulse_count = row[1]
    time_span = row[2]

    avg_pps = row[3]
    watt = row[4]
    whours = row[5]

    #average_pps = (time_span / pulse_count) / 1000000000
    #watts = (3600 / (3200 / 1000)) / average_pps
    #Wh = ((time_span / 1000000000) / 3600) * watts

    #print (timestamp + "|" + str(pulse_count) + "|" + str(time_span) + "|" + str(average_pps) + "|" + str(avg_pps) + "|" + str(watts) + "|" + str(watt) + "|" + str(Wh) + "|" + str(whours))
    #print (timestamp + "\t" + str(pulse_count) + "\t" + str(time_span) + "\t" + str(average_pps) + "(" + str(avg_pps) + ")\t" + str(watts) + "(" + str(watt) + ")\t" + str(Wh) + "(" + str(whours) + ")")
    #print ("{0}\t{1}\t{2}\t{3:.3f}\t{4:.3f}\t{5:.3f}".format(timestamp, pulse_count, time_span, average_pps, watts, Wh))

    print ("{0}\t{1}\t{2}\t{3:.3f}\t{4:.3f}\t{5:.3f}".format(timestamp, pulse_count, time_span, avg_pps, watt, whours))

cur.close()
conn.close()



#time_stamp = 1579385462707227160
#time_stamp = time_stamp / 1000000000 # to seconds

#stamp = time.localtime(time_stamp)

#print (time.strftime('%Y-%m-%d %H:%M:%S %Z', stamp))

