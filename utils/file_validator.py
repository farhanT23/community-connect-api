from fastapi import HTTPException, status
from typing import IO


def validate_file_size_type(file: IO, file_types: list[str], max_size: int=2097152, min_size: int = 0):


    if file.content_type not in file_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type",
        )

    real_file_size = 0
    for chunk in file.file:
        real_file_size += len(chunk)
        if real_file_size > max_size:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Too large")

        if real_file_size < min_size:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too small")
