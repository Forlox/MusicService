from fastapi import APIRouter, Depends

from Authentication.Auth import get_admin_user
import MusicManager.interface as music

manage_router = APIRouter(
    prefix="/tracks",
    tags=["Admin"],
    dependencies=[Depends(get_admin_user)]
)
# TODO сделать нормальную загрузку файлов
# @manage_router.post("/add")
# async def add_music_file(file: str):
#     return music.add_music_file(file)

@manage_router.delete("/{track_id}")
async def delete_track(track_id: int):
    return {"deleted": music.delete_track_by_id(track_id)}

@manage_router.get("/full/{track_id}")
async def get_track_by_id_full(track_id: int):
    return music.get_track_by_id(track_id, False)