from DB import DB_PATH
import sqlite3

class Playlist:

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()


    def create_tables(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            creator_id INTEGER,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (creator_id)
                REFERENCES users(id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS playlist_tracks (
            playlist_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,

            position INTEGER NOT NULL,

            PRIMARY KEY (playlist_id, track_id),

            FOREIGN KEY (playlist_id)
                REFERENCES playlists(id)
                ON DELETE CASCADE,

            FOREIGN KEY (track_id)
                REFERENCES tracks(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_playlists (
            user_id INTEGER NOT NULL,
            playlist_id INTEGER NOT NULL,

            PRIMARY KEY (user_id, playlist_id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (playlist_id)
                REFERENCES playlists(id)
                ON DELETE CASCADE
        );
        """)

        self.conn.commit()


    def create(self, name, track_ids, creator_id=None):
        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO playlists (
            name,
            creator_id
        )
        VALUES (?, ?)
        """, (
            name,
            creator_id
        ))

        playlist_id = cursor.lastrowid

        for position, track_id in enumerate(track_ids):
            cursor.execute("""
            INSERT INTO playlist_tracks (
                playlist_id,
                track_id,
                position
            )
            VALUES (?, ?, ?)
            """, (
                playlist_id,
                track_id,
                position
            ))

        if creator_id is not None:
            cursor.execute("""
            INSERT INTO user_playlists (
                user_id,
                playlist_id
            )
            VALUES (?, ?)
            """, (
                creator_id,
                playlist_id
            ))

        self.conn.commit()

        return playlist_id