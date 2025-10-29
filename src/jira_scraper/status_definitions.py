"""Status definitions for Jira ticket categorization.

This module provides centralized status mappings for consistent categorization
across all chart and analysis components.
"""

from typing import List, Set


class StatusDefinitions:
    """Centralized status definitions for Jira tickets."""

    # Status Category: To Do (statusCategory = "To Do")
    TODO_STATUSES: List[str] = [
        "To Do",
        "TODO",
        "Open",
        "New",
        "Backlog",
        "Reopened",
        "Ready",
        "Ready for Development",
        "Ready for Dev",
        "Planned",
        "Pending",
        "Waiting",
        "On Hold",
        "Blocked",
    ]

    # Status Category: In Progress (statusCategory = "In Progress" or "Indeterminate")
    IN_PROGRESS_STATUSES: List[str] = [
        "In Progress",
        "In Development",
        "In Dev",
        "Developing",
        "Development",
        "In Review",
        "In Code Review",
        "Code Review",
        "Reviewing",
        "Review",
        "Testing",
        "In Testing",
        "In QA",
        "QA",
        "Quality Assurance",
        "To Test",
        "Ready for Testing",
        "Ready for QA",
        "Verification",
        "In Verification",
        "Deployment",
        "In Deployment",
        "Ready for Deployment",
        "UAT",
        "User Acceptance Testing",
    ]

    # Status Category: Done (statusCategory = "Done")
    DONE_STATUSES: List[str] = [
        "Done",
        "Closed",
        "Resolved",
        "Complete",
        "Completed",
        "Finished",
        "Released",
        "Deployed",
        "Live",
        "Production",
        "Cancelled",
        "Canceled",
        "Rejected",
        "Duplicate",
        "Won't Do",
        "Won't Fix",
        "Invalid",
        "Cannot Reproduce",
    ]

    # Keywords for heuristic detection
    TODO_KEYWORDS: List[str] = [
        "todo", "open", "new", "backlog", "reopen", "ready", "planned", "pending", "waiting", "hold", "blocked"
    ]

    IN_PROGRESS_KEYWORDS: List[str] = [
        "progress", "development", "developing", "review", "testing", "verification", "deployment", "uat", "qa"
    ]

    DONE_KEYWORDS: List[str] = [
        "done", "closed", "resolved", "complete", "finish", "released", "deployed", "live",
        "production", "cancel", "reject", "duplicate", "wont", "won't", "invalid"
    ]

    @classmethod
    def get_all_todo_statuses(cls) -> Set[str]:
        """Get all To Do statuses as a set for fast lookup."""
        return set(cls.TODO_STATUSES)

    @classmethod
    def get_all_in_progress_statuses(cls) -> Set[str]:
        """Get all In Progress statuses as a set for fast lookup."""
        return set(cls.IN_PROGRESS_STATUSES)

    @classmethod
    def get_all_done_statuses(cls) -> Set[str]:
        """Get all Done statuses as a set for fast lookup."""
        return set(cls.DONE_STATUSES)

    @classmethod
    def is_todo_status(cls, status: str) -> bool:
        """
        Check if a status is in the To Do category.

        Args:
            status: Status string

        Returns:
            True if status is To Do category
        """
        # Exact match
        if status in cls.TODO_STATUSES:
            return True

        # Heuristic detection
        status_lower = status.lower()
        return any(keyword in status_lower for keyword in cls.TODO_KEYWORDS)

    @classmethod
    def is_in_progress_status(cls, status: str) -> bool:
        """
        Check if a status is in the In Progress category.

        Args:
            status: Status string

        Returns:
            True if status is In Progress category
        """
        # Exact match
        if status in cls.IN_PROGRESS_STATUSES:
            return True

        # Heuristic detection
        status_lower = status.lower()
        return any(keyword in status_lower for keyword in cls.IN_PROGRESS_KEYWORDS)

    @classmethod
    def is_done_status(cls, status: str) -> bool:
        """
        Check if a status is in the Done category.

        Args:
            status: Status string

        Returns:
            True if status is Done category
        """
        # Exact match
        if status in cls.DONE_STATUSES:
            return True

        # Heuristic detection
        status_lower = status.lower()
        return any(keyword in status_lower for keyword in cls.DONE_KEYWORDS)

    @classmethod
    def categorize_status(cls, status: str, status_category: str = "") -> str:
        """
        Categorize a status into To Do, In Progress, or Done.

        Args:
            status: Status string
            status_category: Optional Jira statusCategory field value

        Returns:
            One of: "To Do", "In Progress", "Done"
        """
        # Use Jira's statusCategory if available
        if status_category:
            cat_lower = status_category.lower()
            if cat_lower in ["todo", "to do", "new"]:
                return "To Do"
            elif cat_lower in ["indeterminate", "in progress", "inprogress"]:
                return "In Progress"
            elif cat_lower in ["done", "complete", "completed"]:
                return "Done"

        # Fallback to status name detection
        if cls.is_done_status(status):
            return "Done"
        elif cls.is_in_progress_status(status):
            return "In Progress"
        else:
            return "To Do"

    @classmethod
    def is_not_done(cls, status: str, status_category: str = "") -> bool:
        """
        Check if a status is NOT in Done category (i.e., To Do or In Progress).

        This is the main method to use for "open" or "active" ticket filtering.

        Args:
            status: Status string
            status_category: Optional Jira statusCategory field value

        Returns:
            True if status is NOT Done (i.e., ticket is still open/active)
        """
        # Use Jira's statusCategory if available
        if status_category:
            cat_lower = status_category.lower()
            if cat_lower in ["done", "complete", "completed"]:
                return False
            else:
                return True

        # Fallback to status name detection
        return not cls.is_done_status(status)


# Convenience functions for backward compatibility
def is_done_status(status: str) -> bool:
    """Check if status is Done category."""
    return StatusDefinitions.is_done_status(status)


def is_not_done_status(status: str, status_category: str = "") -> bool:
    """Check if status is NOT Done category."""
    return StatusDefinitions.is_not_done(status, status_category)


def categorize_status(status: str, status_category: str = "") -> str:
    """Categorize status into To Do, In Progress, or Done."""
    return StatusDefinitions.categorize_status(status, status_category)
