import sqlite3
DB_PATH = "../DB.db"

if __name__ == "__main__":
    conn = sqlite3.connect("DB.db")
    cursor = conn.cursor()

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
                conn.commit()
                print("OK")

        except Exception as e:
            print("Ошибка:", e)
    conn.close()

    # SELECT title, author FROM tracks;
    # SELECT * FROM tracks WHERE author = 'Ария';
    # DELETE FROM tracks WHERE id = 1;
    # UPDATE tracks SET title = 'New name' WHERE id = 1;