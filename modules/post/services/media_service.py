import os
import uuid
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from modules.post.models import Media

class MediaService:
    def __init__(self, db: AsyncSession, media_dir: str = "media"):
        self.db = db
        self.media_dir = media_dir
        os.makedirs(self.media_dir, exist_ok=True)

    def _generate_unique_filename(self, original_filename: str):
        ext = os.path.splitext(original_filename)[1]
        return f"{uuid.uuid4().hex}{ext}"
    
    async def save_media_files(self, media_files: Optional[List[UploadFile]]):
        saved_media = []
        for file in media_files or []:
            filename = self._generate_unique_filename(file.filename)
            file_path = os.path.join(self.media_dir, filename)

            
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            
            media = Media(
                file=filename,
                media_type=file.content_type
            )
            self.db.add(media)
            await self.db.flush()

            saved_media.append(media)

        return saved_media
    
    async def delete_media_file(self, media: Media):
        file_path = os.path.join(self.media_dir, media.file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")