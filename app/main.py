from pathlib import Path
from dotenv import load_dotenv

dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# TODO исправь эту кашу под формат "from * import *"
import MusicManager.MusicManager as MusicManager
import Playlist.Playlist as Playlist
import MusicManager.Queue as Queue
import Users.Devices as Devices
import Users.Users as Users
from Users.UserManager import UserManager

import uvicorn, api.api as api

# Нужно сохранять порядок вызова для sql таблиц
def initialize_database():
    Users.Users()
    MusicManager.Music_DB_Manager()
    Playlist.Playlist()
    Devices.Devices()
    Queue.Queue()

def main():
    initialize_database()
    MusicManager.MusicManager().organize_files()
    UserManager().sync_all_users()

if __name__ == "__main__":
    main()
    uvicorn.run(api.app, host="127.0.0.1", port=8000)
