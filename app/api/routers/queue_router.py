from fastapi import APIRouter, Depends

from Authentication.Auth import get_current_user
import Queue.interface as queue

queue_router = APIRouter(prefix="/queue", tags=["Queue"])

def _user_id(current_user: dict) -> str:
    return current_user["sub"]

@queue_router.post("/", description="Создание (пересоздание) очереди из списка id треков, допустимы дубликаты")
async def queue_create(
    track_ids: list[int],
    current_user: dict = Depends(get_current_user)):
    return queue.create(_user_id(current_user), track_ids)


@queue_router.get("/", description="Получение очереди треков")
async def queue_get(
    current_user: dict = Depends(get_current_user)):
    return queue.get_queue(_user_id(current_user))


@queue_router.post("/tracks", description="Добавить треки в конец очереди")
async def queue_add_tracks(
    track_ids: list[int],
    current_user: dict = Depends(get_current_user)):
    return queue.add_tracks(_user_id(current_user), track_ids)


@queue_router.post("/tracks/next", description="Вставляет трек после указанной позиции очереди")
async def queue_add_next(
    track_id: int,
    current_position: int,
    current_user: dict = Depends(get_current_user)):
    return queue.add_after_position(_user_id(current_user), track_id, current_position)


@queue_router.delete("/tracks/{position}", description="Убрать трек из очереди по позиции")
async def queue_remove_track(
    position: int,
    current_user: dict = Depends(get_current_user)):
    return queue.remove_track(_user_id(current_user), position)


@queue_router.delete("/", description="Очистить очередь")
async def queue_clear(
    current_user: dict = Depends(get_current_user)):
    return queue.clear(_user_id(current_user))