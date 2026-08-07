from pathlib import Path
from dotenv import load_dotenv

dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

from MusicManager.MusicManager import MusicManager, Music_DB_Manager
from Playlist.Playlist import Playlist
from MusicManager.Queue import Queue
# from Users.Devices import Devices
from Users.Users import Users
from Users.UserManager import UserManager
from Authentication.Keycloak import configure_keycloak

import uvicorn, api.api as api, os

# Нужно сохранять порядок вызова для sql таблиц
def initialize_database():
    Users()
    Music_DB_Manager()
    Playlist()
    # Devices()
    Queue()



def main():
    initialize_database()
    configure_keycloak()
    MusicManager().organize_files()
    UserManager().sync_all_users()

if __name__ == "__main__":
    main()
    uvicorn.run(api.app, host="127.0.0.1", port=8000)
