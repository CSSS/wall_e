import psycopg2
import psycopg2.extensions

conn = psycopg2.connect("dbname='csss_discord_db' user='wall_e' host='localhost' password='3fon49h23GPk3!r$'")
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

curs = conn.cursor()
curs.execute("DROP TABLE IF EXISTS Reminders;")

curs.execute("CREATE TABLE Reminders ( reminder_id BIGSERIAL  PRIMARY KEY, reminder_date timestamp,  channel_id varchar(500), message varchar(2000), author_id varchar(500) );")

import datetime
dt = datetime.datetime.now()

#(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
b = dt + datetime.timedelta(seconds=10) # days, seconds, then other fields.
print(dt.time())
print(b.time())
curs.execute("insert into Reminders (reminder_date, channel_id, message, author_id)values ( TIMESTAMP '"+str(b)+"',  'channel_id' , 'message', 'author_id' );")


while 1:
	dt = datetime.datetime.now()
	curs.execute("SELECT * FROM Reminders where reminder_date <= TIMESTAMP '"+str(dt)+"';")
	for row in curs.fetchall():
		print(row)
		curs.execute("DELETE FROM Reminders WHERE reminder_id = "+str(row[0])+";")
