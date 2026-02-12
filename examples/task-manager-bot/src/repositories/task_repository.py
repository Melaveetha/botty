from botty import BaseRepository

from datetime import datetime

from sqlmodel import Session, select

from src.models.task import Task


class TaskRepository(BaseRepository):
    """Repository for Task model operations."""

    model = Task

    def __init__(self, session: Session):
        super().__init__(session)

    def get_user_tasks(
        self, user_id: int, completed: bool | None = None, limit: int = 100
    ) -> list[Task]:
        """
        Get all tasks for a user.

        Args:
            user_id: User ID
            completed: Filter by completion status (None = all)
            limit: Maximum number of tasks to return

        Returns:
            List of tasks
        """
        statement = select(Task).where(Task.user_id == user_id)

        if completed is not None:
            statement = statement.where(Task.completed == completed)

        statement = statement.order_by(Task.created_at.desc()).limit(limit)

        return list(self.session.exec(statement).all())

    def get_pending_tasks(self, user_id: int) -> list[Task]:
        """
        Get all incomplete tasks for a user.

        Args:
            user_id: User ID

        Returns:
            List of incomplete tasks
        """
        return self.get_user_tasks(user_id, completed=False)

    def get_completed_tasks(self, user_id: int, limit: int = 50) -> list[Task]:
        """
        Get completed tasks for a user.

        Args:
            user_id: User ID
            limit: Maximum number of tasks

        Returns:
            List of completed tasks
        """
        return self.get_user_tasks(user_id, completed=True, limit=limit)

    def create_task(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        priority: str = "medium",
        tags: str | None = None,
        due_date: datetime | None = None,
    ) -> Task:
        """
        Create a new task.

        Args:
            user_id: User ID
            title: Task title
            description: Optional description
            priority: Task priority (low, medium, high)
            tags: Comma-separated tags
            due_date: Optional due date

        Returns:
            Created task
        """
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            tags=tags,
            due_date=due_date,
        )

        return self.create(task)

    def mark_complete(self, task_id: int, completed: bool = True) -> Task | None:
        """
        Mark task as complete or incomplete.

        Args:
            task_id: Task ID
            completed: Completion status

        Returns:
            Updated task or None if not found
        """
        task = self.get(task_id)

        if task:
            task.completed = completed
            task.completed_at = datetime.utcnow() if completed else None

            self.update(task)

        return task

    def search_tasks(self, user_id: int, keyword: str) -> list[Task]:
        """
        Search tasks by keyword in title or description.

        Args:
            user_id: User ID
            keyword: Search keyword

        Returns:
            List of matching tasks
        """
        keyword_lower = f"%{keyword.lower()}%"

        statement = (
            select(Task)
            .where(Task.user_id == user_id)
            .where(
                (Task.title.ilike(keyword_lower))
                | (Task.description.ilike(keyword_lower))
            )
            .order_by(Task.created_at.desc())
        )

        return list(self.session.exec(statement).all())

    def get_tasks_by_tag(self, user_id: int, tag: str) -> list[Task]:
        """
        Get tasks with specific tag.

        Args:
            user_id: User ID
            tag: Tag to search for

        Returns:
            List of tasks with the tag
        """
        statement = (
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.tags.contains(tag))
            .order_by(Task.created_at.desc())
        )

        return list(self.session.exec(statement).all())

    def get_overdue_tasks(self, user_id: int) -> list[Task]:
        """
        Get overdue tasks for a user.

        Args:
            user_id: User ID

        Returns:
            List of overdue tasks
        """
        now = datetime.utcnow()

        statement = (
            select(Task)
            .where(Task.user_id == user_id)
            .where(not Task.completed)
            .where(Task.due_date < now)
            .order_by(Task.due_date.asc())
        )

        return list(self.session.exec(statement).all())

    def get_task_stats(self, user_id: int) -> dict:
        """
        Get statistics about user's tasks.

        Args:
            user_id: User ID

        Returns:
            Dictionary with task statistics
        """
        all_tasks = self.get_user_tasks(user_id, limit=10000)
        completed = [t for t in all_tasks if t.completed]
        pending = [t for t in all_tasks if not t.completed]
        overdue = [t for t in pending if t.is_overdue]

        return {
            "total": len(all_tasks),
            "completed": len(completed),
            "pending": len(pending),
            "overdue": len(overdue),
            "completion_rate": (len(completed) / len(all_tasks) * 100)
            if all_tasks
            else 0,
        }
