from Database import Database
import logging

logger = logging.getLogger(__name__)

class Users:
    def __init__(self):
        self.sql = Database().sql_connect()
        self.create_sql_tables()

    def create_sql_tables(self):
        self.sql.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keycloak_id TEXT NOT NULL UNIQUE,      -- UUID из Keycloak
            login TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            is_admin INTEGER NOT NULL DEFAULT 0,   -- дублируется из ролей Keycloak
            is_active INTEGER NOT NULL DEFAULT 1   -- дублируется из enabled в Keycloak
        );
        """)
        self.sql.commit()

    def get_user_by_keycloak_id(self, keycloak_id: str):
        cursor = self.sql.cursor()
        cursor.execute("SELECT * FROM users WHERE keycloak_id = ?", (keycloak_id,))
        return cursor.fetchone()

    def get_all_local_users(self):
        cursor = self.sql.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()

    def create_local_user(self, keycloak_id: str, login: str, is_admin: bool = False, is_active: bool = True):
        """Создаёт запись в локальной БД после успешного создания в Keycloak."""
        cursor = self.sql.cursor()
        # Проверяем, нет ли уже такого keycloak_id
        cursor.execute("SELECT id FROM users WHERE keycloak_id = ?", (keycloak_id,))
        if cursor.fetchone():
            logger.debug(f"Пользователь {keycloak_id} уже существует локально")
            return False  # или выбросить исключение
        cursor.execute("""
            INSERT INTO users (keycloak_id, login, is_admin, is_active)
            VALUES (?, ?, ?, ?)
        """, (keycloak_id, login, int(is_admin), int(is_active)))
        self.sql.commit()
        logger.info(f"Создана локальная запись пользователя {keycloak_id} (login={login})")
        return True

    def update_local_user(self, keycloak_id: str, login: str = None,
                          is_admin: bool = None, is_active: bool = None):
        """Обновляет локальные данные пользователя (без last_login)."""
        updates = []
        params = []
        if login is not None:
            updates.append("login = ?")
            params.append(login)
        if is_admin is not None:
            updates.append("is_admin = ?")
            params.append(int(is_admin))
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(int(is_active))
        if not updates:
            return
        params.append(keycloak_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE keycloak_id = ?"
        self.sql.execute(query, params)
        self.sql.commit()

    def delete_local_user(self, keycloak_id: str):
        self.sql.execute("DELETE FROM users WHERE keycloak_id = ?", (keycloak_id,))
        self.sql.commit()
        logger.info(f"Удалена локальная запись пользователя {keycloak_id}")

    def update_last_login(self, keycloak_id: str):
        self.sql.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE keycloak_id = ?",
            (keycloak_id,)
        )
        self.sql.commit()
        logger.debug(f"Обновлено last_login для пользователя {keycloak_id}")


    def add_user(self, login, is_admin=False):
        # Устаревший метод, рекомендуется использовать create_local_user с keycloak_id
        cursor = self.sql.cursor()
        cursor.execute("SELECT id FROM users WHERE login=?", (login,))
        if cursor.fetchone():
            return False
        cursor.execute("""
            INSERT INTO users (login, is_admin)
            VALUES (?, ?)
        """, (login, int(is_admin)))
        self.sql.commit()
        return True

    def get_user(self, login):
        cursor = self.sql.cursor()
        cursor.execute("SELECT * FROM users WHERE login = ?", (login,))
        return cursor.fetchone()

    def add_playlist(self, user_id, playlist_id):
        self.sql.execute("INSERT OR IGNORE INTO user_playlists VALUES (?, ?)",
                         (user_id, playlist_id))
        self.sql.commit()

    def remove_playlist(self, user_id, playlist_id):
        self.sql.execute("DELETE FROM user_playlists WHERE user_id = ? AND playlist_id = ?",
                         (user_id, playlist_id))
        self.sql.commit()

    def set_admin(self, user_id, isAdmin=True):
        self.sql.execute("UPDATE users SET is_admin = ? WHERE id = ?",
                         (int(isAdmin), user_id)) # int потому что в бд нет bool

        self.sql.commit()

    def set_active(self, user_id, isActive=True):
        self.sql.execute("UPDATE users SET is_active = ? WHERE id = ?",
                         (int(isActive),user_id)) # int потому что в бд нет bool
        self.sql.commit()