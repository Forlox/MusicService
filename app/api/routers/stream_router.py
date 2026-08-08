import os
import logging
from fastapi import APIRouter, Request, Depends, HTTPException

from MusicManager.StreaminService import stream_file
import MusicManager.interface as music

from Authentication.Auth import get_current_user
from Authentication.StreamingToken import create_stream_token, verify_stream_token

logger = logging.getLogger(__name__)

stream_router = APIRouter(
    prefix="/stream",
    tags=["Streaming"]
)

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

@stream_router.get("/{track_id}/url", description='Получаем ссылку на стрим через bearer токен')
async def get_stream_url(track_id: int, current_user: dict = Depends(get_current_user)):
    track_path = music.get_track_file_path_by_id(track_id)
    if not track_path:
        logger.warning(f"Запрос стрим-ссылки на отсутствующий трек {track_id}")
        raise HTTPException(
            status_code=404,
            detail="Track not found"
        )
    token = create_stream_token(current_user["sub"], track_id)
    logger.info(f"Создана стрим-ссылка на трек {track_id} для пользователя {current_user['sub']}")
    return { "url": f"{BASE_URL}/stream/play/{track_id}?token={token}" }

@stream_router.get("/play/{track_id}")
async def play_stream(track_id: int, request: Request, token: str):
    if not verify_stream_token(token, track_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid stream token"
        )

    track_path = music.get_track_file_path_by_id(track_id)
    if not track_path:
        logger.warning(f"Попытка стрима отсутствующего трека: {track_id}")
        raise HTTPException(
            status_code=404,
            detail="Track not found"
        )

    logger.debug(f"Стрим трека {track_id}")
    return stream_file(track_path, request)