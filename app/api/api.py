from typing import Optional
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials

import MusicManager.interface as music
from Authentication.Auth import get_current_user, get_admin_user, basic_scheme, keycloak_openid
import Users.interface as users

app = FastAPI()

@app.post("/token")
async def get_token(credentials: HTTPBasicCredentials = Depends(basic_scheme)):
    try:
        token = keycloak_openid.token(
            username=credentials.username,
            password=credentials.password
        )
        return {"access_token": token["access_token"], "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

tracks_router = APIRouter(prefix="/tracks", tags=["Public"])

@tracks_router.get("/{track_id}")
def get_track_by_id(track_id: int):
    return music.get_track_by_id(track_id)

@tracks_router.get("/album")
def get_album(album: str, author: str | None = None):
    return music.get_tracks_by_album(album, author)

@tracks_router.get("/author")
def get_author_tracks(author: str):
    return music.get_tracks_by_author(author)

@tracks_router.get("/search")
def search(query: str):
    return music.search_tracks(query)

users_router = APIRouter(prefix="/users", tags=["Users"])

@users_router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return users.get_current_user_info(current_user)

@users_router.get("/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    return users.get_user_by_id(user_id, current_user)

@users_router.put("/{user_id}")
async def update_user(user_id: str,
                      username: Optional[str] = None,
                      email: Optional[str] = None,
                      first_name: Optional[str] = None,
                      last_name: Optional[str] = None,
                      enabled: Optional[bool] = None,
                      current_user: dict = Depends(get_current_user)):
    return users.update_self_or_admin(user_id, current_user, username, email, first_name, last_name, enabled)

@users_router.delete("/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    return users.delete_user_by_id(user_id, admin)

@users_router.post("/")
async def create_user(username: str, email: str, password: str,
                      first_name: str = "", last_name: str = "",
                      admin: dict = Depends(get_admin_user)):
    return users.create_new_user(username, email, password, first_name, last_name, admin)

@users_router.post("/{user_id}/admin")
async def assign_admin(user_id: str, admin: dict = Depends(get_admin_user)):
    return users.assign_admin_role(user_id, admin)

@users_router.delete("/{user_id}/admin")
async def remove_admin(user_id: str, admin: dict = Depends(get_admin_user)):
    return users.remove_admin_role(user_id, admin)

@users_router.get("/")
async def list_users(admin: dict = Depends(get_admin_user)):
    return users.list_all_users(admin)

@users_router.post("/sync")
async def sync_users(admin: dict = Depends(get_admin_user)):
    return users.sync_all_users(admin)

manage_router = APIRouter(prefix="/tracks", tags=["Admin"])
@manage_router.post("/add")
def add(file: str, admin_data: dict = Depends(get_admin_user)):
    return music.add_music_file(file)

@manage_router.delete("/{track_id}")
def delete_track(track_id: int, admin_data: dict = Depends(get_admin_user)):
    return {"deleted": music.delete_track_by_id(track_id)}

@manage_router.get("/full/{track_id}")
def get_track_by_id_full(track_id: int, dict = Depends(get_admin_user)):
    return music.get_track_by_id(track_id, False)

app.include_router(users_router)
app.include_router(tracks_router)
app.include_router(manage_router)