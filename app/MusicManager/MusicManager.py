from MusicManager.FileManager import FileManager
from Database import Database
from pathlib import Path
import os

class MusicManager:
    def __init__(self):
        self.db = Music_DB_Manager()
        self.file_manager = FileManager()

    def organize_files(self, printLogs=False):
        self.file_manager.run()

        for track in self.file_manager.tracks:
            add = self.db.add_track(track)
            if printLogs:
                if add:
                    print(f"Добавлен в БД: {track['title']} | {track['author']} | {track['album']} | {track['year']} | {track['length']} сек")
                else:
                    print(f"Уже существует: {track['title']} | {track['author']} | {track['album']} | {track['year']} | {track['length']} сек")

    def add_music_file(self, file_path, printLogs=False):
        from pathlib import Path
        file_path = Path(file_path)

        if not file_path.exists():
            if printLogs:
                print(f"Файл не найден: {file_path}")
            return False

        # Проверяем расширение файла
        if file_path.suffix.lower() not in FileManager.EXTENSIONS:
            if printLogs:
                print(f"Неподдерживаемый формат файла: {file_path.suffix}")
            return False

        self.file_manager.process(file_path)

        if self.file_manager.tracks:
            track = self.file_manager.tracks[-1]  # Последний добавленный трек
            add = self.db.add_track(track)

            if printLogs:
                if add:
                    print(
                        f"Добавлен в БД: {track['title']} | {track['author']} | {track['album']} | {track['year']} | {track['length']} сек")
                else:
                    print(
                        f"Уже существует: {track['title']} | {track['author']} | {track['album']} | {track['year']} | {track['length']} сек")

            return add
        else:
            if printLogs:
                print(f"Не удалось обработать файл: {file_path}")
            return False

    def delete_track(self, track_id, printLogs=False):
        """ Возвращает True - удален файл, False - не удален """
        try:
            cursor = self.db.sql.cursor()
            cursor.execute("SELECT file_path, title, author FROM tracks WHERE id = ?", (track_id,))
            track_data = cursor.fetchone()

            if not track_data:
                if printLogs:
                    print(f"Трек с ID {track_id} не найден в базе данных")
                return False

            file_path = track_data[0]
            title = track_data[1]
            author = track_data[2]

            if file_path:
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    try:
                        os.remove(file_path_obj)
                        if printLogs:
                            print(f"Удален файл: {file_path}")
                    except (OSError, PermissionError) as e:
                        if printLogs:
                            print(f"Ошибка при удалении файла {file_path}: {e}")
                        return False
                else:
                    if printLogs:
                        print(f"Файл не найден на диске: {file_path}")

            cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
            self.db.sql.commit()

            if printLogs:
                print(f"Трек '{title}' | {author} (ID: {track_id}) успешно удален")
            return True
        except Exception as e:
            if printLogs:
                print(f"Ошибка при удалении трека: {e}")
            return False


class Music_DB_Manager:
    def __init__(self):
        self.sql = Database().sql_connect()
        self.create_sql_tables()

    def create_sql_tables(self):
        self.sql.executescript("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            album TEXT,
            year TEXT,
            file_path TEXT NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            length INTEGER  -- длина в секундах
        );
        """)
        self.sql.commit()

    def track_exists(self, title, author, album, year):
        cursor = self.sql.cursor()
        cursor.execute("""
        SELECT id FROM tracks
        WHERE title = ?
        AND author = ?
        AND album IS ?
        AND year IS ?
        """, (title, author, album, year))
        return cursor.fetchone() is not None

    def add_track(self, data):
        if self.track_exists(data["title"], data["author"], data["album"], data["year"]):
            self.sql.execute("""
            UPDATE tracks SET length = ?
            WHERE title = ? AND author = ? AND album IS ? AND year IS ?
            """, (data["length"], data["title"], data["author"], data["album"], data["year"]))
            self.sql.commit()
            return False

        self.sql.execute("""
        INSERT INTO tracks (title, author, album, year, file_path, length)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (data["title"], data["author"], data["album"], data["year"], data["file_path"], data["length"]))
        self.sql.commit()
        return True


if __name__ == "__main__":
    manager = MusicManager()
    manager.organize_files()