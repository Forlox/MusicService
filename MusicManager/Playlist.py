from Database import Database

class Playlist:
    def __init__(self):
        self.sql = Database().sql_connect()
        self.create_sql_tables()

    def create_sql_tables(self):
        self.sql.executescript("""
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

        columns = {row["name"] for row in self.sql.execute("PRAGMA table_info(playlists)")}
        if "creator_id" not in columns:
            self.sql.execute("ALTER TABLE playlists ADD COLUMN creator_id INTEGER")

        self.sql.commit()

    def create(self, name, track_ids, creator_id=None):
        cursor = self.sql.cursor()
        cursor.execute("""
        INSERT INTO playlists (name, creator_id)
        VALUES (?, ?)
        """, (name, creator_id))

        playlist_id = cursor.lastrowid

        for position, track_id in enumerate(track_ids):
            cursor.execute("""
            INSERT INTO playlist_tracks (playlist_id, track_id, position)
            VALUES (?, ?, ?)
            """, (playlist_id, track_id,position))

        if creator_id is not None:
            cursor.execute("""
            INSERT INTO user_playlists (user_id, playlist_id)
            VALUES (?, ?)
            """, (creator_id, playlist_id))

        self.sql.commit()
        return playlist_id