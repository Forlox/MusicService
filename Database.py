import sqlite3

class Database: # Синглтон для подключения к БД
    instance, connection = None, None

    def __new__(cls):
        if cls.instance in None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def sql_connect(self):
        if self.connection in None:
            self.sql = sqlite3.connect("DB.db")
        return self.connection

    def close_sql_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None


if __name__ == "__main__":
    sql = sqlite3.connect("DB.db") # Тута отдельное подключение
    cursor = sql.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    print(cursor.fetchall())

    while True:
        query = input("\nSQL> ")

        if query.lower() == "exit":
            break

        try:
            cursor.execute(query)
            if query.strip().lower().startswith("select"):
                rows = cursor.fetchall()

                for row in rows:
                    print(row)
            else:
                sql.commit()
                print("OK")

        except Exception as e:
            print("Ошибка:", e)
    sql.close()

    # SELECT title, author FROM tracks;
    # SELECT * FROM tracks WHERE author = 'Ария';
    # DELETE FROM tracks WHERE id = 1;
    # UPDATE tracks SET title = 'New name' WHERE id = 1;