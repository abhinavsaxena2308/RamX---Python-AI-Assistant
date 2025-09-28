import sqlite3

conn = sqlite3.connect('Ramx.db')
cursor = conn.cursor()

query = "CREATE TABLE IF NOT EXISTS sys_commmand(id INTEGER PRIMARY KEY, name varchar(255),path varchar(255))"
cursor.execute(query)

# below query is for locally installed apps
# query = "INSERT INTO sys_commmand VALUES (null, 'Chrome','C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe')"
# cursor.execute(query)
# conn.commit()

# below query is for web apps
query = "CREATE TABLE IF NOT EXISTS web_commmand(id INTEGER PRIMARY KEY, name varchar(255),url Varchar(255))"
cursor.execute(query)

query = "INSERT INTO web_commmand VALUES (null, 'Web Whatsapp','https://web.whatsapp.com/')"
cursor.execute(query)
conn.commit()