import sqlite3
from DB import DB_PATH

class Devices:
    def __init__(self):
        self.sql = sqlite3.connect(DB_PATH)
        self.create_sql_tables()

    def create_sql_tables(self):
        self.sql.executescript("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            device_uuid TEXT NOT NULL,
            device_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(user_id, device_uuid), -- Один пользователь не может иметь два устройства с одинаковым UUID
            
            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE);
        """)
        self.sql.commit()

    def add_device(self, user_id, device_uuid, device_name=None):
        cursor = self.sql.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO devices
        (user_id, device_uuid, device_name) VALUES (?, ?, ?)""",
                       (user_id, device_uuid, device_name))

        self.sql.commit()

    def update_last_seen(self, user_id, device_uuid):
        self.sql.execute("""
        UPDATE devices
        SET last_seen = CURRENT_TIMESTAMP
        WHERE user_id = ? AND device_uuid = ?""",
                         (user_id, device_uuid))
        self.sql.commit()

    def get_device(self, user_id, device_uuid):
        cursor = self.sql.cursor()
        cursor.execute("""
        SELECT * FROM devices
        WHERE user_id = ? AND device_uuid = ?""",
                       (user_id, device_uuid))
        return cursor.fetchone()

    def get_user_devices(self, user_id):
        cursor = self.sql.cursor()
        cursor.execute("""
        SELECT * FROM devices
        WHERE user_id = ?""", (user_id))
        return cursor.fetchall()

    def delete_old_devices(self, days=90):
        self.sql.execute("""
        DELETE FROM devices
        WHERE last_seen < datetime('now', ?)
        """, (f"-{days} days",))
        self.sql.commit()