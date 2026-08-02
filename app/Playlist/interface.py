from Playlist.Playlist import Playlist
from Database import Database

pl = Playlist()
_db = Playlist().sql
def _get_cursor():
    return _db.cursor()


def create(name, owner_id=None, track_ids=None):
    return pl.create(name, owner_id, track_ids)

def add_owner(playlist_id, user_id):
    return pl.add_owner(playlist_id, user_id)

def add_tracks(playlist_id, track_ids):
    return pl.add_tracks(playlist_id, track_ids)

def remove_track(playlist_id, track_id):
    return pl.remove_track(playlist_id, track_id)

def rename(playlist_id, new_name):
    return pl.rename(playlist_id, new_name)

def set_main_owner(playlist_id, user_id):
    return pl.set_main_owner(playlist_id, user_id)

def get_owners(playlist_id):
    return pl.get_owners(playlist_id)

def get_main_owner(playlist_id):
    return pl.get_main_owner(playlist_id)

def list_playlists():
    cursor = _get_cursor()
    cursor.execute("""
        SELECT id, name, owners, created_at
        FROM playlists
        ORDER BY created_at DESC
    """)
    return [dict(row) for row in cursor.fetchall()]