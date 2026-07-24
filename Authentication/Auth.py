from datetime import datetime, timedelta, timezone
import os
from Database import Database

import bcrypt
from jose import JWTError, jwt

ALGORITHM = "HS256"
TOKEN_TIME = 60 * 24

class Auth:
    def __init__(self):
        self.sql = Database().sql_connect()
        self.create_sql_tables()

    def create_sql_tables(self):
        columns = {row["name"] for row in self.sql.execute("PRAGMA table_info(users)")}
        # if not columns:
        #     raise RuntimeError("Сначала создайте таблицу users через Users().")

        if "two_factor_enabled" not in columns: # вайбкод: без проверки ALTER TABLE падает при каждом следующем запуске.
            self.sql.execute("ALTER TABLE users ADD COLUMN two_factor_enabled INTEGER DEFAULT 0")
        if "two_factor_secret" not in columns:
            self.sql.execute("ALTER TABLE users ADD COLUMN two_factor_secret TEXT")

        self.sql.commit()

    @staticmethod
    def _secret_key():
        secret_key = os.getenv("JWT_KEY")
        if not secret_key:
            raise RuntimeError("Нет JWT ключа в .env.")
        return secret_key

    def verify_password(self, password, password_hash):
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def login(self, login, password):
        cursor = self.sql.cursor()
        cursor.execute("""
        SELECT id, password_hash, is_active FROM users
        WHERE login = ?
        """, (login,))

        user = cursor.fetchone()

        if not user:
            return None

        user_id = user[0]
        password_hash = user[1]
        is_active = user[2]

        if not is_active:
            return None
        if not self.verify_password(password, password_hash):
            return None

        self.sql.execute("""
        UPDATE users
        SET last_login = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (user_id,))

        self.sql.commit()
        return self.create_token(user_id)

    def create_token(self, user_id):
        payload = {
            "user_id": user_id,
            "exp":
                datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TIME)
        }

        return jwt.encode(payload, self._secret_key(), algorithm=ALGORITHM)

    def verify_token(self, token):
        try:
            payload = jwt.decode(token, self._secret_key(), algorithms=[ALGORITHM])
            return payload["user_id"]

        except (JWTError, KeyError):
            return None