from pathlib import Path
from dotenv import load_dotenv

dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

from MusicManager.MusicManager import MusicManager, Music_DB_Manager
from Playlist.Playlist import Playlist
from MusicManager.Queue import Queue
from Users.Devices import Devices
from Users.Users import Users
from Users.UserManager import UserManager

import uvicorn, api.api as api

# Нужно сохранять порядок вызова для sql таблиц
def initialize_database():
    Users()
    Music_DB_Manager()
    Playlist()
    Devices()
    Queue()

# TODO везде сделать логгер и настроить его тут (пример в UserManager)
# TODO поменять СУБД на Postgres по возможности

def main():
    initialize_database()
    MusicManager().organize_files()
    UserManager().sync_all_users()

if __name__ == "__main__":
    main()
    uvicorn.run(api.app, host="127.0.0.1", port=8000)
