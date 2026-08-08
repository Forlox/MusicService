from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from Authentication.Auth import basic_scheme, keycloak_openid
from api.routers.tracks_router import track_router
from api.routers.users_router import user_router
from api.routers.playlist_router import playlist_router
from api.routers.stream_router import stream_router
from api.routers.queue_router import queue_router
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

# TODO
#  нужны эндпоинты:
#  - публичный для регистрации со всеми проверками

@app.post("/token")
async def get_token(credentials: HTTPBasicCredentials = Depends(basic_scheme)):
    try:
        token = keycloak_openid.token(
            username=credentials.username,
            password=credentials.password
        )
        logger.info(f"Выдан токен пользователю {credentials.username}")
        return {"access_token": token["access_token"], "token_type": "bearer"}
    except Exception:
        logger.warning(f"Неудачная попытка входа пользователя {credentials.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

app.include_router(user_router)
app.include_router(track_router)
app.include_router(playlist_router)
app.include_router(queue_router)
app.include_router(stream_router)