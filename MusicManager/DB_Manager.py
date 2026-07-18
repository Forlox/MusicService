import sqlite3

DB_PATH = "../DB.db"

class DB_Manager:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH)
        self.create_tables()

    def create_tables(self):
        self.db.executescript("""
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

        self.db.commit()

    def track_exists(
            self,
            title,
            author,
            album,
            year
    ):
        cursor = self.db.cursor()

        cursor.execute("""
        SELECT id FROM tracks
        WHERE title = ?
        AND author = ?
        AND album IS ?
        AND year IS ?
        """, (
            title,
            author,
            album,
            year
        ))

        return cursor.fetchone() is not None


    def add_track(self, data):
        if self.track_exists(
            data["title"],
            data["author"],
            data["album"],
            data["year"]
        ):
            return False

        self.db.execute("""
        INSERT INTO tracks
        (
            title,
            author,
            album,
            year,
            file_path
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            data["title"],
            data["author"],
            data["album"],
            data["year"],
            data["file_path"]
        ))

        self.db.commit()

        return True