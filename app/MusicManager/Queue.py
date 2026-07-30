from Database import Database

class Queue:
    def __init__(self):
        self.sql = Database().sql_connect()
        self.create_sql_tables()

    def create_sql_tables(self):
        self.sql.executescript("""
        CREATE TABLE IF NOT EXISTS playback_queue (
            id INTEGER PRIMARY KEY,
            device_id INTEGER NOT NULL UNIQUE, -- Устройство, которому принадлежит очередь
            current_track_id INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(device_id)
                REFERENCES devices(id)
                ON DELETE CASCADE,

            FOREIGN KEY(current_track_id)
                REFERENCES tracks(id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS queue_tracks (
            queue_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            position INTEGER NOT NULL,

            PRIMARY KEY(queue_id, track_id),
            
            FOREIGN KEY(queue_id)
                REFERENCES playback_queue(id)
                ON DELETE CASCADE,

            FOREIGN KEY(track_id)
                REFERENCES tracks(id)
                ON DELETE CASCADE
        );
        """)

        self.sql.commit()


    def create_queue(self, device_id, track_ids=None):
        cursor = self.sql.cursor()

        # Создаём очередь, если её ещё нет
        cursor.execute("INSERT OR IGNORE INTO playback_queue(device_id) VALUES (?)", (device_id,))

        cursor.execute("SELECT id FROM playback_queue WHERE device_id = ?", (device_id,))
        queue_id = cursor.fetchone()[0]

        if track_ids is not None: # is not None - пустой список должен очищать очередь
            self.clear(queue_id)
            for position, track_id in enumerate(track_ids):
                cursor.execute("""
                INSERT INTO queue_tracks
                (queue_id, track_id, position) VALUES (?, ?, ?)""",
                               (queue_id, track_id, position))
        self.update_time(queue_id)
        self.sql.commit()
        return queue_id

    def add_track(self, queue_id, track_id):
        cursor = self.sql.cursor()
        cursor.execute("""
        SELECT MAX(position)
        FROM queue_tracks
        WHERE queue_id = ?
        """, (queue_id,))

        position = cursor.fetchone()[0]

        if position is None: position = 0
        else: position += 1

        cursor.execute("""
        INSERT INTO queue_tracks
        VALUES (?, ?, ?)
        """, (queue_id, track_id, position))

        self.update_time(queue_id)
        self.sql.commit()


    def remove_track(self, queue_id, track_id):
        self.sql.execute("""
        DELETE FROM queue_tracks
        WHERE queue_id = ?
        AND track_id = ?
        """, (
            queue_id,
            track_id
        ))

        self.update_positions(queue_id)
        self.update_time(queue_id)
        self.sql.commit()


    def move_track(self, queue_id, track_id, new_position):
        cursor = self.sql.cursor()
        cursor.execute("""
        SELECT track_id
        FROM queue_tracks
        WHERE queue_id = ?
        ORDER BY position
        """, (queue_id,))

        tracks = [row[0] for row in cursor.fetchall()]
        tracks.remove(track_id)
        tracks.insert(new_position, track_id)

        self.clear(queue_id)

        for position, track in enumerate(tracks):
            cursor.execute("""
            INSERT INTO queue_tracks
            VALUES (?, ?, ?)
            """, (
                queue_id,
                track,
                position
            ))

        self.update_time(queue_id)
        self.sql.commit()


    def set_current_track(self, queue_id, track_id):
        self.sql.execute("""
        UPDATE playback_queue
        SET current_track_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (track_id, queue_id))

        self.sql.commit()


    def get_queue(self, queue_id):
        cursor = self.sql.cursor()
        cursor.execute("""
        SELECT track_id
        FROM queue_tracks
        WHERE queue_id = ?
        ORDER BY position
        """, (queue_id,))
        return [row[0] for row in cursor.fetchall()]


    def clear(self, queue_id):
        self.sql.execute("""
        DELETE FROM queue_tracks
        WHERE queue_id = ?
        """, (queue_id,))

        # После очистки current_track_id не может ссылаться на трек, которого больше нет в очереди.
        self.sql.execute("""
        UPDATE playback_queue
        SET current_track_id = NULL
        WHERE id = ?
        """, (queue_id,))


    def update_positions(self, queue_id):
        cursor = self.sql.cursor()
        cursor.execute("""
        SELECT track_id
        FROM queue_tracks
        WHERE queue_id = ?
        ORDER BY position
        """, (queue_id,))

        tracks = cursor.fetchall()

        for position, track in enumerate(tracks):
            cursor.execute("""
            UPDATE queue_tracks
            SET position = ?
            WHERE queue_id = ?
            AND track_id = ?
            """, (position, queue_id, track[0]))


    def update_time(self, queue_id):
        self.sql.execute("""
        UPDATE playback_queue
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (queue_id,))


    def delete_old_queues(self, days=7):
        self.sql.execute("""
        DELETE FROM playback_queue
        WHERE updated_at < datetime('now', ?)
        """, (f"-{days} days",))
        self.sql.commit()