from Playlist.Playlist import Playlist

pl = Playlist()
_db = Playlist().sql
def _get_cursor():
    return _db.cursor()


def create(name, owner_id=None, track_ids=None):
    return pl.create(name, owner_id, track_ids)

def delete(playlist_id: int):
    return pl.delete(playlist_id)

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
        SELECT p.id, p.name, p.owners, p.created_at, 
               COUNT(pt.track_id) as track_count
        FROM playlists p
        LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
        GROUP BY p.id, p.name, p.owners, p.created_at
        ORDER BY p.created_at DESC
    """)
    return [dict(row) for row in cursor.fetchall()]

def track_list(playlist_id):
    cursor = _get_cursor()
    cursor.execute("""
        SELECT 
            t.id,
            t.title,
            t.author,
            t.album,
            t.year,
            t.length,
            pt.position,
            pt.added_at
        FROM playlist_tracks pt
        JOIN tracks t ON pt.track_id = t.id
        WHERE pt.playlist_id = ?
        ORDER BY pt.position ASC, pt.added_at ASC
    """, (playlist_id,))
    return [dict(row) for row in cursor.fetchall()]