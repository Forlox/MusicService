import Authentication.Auth as Auth
import MusicManager.MusicManager as MusicManager
import MusicManager.Playlist as Playlist
import MusicManager.Queue as Queue
import Users.Devices as Devices
import Users.Users as Users
import Database

# Нужно сохранять порядок вызова для sql таблиц
def initialize_database():
    Users.Users()
    MusicManager.Music_DB_Manager()
    Playlist.Playlist()
    Devices.Devices()
    Queue.Queue()
    Auth.Auth()

def main():
    initialize_database()
    MusicManager.MusicManager().run()

if __name__ == "__main__":
    main()

    Database.sql_console()
