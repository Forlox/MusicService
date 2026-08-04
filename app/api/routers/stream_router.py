from fastapi import APIRouter, Request

from MusicManager.StreaminService import stream_file
import MusicManager.interface as music


stream_router = APIRouter(
    prefix="/stream",
    tags=["Streaming"]
)


@stream_router.get("/{track_id}")
async def get_stream_by_track_id(
        track_id: int,
        request: Request
):
    track_path = music.get_track_file_path_by_id(track_id)

    return stream_file(track_path, request)