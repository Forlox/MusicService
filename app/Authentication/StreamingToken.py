import secrets
import time
import logging

logger = logging.getLogger(__name__)

tokens = {}
def create_stream_token(user_id: str, track_id: int, token_lifetime=600):
    token = secrets.token_urlsafe(32)
    tokens[token] = {
        "user_id": user_id,
        "track_id": track_id,
        "expires": time.time() + token_lifetime
    }
    logger.debug(f"Создан stream-токен для user={user_id}, track={track_id}")
    return token


def verify_stream_token(token: str, track_id: int):
    data = tokens.get(token)

    if not data:
        logger.warning(f"Попытка использования несуществующего stream-токена для track={track_id}")
        return False

    if data["expires"] < time.time():
        del tokens[token]
        logger.warning(f"Использован просроченный stream-токен для track={track_id}")
        return False

    if data["track_id"] != track_id:
        logger.warning("Stream-токен использован для другого трека")
        return False

    return True