from sqlmodel import SQLModel, Field
from datetime import datetime


class MediaFile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    file_id: str
    file_type: str  # "photo", "document", etc.
    caption: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
