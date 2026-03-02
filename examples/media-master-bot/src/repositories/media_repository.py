from botty import BaseRepository
from sqlmodel import select
from src.models.media import MediaFile


class MediaRepository(BaseRepository[MediaFile]):
    model = MediaFile

    def add_file(
        self, user_id: int, file_id: str, file_type: str, caption: str | None = None
    ) -> MediaFile:
        media = MediaFile(
            user_id=user_id, file_id=file_id, file_type=file_type, caption=caption
        )
        return self.create(media)

    def get_user_files(
        self, user_id: int, file_type: str | None = None
    ) -> list[MediaFile]:
        stmt = select(MediaFile).where(MediaFile.user_id == user_id)
        if file_type:
            stmt = stmt.where(MediaFile.file_type == file_type)
        return list(self.session.exec(stmt).all())

    def get_by_file_id(self, file_id: str) -> MediaFile | None:
        statement = select(MediaFile).where(MediaFile.file_id == file_id)
        return self.session.exec(statement).first()
