from fastapi import APIRouter, Request
from fastapi import Depends

from MusicManager.StreaminService import stream_file
import MusicManager.interface as music
from Authentication.Auth import get_current_user, get_admin_user


stream_router = APIRouter(
    prefix="/stream",
    tags=["Streaming"],
    dependencies=[Depends(get_current_user)]
)


@stream_router.get("/{track_id}")
async def get_stream_by_track_id(
        track_id: int,
        request: Request
):
    track_path = music.get_track_file_path_by_id(track_id)

    return stream_file(track_path, request)