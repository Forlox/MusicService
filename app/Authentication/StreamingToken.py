import secrets
import time

tokens = {}
TOKEN_LIFETIME = 300

def create_stream_token(user_id: str, track_id: int):
    token = secrets.token_urlsafe(32)

    tokens[token] = {
        "user_id": user_id,
        "track_id": track_id,
        "expires": time.time() + TOKEN_LIFETIME
    }

    return token


def verify_stream_token(token: str, track_id: int):
    data = tokens.get(token)

    if not data:
        return False

    if data["expires"] < time.time():
        del tokens[token]
        return False

    if data["track_id"] != track_id:
        return False

    return True