from pathlib import Path
from dotenv import load_dotenv

dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

import logging
import uvicorn, api.api as api

from logging_config import configure_logging
from MusicManager.MusicManager import MusicManager, Music_DB_Manager
from Playlist.Playlist import Playlist
from Queue.Queue import Queue
# from Users.Devices import Devices
from Users.Users import Users
from Users.UserManager import UserManager
from Authentication.Keycloak import configure_keycloak

logger = logging.getLogger(__name__)


# Нужно сохранять порядок вызова для sql таблиц
def initialize_database():
    Users()
    Music_DB_Manager()
    Playlist()
    # Devices()
    Queue()


def main():
    configure_logging()
    logger.info("Запуск Music Service")
    initialize_database()
    logger.info("База данных инициализирована")
    configure_keycloak()
    logger.info("Keycloak настроен")
    MusicManager().organize_files()
    logger.info("Музыкальные файлы организованы")
    UserManager().sync_all_users()
    logger.info("Пользователи синхронизированы")

if __name__ == "__main__":
    main()
    uvicorn.run(api.app, host="127.0.0.1", port=8000)
