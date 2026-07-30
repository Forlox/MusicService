from fastapi import FastAPI, APIRouter, Depends
import MusicManager.interface as music
from Authentication.Auth import get_admin_user

app = FastAPI()

tracks = APIRouter(prefix="/tracks", tags=["Public"])

@tracks.get("/{track_id}")
def get_track_by_id(track_id: int):
    return music.get_track_by_id(track_id)

@tracks.get("/album")
def get_album(album: str, author: str | None = None):
    return music.get_tracks_by_album(album, author)

@tracks.get("/author")
def get_author_tracks(author: str):
    return music.get_tracks_by_author(author)

@tracks.get("/search")
def search(query: str):
    return music.search_tracks(query)


manage = APIRouter(prefix="/tracks", tags=["Admin"])

@manage.post("/add")
def add(file: str, admin_data: dict = Depends(get_admin_user)):
    return music.add_music_file(file)

@manage.delete("/{track_id}")
def delete_track(track_id: int, admin_data: dict = Depends(get_admin_user)):
    return {"deleted": music.delete_track_by_id(track_id)}

@manage.get("/full/{track_id}")
def get_track_by_id_full(track_id: int, dict = Depends(get_admin_user)):
    return music.get_track_by_id(track_id, False)

# Подключаем роутеры
app.include_router(tracks)
app.include_router(manage)