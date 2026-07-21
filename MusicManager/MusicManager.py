from FileManager import FileManager

class MusicManager:
    def __init__(self):
        self.db = DB_Manager()
        self.file_manager = FileManager()

    def run(self):
        self.file_manager.run()

        for track in self.file_manager.tracks:
            add = self.db.add_track(track)
            if add:
                print(f"Добавлен в БД: {track['title']} | {track['author']} | {track['album']} | {track['year']}")
            else:
                print(f"Уже существует: {track['title']} | {track['author']} | {track['album']} | {track['year']}")


import sqlite3
from DB import DB_PATH

class DB_Manager:
    def __init__(self):
        self.sql = sqlite3.connect(DB_PATH)
        self.create_sql_tables()

    def create_sql_tables(self):
        self.sql.executescript("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            album TEXT,
            year TEXT,
            file_path TEXT NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        self.sql.commit()

    def track_exists(self, title, author, album, year):
        cursor = self.sql.cursor()
        cursor.execute("""
        SELECT id FROM tracks
        WHERE title = ?
        AND author = ?
        AND album IS ?
        AND year IS ?
        """, (title, author, album, year))

        return cursor.fetchone() is not None

    def add_track(self, data):
        if self.track_exists(data["title"], data["author"], data["album"], data["year"]):
            return False

        self.sql.execute("""
        INSERT INTO tracks (title, author, album, year, file_path)
        VALUES (?, ?, ?, ?, ?)
        """, (data["title"], data["author"], data["album"], data["year"], data["file_path"]))

        self.sql.commit()

        return True


if __name__ == "__main__":
    manager = MusicManager()
    manager.run()