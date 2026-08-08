from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

import MusicManager.interface as music
from Authentication.Auth import get_current_user, require_roles, require_active_user
from MusicManager.FileManager import ALLOWED_EXTENSIONS, MUSIC_DIR

track_router = APIRouter(
    prefix="/tracks",
    tags=["Tracks"],
    dependencies=[Depends(get_current_user)],
)

@track_router.get("/search", dependencies=[Depends(require_active_user())])
async def search_tracks(query: str):
    return music.search_tracks(query)

@track_router.get("/{track_id}", dependencies=[Depends(require_active_user())])
async def get_track_by_id(track_id: int):
    return music.get_track_by_id(track_id)

@track_router.get("/album", dependencies=[Depends(require_active_user())])
async def get_album(album: str, author: str | None = None):
    return music.get_tracks_by_album(album, author)

@track_router.get("/author", dependencies=[Depends(require_active_user())])
async def get_author_tracks(author: str):
    return music.get_tracks_by_author(author)

@track_router.get('/', dependencies=[Depends(require_active_user())])
async def track_list():
    return music.get_track_list()

@track_router.get('/{track_id}', dependencies=[Depends(require_active_user())])
async def get_track_file_location(id: int):
    return music.get_track_file_path_by_id(id)

@track_router.post("/add", dependencies=[Depends(require_roles("upload"))],
                   description="Требует роль upload. Существование файла проверяет по метаданным: название, автор, альбом, год.")
async def add_music_file(file: UploadFile = File(...)):
    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Поддерживаемые файлы: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    destination = MUSIC_DIR / file.filename

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        await file.close()

    added = music.add_music_file(destination)

    if not added:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=409,
            detail="Такой трек уже существует."
        )

    return {
        "message": "Файл успешно загружен.",
        "filename": file.filename
    }

@track_router.delete("/{track_id}", dependencies=[Depends(require_roles("manage"))])
async def delete_track(track_id: int):
    return {"deleted": music.delete_track_by_id(track_id)}