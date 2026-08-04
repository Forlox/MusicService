from fastapi import APIRouter

import MusicManager.interface as music

track_router = APIRouter(prefix="/tracks", tags=["Tracks Public"])

@track_router.get("/search")
async def search_tracks(query: str):
    return music.search_tracks(query)

@track_router.get("/{track_id}")
async def get_track_by_id(track_id: int):
    return music.get_track_by_id(track_id)

@track_router.get("/album")
async def get_album(album: str, author: str | None = None):
    return music.get_tracks_by_album(album, author)

@track_router.get("/author")
async def get_author_tracks(author: str):
    return music.get_tracks_by_author(author)

@track_router.get('/')
async def track_list():
    return music.get_track_list()

@track_router.get('/{track_id}')
async def get_track_file_location(id: int):
    return music.get_track_file_path_by_id(id)