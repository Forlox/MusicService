from fastapi import HTTPException, status
import json
from Playlist.Playlist import Playlist

pl = Playlist()
_db = Playlist().sql
def _get_cursor():
    return _db.cursor()


def check_owner_permission(playlist_id: int, user_id: str):
    """Проверяет, является ли пользователь владельцем плейлиста"""
    try:
        owners = pl.get_owners(playlist_id)
        if user_id not in owners:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User {user_id} is not an owner of playlist {playlist_id}"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


def create(name, owner_id=None, track_ids=None):
    playlist_id, not_added = pl.create(name, owner_id, track_ids)

    return {
        "playlist_id": playlist_id,
        "not_added": not_added,
        "message": (
            f"Создан плейлист с id: {playlist_id}"
            if not not_added
            else f"Создан плейлист с id: {playlist_id}. Не добавлены треки: {not_added}"
        )
    }

def delete(playlist_id: int):
    return {"message": pl.delete(playlist_id)}

def add_owner(playlist_id, user_id):
    return {"added": pl.add_owner(playlist_id, user_id)}

def add_tracks(playlist_id, track_ids):
    added, not_added = pl.add_tracks(playlist_id, track_ids)

    return {
        "added": added,
        "not_added": not_added
    }

def remove_track(playlist_id, track_id):
    return {"removed": pl.remove_track(playlist_id, track_id)}

def rename(playlist_id, new_name):
    return {"renamed": pl.rename(playlist_id, new_name)}

def set_main_owner(playlist_id, user_id):
    return {"changed": pl.set_main_owner(playlist_id, user_id)}

def get_owners(playlist_id):
    return {"owners": pl.get_owners(playlist_id)}

def get_main_owner(playlist_id):
    return {"owner": pl.get_main_owner(playlist_id)}

def list_playlists(current_user: dict = None):
    """Возвращает плейлисты. Обычный пользователь видит только свои, админ - все."""
    cursor = _get_cursor()
    cursor.execute("""
        SELECT p.id, p.name, p.owners, p.created_at, 
               COUNT(pt.track_id) as track_count
        FROM playlists p
        LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
        GROUP BY p.id, p.name, p.owners, p.created_at
        ORDER BY p.created_at DESC
    """)

    playlists = [dict(row) for row in cursor.fetchall()]

    if current_user is None: return playlists

    user_id = current_user.get("sub")
    is_admin = "admin" in current_user.get("realm_access", {}).get("roles", [])

    if is_admin: return playlists

    return [
        playlist for playlist in playlists
        if user_id in json.loads(playlist["owners"])
    ]

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