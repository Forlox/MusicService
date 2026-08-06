from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from Authentication.Auth import get_admin_user
import MusicManager.interface as music

manage_router = APIRouter(
    prefix="/tracks",
    tags=["Admin"],
    dependencies=[Depends(get_admin_user)]
)

from MusicManager.FileManager import ALLOWED_EXTENSIONS, MUSIC_DIR


#TODO
# Сделать доступ по роли
# При отсутствии метаданных брать "название, автор, альбом, год"
@manage_router.post("/add", description="Существование файла проверяет по метаданным: название, автор, альбом, год")
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


@manage_router.delete("/{track_id}")
async def delete_track(track_id: int):
    return {"deleted": music.delete_track_by_id(track_id)}

# @manage_router.get("/full/{track_id}")
# async def get_track_by_id_full(track_id: int):
#     return music.get_track_by_id(track_id, False)