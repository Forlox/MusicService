from Database import Database
import json
import logging

logger = logging.getLogger(__name__)

class Playlist:
    def __init__(self):
        self.sql = Database().sql_connect()
        self.create_sql_tables()

    def create_sql_tables(self):
        self.sql.executescript("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owners TEXT NOT NULL DEFAULT '[]',  -- JSON массив [keycloak_id, ...], первый в списке - главный владелец
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS playlist_tracks (
            playlist_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (playlist_id, track_id),

            FOREIGN KEY (playlist_id)
                REFERENCES playlists(id)
                ON DELETE CASCADE,

            FOREIGN KEY (track_id)
                REFERENCES tracks(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_playlist_tracks_order ON playlist_tracks(playlist_id, position);
        """)
        self.sql.commit()

    def create(self, name, owner_keycloak_id=None, track_ids=None):
        cursor = self.sql.cursor()

        if track_ids is None:
            track_ids = []

        if owner_keycloak_id is not None:
            cursor.execute(
                "SELECT 1 FROM users WHERE keycloak_id = ?",
                (owner_keycloak_id,)
            )
            if not cursor.fetchone():
                return f"Пользователь с keycloak_id {owner_keycloak_id} не найден"

        owners = json.dumps([owner_keycloak_id]) if owner_keycloak_id is not None else "[]"

        cursor.execute(
            "INSERT INTO playlists (name, owners) VALUES (?, ?)",
            (name, owners)
        )

        playlist_id = cursor.lastrowid
        self.sql.commit()
        logger.info(f"Создан плейлист: id={playlist_id}, name='{name}'")

        _, not_added = self.add_tracks(playlist_id, track_ids)

        return playlist_id, not_added

    def add_owner(self, playlist_id, owner_keycloak_id):
        cursor = self.sql.cursor()

        cursor.execute("SELECT owners FROM playlists WHERE id = ?", (playlist_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Плейлист с id {playlist_id} не найден")

        cursor.execute(
            "SELECT 1 FROM users WHERE keycloak_id = ?",
            (owner_keycloak_id,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Пользователь с keycloak_id {owner_keycloak_id} не найден")

        owners = json.loads(row[0])

        if owner_keycloak_id in owners:
            logger.debug(f"Владелец уже есть: playlist={playlist_id}, owner={owner_keycloak_id}")
            return False

        owners.append(owner_keycloak_id)
        cursor.execute(
            "UPDATE playlists SET owners = ? WHERE id = ?",
            (json.dumps(owners), playlist_id)
        )
        self.sql.commit()
        logger.info(f"Добавлен владелец {owner_keycloak_id} плейлиста {playlist_id}")
        return True

    def add_tracks(self, playlist_id, track_ids):
        """Берет список id треков и добавляет в плейлист"""
        cursor = self.sql.cursor()

        cursor.execute("SELECT id FROM playlists WHERE id = ?", (playlist_id,))
        if not cursor.fetchone():
            return f"Плейлист с id {playlist_id} не найден"

        cursor.execute(
            "SELECT COALESCE(MAX(position), -1) FROM playlist_tracks WHERE playlist_id = ?",
            (playlist_id,)
        )
        max_pos = cursor.fetchone()[0]

        added = 0
        not_added = []

        for track_id in track_ids:
            if track_id == 0:
                continue

            cursor.execute(
                "SELECT 1 FROM tracks WHERE id = ?",
                (track_id,)
            )
            if not cursor.fetchone():
                not_added.append(track_id)
                continue

            max_pos += 1
            cursor.execute(
                """
                INSERT OR IGNORE INTO playlist_tracks (playlist_id, track_id, position)
                VALUES (?, ?, ?)
                """,
                (playlist_id, track_id, max_pos)
            )

            if cursor.rowcount:
                added += 1

        self.sql.commit()
        logger.info(f"В плейлист {playlist_id} добавлено треков: {added}, не найдено: {len(not_added)}")
        return added, not_added

    def remove_track(self, playlist_id, track_id):
        cursor = self.sql.cursor()

        # Проверка существования
        cursor.execute(
            "SELECT position FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
            (playlist_id, track_id)
        )
        row = cursor.fetchone()
        if not row:
            logger.debug(f"Трек не найден в плейлисте: playlist={playlist_id}, track={track_id}")
            return False

        deleted_position = row[0]
        cursor.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
            (playlist_id, track_id)
        )

        # Сдвигаем позиции всех последующих треков вверх
        cursor.execute("""
        UPDATE playlist_tracks
        SET position = position - 1
        WHERE playlist_id = ? AND position > ?
        """, (playlist_id, deleted_position))

        self.sql.commit()
        logger.info(f"Трек {track_id} удален из плейлиста {playlist_id}")
        return True

    def rename(self, playlist_id, new_name):
        cursor = self.sql.cursor()
        cursor.execute(
            "UPDATE playlists SET name = ? WHERE id = ?",
            (new_name, playlist_id)
        )

        if cursor.rowcount == 0:
            raise ValueError(f"Плейлист с id {playlist_id} не найден")

        self.sql.commit()
        logger.info(f"Плейлист {playlist_id} переименован в '{new_name}'")
        return True

    def set_main_owner(self, playlist_id, owner_keycloak_id):
        cursor = self.sql.cursor()

        cursor.execute("SELECT owners FROM playlists WHERE id = ?", (playlist_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Плейлист с id {playlist_id} не найден")

        owners = json.loads(row[0])

        if owner_keycloak_id not in owners:
            raise ValueError(f"Пользователь {owner_keycloak_id} не является владельцем плейлиста")

        owners.remove(owner_keycloak_id)
        owners.insert(0, owner_keycloak_id)

        cursor.execute(
            "UPDATE playlists SET owners = ? WHERE id = ?",
            (json.dumps(owners), playlist_id)
        )
        self.sql.commit()
        logger.info(f"Главный владелец плейлиста {playlist_id}: {owner_keycloak_id}")
        return True

    def get_owners(self, playlist_id):
        cursor = self.sql.cursor()
        cursor.execute("SELECT owners FROM playlists WHERE id = ?", (playlist_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Плейлист с id {playlist_id} не найден")

        return json.loads(row[0])

    def get_main_owner(self, playlist_id):
        owners = self.get_owners(playlist_id)
        return owners[0] if owners else None

    def delete(self, playlist_id):
        cursor = self.sql.cursor()

        cursor.execute("SELECT name FROM playlists WHERE id = ?",(playlist_id,))
        row = cursor.fetchone()

        if not row:
            logger.warning(f"Удаление несуществующего плейлиста: id={playlist_id}")
            return f"Плейлист с id {playlist_id} не найден"

        playlist_name = row[0]
        cursor.execute(
            "DELETE FROM playlists WHERE id = ?",
            (playlist_id,)
        )

        self.sql.commit()
        logger.info(f"Плейлист '{playlist_name}' (id={playlist_id}) удален")
        return f'Плейлист «{playlist_name}» (id={playlist_id}) успешно удален'