from Database import Database

class Queue:
    def __init__(self):
        self.sql = Database().sql_connect()
        self.create_sql_tables()

    def create_sql_tables(self):
        self.sql.executescript("""
        CREATE TABLE IF NOT EXISTS playback_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,  -- У пользователя может быть только одна очередь
            current_track_id INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(current_track_id)
                REFERENCES tracks(id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS queue_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            position INTEGER NOT NULL,

            FOREIGN KEY(queue_id)
                REFERENCES playback_queue(id)
                ON DELETE CASCADE,

            FOREIGN KEY(track_id)
                REFERENCES tracks(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_queue_tracks_order ON queue_tracks(queue_id, position);
        """)

        self.sql.commit()

    def _get_queue_id(self, user_id, create=True):
        cursor = self.sql.cursor()
        cursor.execute("SELECT id FROM playback_queue WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            return row[0]

        if not create:
            return None

        cursor.execute("INSERT INTO playback_queue(user_id) VALUES (?)", (user_id,))
        self.sql.commit()
        return cursor.lastrowid

    def _track_exists(self, track_id):
        cursor = self.sql.cursor()
        cursor.execute("SELECT 1 FROM tracks WHERE id = ?", (track_id,))
        return cursor.fetchone() is not None

    def _update_time(self, queue_id):
        self.sql.execute("""
        UPDATE playback_queue
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (queue_id,))


    def create(self, user_id, track_ids):
        queue_id = self._get_queue_id(user_id)
        cursor = self.sql.cursor()

        cursor.execute("DELETE FROM queue_tracks WHERE queue_id = ?", (queue_id,))
        cursor.execute("UPDATE playback_queue SET current_track_id = NULL WHERE id = ?", (queue_id,))

        added = []
        not_added = []
        for position, track_id in enumerate(track_ids):
            if not self._track_exists(track_id):
                not_added.append(track_id)
                continue

            cursor.execute(
                "INSERT INTO queue_tracks (queue_id, track_id, position) VALUES (?, ?, ?)",
                (queue_id, track_id, position)
            )
            added.append(track_id)

        self._update_time(queue_id)
        self.sql.commit()
        return added, not_added

    def add_tracks(self, user_id, track_ids):
        queue_id = self._get_queue_id(user_id)
        cursor = self.sql.cursor()

        cursor.execute(
            "SELECT COALESCE(MAX(position), -1) FROM queue_tracks WHERE queue_id = ?",
            (queue_id,)
        )
        position = cursor.fetchone()[0]

        added = []
        not_added = []
        for track_id in track_ids:
            if not self._track_exists(track_id):
                not_added.append(track_id)
                continue

            position += 1
            cursor.execute(
                "INSERT INTO queue_tracks (queue_id, track_id, position) VALUES (?, ?, ?)",
                (queue_id, track_id, position)
            )
            added.append(track_id)

        self._update_time(queue_id)
        self.sql.commit()
        return added, not_added

    def add_track(self, user_id, track_id):
        added, not_added = self.add_tracks(user_id, [track_id])
        return len(added) == 1

    def add_after_position(self, user_id, track_id, current_position):
        """Вставляет трек на current_position+1."""
        queue_id = self._get_queue_id(user_id)
        cursor = self.sql.cursor()

        if not self._track_exists(track_id):
            return False

        cursor.execute(
            "SELECT track_id FROM queue_tracks WHERE queue_id = ? ORDER BY position",
            (queue_id,)
        )
        current = [row[0] for row in cursor.fetchall()]

        # Трек вставляется после current_position. Отрицательные/большие значения — вставка, где допустимо
        if current_position < 0:
            current_position = 0
        elif current_position > len(current):
            current_position = len(current)

        reordered = current[:current_position + 1] + [track_id] + current[current_position + 1:]

        cursor.execute("DELETE FROM queue_tracks WHERE queue_id = ?", (queue_id,))
        for position, tid in enumerate(reordered):
            cursor.execute(
                "INSERT INTO queue_tracks (queue_id, track_id, position) VALUES (?, ?, ?)",
                (queue_id, tid, position)
            )

        self._update_time(queue_id)
        self.sql.commit()
        return True

    def remove_track(self, user_id, position):
        """Удаляет трек и сдвигает позиции других."""
        queue_id = self._get_queue_id(user_id, create=False)
        if queue_id is None:
            return False

        cursor = self.sql.cursor()
        cursor.execute(
            "SELECT 1 FROM queue_tracks WHERE queue_id = ? AND position = ?",
            (queue_id, position)
        )
        if not cursor.fetchone():
            return False

        cursor.execute(
            "DELETE FROM queue_tracks WHERE queue_id = ? AND position = ?",
            (queue_id, position)
        )
        cursor.execute(
            "UPDATE queue_tracks SET position = position - 1 WHERE queue_id = ? AND position > ?",
            (queue_id, position)
        )

        self._update_time(queue_id)
        self.sql.commit()
        return True

    def clear(self, user_id):
        queue_id = self._get_queue_id(user_id, create=False)
        if queue_id is None:
            return False

        self.sql.execute("DELETE FROM queue_tracks WHERE queue_id = ?", (queue_id,))
        # После очистки current_track_id не может ссылаться на трек, которого больше нет в очереди.
        self.sql.execute("UPDATE playback_queue SET current_track_id = NULL WHERE id = ?", (queue_id,))

        self._update_time(queue_id)
        self.sql.commit()
        return True

    def get_queue(self, user_id):
        queue_id = self._get_queue_id(user_id, create=False)
        if queue_id is None:
            return []

        cursor = self.sql.cursor()
        cursor.execute("""
            SELECT t.id, t.title, t.author, t.album, t.year, qt.position
            FROM queue_tracks qt
            JOIN tracks t ON qt.track_id = t.id
            WHERE qt.queue_id = ?
            ORDER BY qt.position ASC
        """, (queue_id,))
        return [dict(row) for row in cursor.fetchall()]

    def set_current_track(self, user_id, track_id):
        queue_id = self._get_queue_id(user_id)
        self.sql.execute("""
        UPDATE playback_queue
        SET current_track_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (track_id, queue_id))
        self.sql.commit()

    def delete_old_queues(self, days=7):
        self.sql.execute("""
        DELETE FROM playback_queue
        WHERE updated_at < datetime('now', ?)
        """, (f"-{days} days",))
        self.sql.commit()