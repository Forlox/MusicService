from fastapi import APIRouter, Depends, HTTPException, status

from Authentication.Auth import get_current_user, require_active_user
import Playlist.interface as playlist
from Playlist.interface import check_owner_permission

playlist_router = APIRouter(prefix="/playlist", tags=["Playlist"], dependencies=[Depends(require_active_user())])

# TODO мб реализовать публичность плейлистов

@playlist_router.post("/")
async def playlist_create(
    playlist_name: str,
    track_ids: list[int] | None = None,
    current_user: dict = Depends(get_current_user)):
    owner_id = current_user["sub"]
    return playlist.create(playlist_name, owner_id, track_ids)

@playlist_router.post("/{playlist_id}/owners")
async def playlist_add_owner(
    playlist_id: int,
    user_id: str,
    current_user: dict = Depends(get_current_user)):
    check_owner_permission(playlist_id, current_user)
    return playlist.add_owner(playlist_id, user_id)

@playlist_router.get("/{playlist_id}")
async def playlist_track_list(
    playlist_id: int,
    current_user: dict = Depends(get_current_user)):
    check_owner_permission(playlist_id, current_user)
    return playlist.track_list(playlist_id)

@playlist_router.post("/{playlist_id}/tracks")
async def playlist_add_tracks(
    playlist_id: int,
    track_ids: list[int],
    current_user: dict = Depends(get_current_user)):
    check_owner_permission(playlist_id, current_user)
    return playlist.add_tracks(playlist_id, track_ids)

@playlist_router.delete("/{playlist_id}/tracks")
async def playlist_remove_track(
    playlist_id: int,
    track_id: int,
    current_user: dict = Depends(get_current_user)):
    check_owner_permission(playlist_id, current_user)
    return playlist.remove_track(playlist_id, track_id)

@playlist_router.put("/{playlist_id}")
async def playlist_rename(
    playlist_id: int,
    new_name: str,
    current_user: dict = Depends(get_current_user)):
    check_owner_permission(playlist_id, current_user)
    return playlist.rename(playlist_id, new_name)

@playlist_router.put("/{playlist_id}/main-owner")
async def playlist_set_main_owner(
    playlist_id: int,
    user_id: str,
    current_user: dict = Depends(get_current_user)):
    check_owner_permission(playlist_id, current_user)
    return playlist.set_main_owner(playlist_id, user_id)

@playlist_router.get("/{playlist_id}/owners")
async def playlist_get_owners(playlist_id: int, current_user: dict = Depends(get_current_user)):
    check_owner_permission(playlist_id, current_user)
    return playlist.get_owners(playlist_id)

@playlist_router.get("/{playlist_id}/main-owner")
async def playlist_get_main_owner(
    playlist_id: int,
    current_user: dict = Depends(get_current_user)):
    check_owner_permission(playlist_id, current_user)
    return playlist.get_main_owner(playlist_id)

@playlist_router.get("/")
async def playlist_list(
    current_user: dict = Depends(get_current_user)):
    return playlist.list_playlists(current_user)

@playlist_router.delete("/{playlist_id}")
async def playlist_delete(
    playlist_id: int,
    current_user: dict = Depends(get_current_user)):
    check_owner_permission(playlist_id, current_user)
    return playlist.delete(playlist_id)