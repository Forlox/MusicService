import bcrypt
import sqlite3
from DB import DB_PATH

class Users:
    def __init__(self):
        self.sql = sqlite3.connect(DB_PATH)
        self.create_tables()

    def create_tables(self):
        self.sql.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            login TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,

            is_admin INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_playlists (
            user_id INTEGER NOT NULL,
            playlist_id INTEGER NOT NULL,

            PRIMARY KEY (user_id, playlist_id),

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(playlist_id)
                REFERENCES playlists(id)
                ON DELETE CASCADE
        );
        """)

        self.sql.commit()

    def hash_password(self, password):
        return bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

    # Для сравнения хэшей паролей, напрямую нельзя строки сравнивать из-за приколов шифрования
    def verify_password(self, password, password_hash):
        return bcrypt.checkpw(
            password.encode(),
            password_hash.encode()
        )


    def add_user(self, login, password, is_admin=False):
        cursor = self.sql.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE login=?",
            (login,)
        )

        if cursor.fetchone():
            return False

        cursor.execute("""
        INSERT INTO users (
            login,
            password_hash,
            is_admin
        )
        VALUES (?, ?, ?)
        """, (
            login,
            self.hash_password(password),
            int(is_admin)
        ))

        self.sql.commit()
        return True


    def login(self, login, password):
        cursor = self.sql.cursor()

        cursor.execute("""
        SELECT
            id,
            password_hash,
            is_active
        FROM users
        WHERE login=?
        """, (login,))

        user = cursor.fetchone()

        if not user:
            return None

        if not user[2]:
            return None

        if not self.verify_password(password, user[1]):
            return None

        cursor.execute("""
        UPDATE users
        SET last_login = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (user[0],))

        self.sql.commit()

        return user[0]


    def get_user(self, login):
        cursor = self.sql.cursor()

        cursor.execute("""
        SELECT *
        FROM users
        WHERE login = ?
        """, (login,))

        return cursor.fetchone()

    def add_playlist(self, user_id, playlist_id):
        self.sql.execute("""
        INSERT OR IGNORE INTO user_playlists
        VALUES (?, ?)
        """, (
            user_id,
            playlist_id
        ))

        self.sql.commit()

    def remove_playlist(self, user_id, playlist_id):
        self.sql.execute("""
        DELETE FROM user_playlists
        WHERE user_id = ?
        AND playlist_id = ?
        """, (
            user_id,
            playlist_id
        ))

        self.sql.commit()

    def set_admin(self, user_id, isAdmin=True):
        self.sql.execute("""
        UPDATE users
        SET is_admin = ?
        WHERE id = ?
        """, (
            int(isAdmin),
            user_id
        ))

        self.sql.commit()

    def set_active(self, user_id, isActive=True):
        self.sql.execute("""
        UPDATE users
        SET is_active = ?
        WHERE id = ?
        """, (
            int(isActive),
            user_id
        ))

        self.sql.commit()


if __name__ == "__main__":
    Users().create_tables()
    Users().set_admin(1, True)