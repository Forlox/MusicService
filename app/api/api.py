from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from Authentication.Auth import get_current_user, get_admin_user, basic_scheme, keycloak_openid

import MusicManager.interface as music
import Users.interface as users
import Playlist.interface as playlist

app = FastAPI()

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


tracks_router = APIRouter(prefix="/tracks", tags=["Public"])
users_router = APIRouter(prefix="/users", tags=["Users"])
manage_router = APIRouter(prefix="/tracks", tags=["Admin"], dependencies=[Depends(get_admin_user)])
playlist_router = APIRouter(prefix="/playlist", tags=["Playlist"])

# --- Треки ---
# TODO добавить get_track_list()

@tracks_router.get("/{track_id}")
async def get_track_by_id(track_id: int):
    return music.get_track_by_id(track_id)

@tracks_router.get("/album")
async def get_album(album: str, author: str | None = None):
    return music.get_tracks_by_album(album, author)

@tracks_router.get("/author")
async def get_author_tracks(author: str):
    return music.get_tracks_by_author(author)

@tracks_router.get("/search") # TODO эндпоинт сломался, надо чинить
async def search_tracks(query: str):
    return music.search_tracks(query)

# --- Плейлисты --- TODO добавить аутентификацию API (Щас оно публично).
@playlist_router.post("/")
async def playlist_create(playlist_name: str, track_ids: list[int] | None = None, current_user: dict = Depends(get_current_user),):
    owner_id = current_user["sub"]
    return playlist.create(playlist_name, owner_id, track_ids)

@playlist_router.post("/{playlist_id}/owners")
async def playlist_add_owner(playlist_id: int, user_id: str):
    return playlist.add_owner(playlist_id, user_id)

@playlist_router.get("/{playlist_id}")
async def playlist_track_list(playlist_id: int):
    return playlist.track_list(playlist_id)

@playlist_router.post("/{playlist_id}/tracks")
async def playlist_add_tracks(playlist_id: int, track_ids: list[int]):
    return playlist.add_tracks(playlist_id, track_ids)

@playlist_router.delete("/{playlist_id}/tracks")
async def playlist_remove_track(playlist_id: int, track_id: int):
    return playlist.remove_track(playlist_id, track_id)

@playlist_router.put("/{playlist_id}")
async def playlist_rename(playlist_id: int, new_name: str):
    return playlist.rename(playlist_id, new_name)

@playlist_router.put("/{playlist_id}/main-owner")
async def playlist_set_main_owner(playlist_id: int, user_id: str):
    return playlist.set_main_owner(playlist_id, user_id)

@playlist_router.get("/{playlist_id}/owners")
async def playlist_get_owners(playlist_id: int):
    return playlist.get_owners(playlist_id)

@playlist_router.get("/{playlist_id}/main-owner")
async def playlist_get_main_owner(playlist_id: int):
    return playlist.get_main_owner(playlist_id)

@playlist_router.get("/")
async def playlist_list():
    return playlist.list_playlists()


# --- Юзеры ---
@users_router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return users.get_current_user_info(current_user)

@users_router.get("/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    return users.get_user_by_id(user_id, current_user)

@users_router.put("/{user_id}")
async def update_user(
    user_id: str,
    username: str | None = None,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    enabled: bool | None = None,
    current_user: dict = Depends(get_current_user),
):
    return users.update_user(
        user_id,
        current_user,
        username,
        email,
        first_name,
        last_name,
        enabled,
    )


@users_router.delete("/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    return users.delete_user_by_id(user_id, admin)

@users_router.post("/")
async def create_user(
    username: str,
    password: str,
    email: str = "",
    first_name: str = "",
    last_name: str = "",
    admin: dict = Depends(get_admin_user),
):
    return users.create_new_user(
        username,
        password,
        email,
        first_name,
        last_name,
        admin,
    )

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

# --- Админ штуки ---
@manage_router.post("/add")
async def add_music_file(file: str):
    return music.add_music_file(file)

@manage_router.delete("/{track_id}")
async def delete_track(track_id: int):
    return {"deleted": music.delete_track_by_id(track_id)}

@manage_router.get("/full/{track_id}")
async def get_track_by_id_full(track_id: int):
    return music.get_track_by_id(track_id, False)

app.include_router(users_router)
app.include_router(tracks_router)
app.include_router(playlist_router)
app.include_router(manage_router)