import sqlite3

with open("DB.sql", "r", encoding="utf-8") as file:
    sql = file.read()

conn = sqlite3.connect("music.db")
conn.executescript(sql)
conn.close()