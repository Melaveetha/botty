"""Task service with business logic."""

import re
from typing import Annotated, Optional, TypeAlias

from telegram import Update

from botty import BaseService, Context, Depends


class TaskService(BaseService):
    """
    Service layer for task-related business logic.

    Handles task parsing, validation, and formatting.
    """

    def __init__(self):
        super().__init__()

    def parse_task_input(self, text: str) -> dict:
        """
        Parse task input text to extract title, priority, and tags.

        Args:
            text: Raw task input from user

        Returns:
            Dictionary with parsed components

        Examples:
            "Buy groceries #shopping"
            → title="Buy groceries", tags="shopping"

            "Fix bug !!! #work #urgent"
            → title="Fix bug", priority="high", tags="work,urgent"
        """
        # Extract priority from exclamation marks
        priority = self.extract_priority(text)

        # Extract hashtags
        tags = self.extract_tags(text)

        # Clean title (remove priority markers and tags)
        title = self.clean_title(text)

        return {
            "title": title,
            "priority": priority,
            "tags": ",".join(tags) if tags else None,
        }

    def extract_priority(self, text: str) -> str:
        """
        Extract priority from text based on keywords and markers.

        Priority indicators:
        - !!! or "urgent" → high
        - !! or "important" → medium
        - ! or default → low

        Args:
            text: Input text

        Returns:
            Priority level (low, medium, high)
        """
        text_lower = text.lower()

        # Check for urgent keywords
        if "urgent" in text_lower or "!!!" in text:
            return "high"

        # Check for important keywords
        if "important" in text_lower or "!!" in text:
            return "medium"

        # Check for single exclamation
        if "!" in text or "high" in text_lower:
            return "high"

        return "medium"  # Default

    def extract_tags(self, text: str) -> list[str]:
        """
        Extract hashtags from text.

        Args:
            text: Input text

        Returns:
            List of tags (without # symbol)

        Example:
            "Buy milk #shopping #groceries" → ["shopping", "groceries"]
        """
        # Find all hashtags
        tags = re.findall(r"#(\w+)", text)

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_tags.append(tag)

        return unique_tags

    def clean_title(self, text: str) -> str:
        """
        Clean task title by removing hashtags and priority markers.

        Args:
            text: Raw input text

        Returns:
            Cleaned title
        """
        # Remove hashtags
        cleaned = re.sub(r"#\w+", "", text)

        # Remove priority keywords
        cleaned = re.sub(
            r"\b(urgent|important|high|medium|low)\b", "", cleaned, flags=re.IGNORECASE
        )

        # Remove excessive exclamation marks
        cleaned = re.sub(r"!+", "", cleaned)

        # Clean up whitespace
        cleaned = " ".join(cleaned.split())

        return cleaned.strip()

    def format_task_list(self, tasks: list, show_completed: bool = False) -> str:
        """
        Format a list of tasks for display.

        Args:
            tasks: List of Task objects
            show_completed: Whether to show completed tasks

        Returns:
            Formatted string for Telegram
        """
        if not tasks:
            return "📭 No tasks found."

        # Filter by completion if needed
        if not show_completed:
            tasks = [t for t in tasks if not t.completed]

        if not tasks:
            return "✅ All tasks completed! Great job!"

        # Group by priority
        high_priority = [t for t in tasks if t.priority == "high"]
        medium_priority = [t for t in tasks if t.priority == "medium"]
        low_priority = [t for t in tasks if t.priority == "low"]

        lines = ["📋 <b>Your Tasks:</b>\n"]

        # Add high priority tasks
        if high_priority:
            lines.append("<b>🔴 High Priority:</b>")
            for task in high_priority:
                lines.append(f"  {task.format_for_display()}")
            lines.append("")

        # Add medium priority tasks
        if medium_priority:
            lines.append("<b>🟡 Medium Priority:</b>")
            for task in medium_priority:
                lines.append(f"  {task.format_for_display()}")
            lines.append("")

        # Add low priority tasks
        if low_priority:
            lines.append("<b>🟢 Low Priority:</b>")
            for task in low_priority:
                lines.append(f"  {task.format_for_display()}")

        return "\n".join(lines)

    def format_task_stats(self, stats: dict) -> str:
        """
        Format task statistics for display.

        Args:
            stats: Statistics dictionary from repository

        Returns:
            Formatted statistics string
        """
        completion_rate = stats["completion_rate"]

        # Determine emoji based on completion rate
        if completion_rate >= 80:
            emoji = "🎉"
        elif completion_rate >= 50:
            emoji = "👍"
        else:
            emoji = "💪"

        lines = [
            f"{emoji} <b>Your Task Statistics:</b>\n",
            f"📊 Total tasks: {stats['total']}",
            f"✅ Completed: {stats['completed']}",
            f"⭕ Pending: {stats['pending']}",
        ]

        if stats["overdue"] > 0:
            lines.append(f"⚠️ Overdue: {stats['overdue']}")

        lines.append(f"📈 Completion rate: {completion_rate:.1f}%")

        return "\n".join(lines)

    def validate_task_id(self, task_id_str: str) -> Optional[int]:
        """
        Validate and convert task ID string to integer.

        Args:
            task_id_str: Task ID as string

        Returns:
            Task ID as integer or None if invalid
        """
        try:
            task_id = int(task_id_str)
            if task_id > 0:
                return task_id
        except (ValueError, TypeError):
            pass

        return None


async def task_service(update: Update, context: Context):
    return TaskService()


TaskServiceDependency: TypeAlias = Annotated[TaskService, Depends(task_service)]
