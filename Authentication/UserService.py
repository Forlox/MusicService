import bcrypt
from Database import Database

class UserService:
    def __init__(self):
        self.sql = Database().sql_connect()

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def get_user_by_login(self, login: str):
        cursor = self.sql.cursor()
        cursor.execute("SELECT * FROM users WHERE login = ?", (login,))
        return cursor.fetchone()

    # Возвращает id пользователя, или None при неудачной аутентификации
    def authenticate(self, login: str, password: str):
        user = self.get_user_by_login(login)
        if not user or not user['is_active']:
            return None
        if not self.verify_password(password, user['password_hash']):
            return None

        cursor = self.sql.cursor()
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
        self.sql.commit()
        return user['id']