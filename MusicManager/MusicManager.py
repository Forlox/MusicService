from FileManager import FileManager
from DB_Manager import DB_Manager

class MusicManager:
    def __init__(self):
        self.db = DB_Manager()
        self.file_manager = FileManager()

    def run(self):
        self.file_manager.run()

        for track in self.file_manager.tracks:
            add = self.db.add_track(track)
            if add:
                print(f"Добавлен в БД: {track['title']} | {track['author']} | {track['album']} | {track['year']}")
            else:
                print(f"Уже существует: {track['title']} | {track['author']} | {track['album']} | {track['year']}")


if __name__ == "__main__":
    manager = MusicManager()
    manager.run()