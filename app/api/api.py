from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from Authentication.Auth import basic_scheme, keycloak_openid
from api.routers.tracks_router import track_router
from api.routers.users_router import user_router
from api.routers.manage_router import manage_router
from api.routers.playlist_router import playlist_router
from api.routers.stream_router import stream_router

app = FastAPI()

#TODO настроить права доступа к апи

@app.post("/token")
async def get_token(credentials: HTTPBasicCredentials = Depends(basic_scheme)):
    try:
        token = keycloak_openid.token(
            username=credentials.username,
            password=credentials.password
        )
        return {"access_token": token["access_token"], "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

app.include_router(user_router)
app.include_router(track_router)
app.include_router(playlist_router)
app.include_router(manage_router)
app.include_router(stream_router)