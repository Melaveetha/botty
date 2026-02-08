from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional


class Task(SQLModel, table=True):
    """
    Task model representing a user's task.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        title: Task title/description
        description: Optional detailed description
        completed: Whether task is completed
        priority: Task priority (low, medium, high)
        tags: Comma-separated tags
        created_at: When task was created
        completed_at: When task was completed (if applicable)
        due_date: Optional due date
    """

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    completed: bool = Field(default=False)
    priority: str = Field(default="medium")  # low, medium, high
    tags: Optional[str] = None  # Comma-separated
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None

    def __repr__(self) -> str:
        status = "✅" if self.completed else "⭕"
        return f"Task(id={self.id}, {status} '{self.title[:30]}...')"

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date or self.completed:
            return False
        return datetime.utcnow() > self.due_date

    @property
    def tag_list(self) -> list[str]:
        """Get tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    @property
    def priority_emoji(self) -> str:
        """Get emoji for priority level."""
        return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(self.priority, "⚪")

    def format_for_display(self, include_id: bool = True) -> str:
        """Format task for display in Telegram."""
        status = "✅" if self.completed else "⭕"
        priority = self.priority_emoji

        parts = []

        if include_id:
            parts.append(f"#{self.id}")

        parts.append(f"{status} {priority} {self.title}")

        if self.tag_list:
            tags = " ".join(f"#{tag}" for tag in self.tag_list)
            parts.append(f"\n   {tags}")

        if self.due_date and not self.completed:
            due_str = self.due_date.strftime("%Y-%m-%d %H:%M")
            if self.is_overdue:
                parts.append(f"\n   ⚠️ Overdue: {due_str}")
            else:
                parts.append(f"\n   📅 Due: {due_str}")

        return " ".join(parts) if len(parts) == 1 else "".join(parts)
