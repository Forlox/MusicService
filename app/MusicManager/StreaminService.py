from pathlib import Path
import mimetypes
import logging
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024

def _file_iterator(path: str, start: int, end: int):
    with open(path, "rb") as file:
        file.seek(start)

        remaining = end - start + 1

        while remaining > 0:
            chunk = file.read(min(CHUNK_SIZE, remaining))

            if not chunk:
                break

            remaining -= len(chunk)
            yield chunk


def stream_file(path: str, request: Request):
    file_path = Path(path)

    if not file_path.exists():
        logger.warning(f"Файл не найден для стрима: {path}")
        raise HTTPException(
            status_code=404,
            detail="Track not found"
        )

    media_type, _ = mimetypes.guess_type(file_path.name)

    if not media_type:
        media_type = "application/octet-stream"

    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    if not range_header:
        logger.debug(f"Полный стрим файла: {path} (размер: {file_size})")
        return StreamingResponse(
            _file_iterator(path, 0, file_size - 1),
            media_type=media_type,
            headers={
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes"
            }
        )

    start, end = range_header.replace("bytes=", "").split("-")

    start = int(start)
    end = int(end) if end else file_size - 1

    if start >= file_size:
        logger.warning(f"Некорректный диапазон для {path}: start={start}, file_size={file_size}")
        raise HTTPException(
            status_code=416,
            detail="Range not satisfiable"
        )

    end = min(end, file_size - 1)
    logger.debug(f"Стрим диапазона {start}-{end}/{file_size} файла: {path}")

    return StreamingResponse(
        _file_iterator(path, start, end),
        status_code=206,
        media_type=media_type,
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1)
        }
    )