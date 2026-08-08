from fastapi import HTTPException, status
from Queue.Queue import Queue
import logging

logger = logging.getLogger(__name__)

queue = Queue()

def create(user_id: str, track_ids: list[int]):
    """Создаёт (пересоздаёт) очередь"""
    added, not_added = queue.create(user_id, track_ids)
    return {
        "added": added,
        "not_added": not_added,
        "message": (
            "Очередь создана" if not not_added else f"Очередь создана. Не добавлены треки: {not_added}"
        )
    }

def get_queue(user_id: str):
    return {"queue": queue.get_queue(user_id)}

def add_tracks(user_id: str, track_ids: list[int]):
    """Добавляет треки в конец очереди."""
    added, not_added = queue.add_tracks(user_id, track_ids)
    return {
        "added": added,
        "not_added": not_added
    }

def add_after_position(user_id: str, track_id: int, current_position: int):
    added = queue.add_after_position(user_id, track_id, current_position)
    if not added:
        logger.warning(f"Не удалось вставить трек {track_id} в очередь пользователя {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Трек с id {track_id} не найден"
        )
    return {"added": track_id, "position": current_position + 1}

def remove_track(user_id: str, position: int):
    removed = queue.remove_track(user_id, position)
    if not removed:
        logger.warning(f"Не удалось удалить трек на позиции {position} из очереди пользователя {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"В очереди нет трека на позиции {position}"
        )
    return {"removed": True, "position": position}

def clear(user_id: str):
    return {"cleared": queue.clear(user_id)}