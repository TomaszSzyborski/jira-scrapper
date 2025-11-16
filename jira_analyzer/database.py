"""
Database service for storing Jira issues in SQLite.

This module provides a lightweight database layer for storing and retrieving
Jira issues with incremental sync support.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import contextmanager


class JiraDatabase:
    """SQLite database for Jira issues with incremental sync support."""

    def __init__(self, db_path: str = "data/jira.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Projects table - tracks sync metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_key TEXT PRIMARY KEY,
                    last_sync_at TEXT NOT NULL,
                    last_created_date TEXT,
                    last_updated_date TEXT,
                    total_issues INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Issues table - stores complete issue data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_key TEXT NOT NULL,
                    issue_key TEXT NOT NULL UNIQUE,
                    issue_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT,
                    created TEXT NOT NULL,
                    updated TEXT NOT NULL,
                    resolved TEXT,
                    reporter TEXT,
                    assignee TEXT,
                    priority TEXT,
                    labels TEXT,
                    issue_data TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    FOREIGN KEY (project_key) REFERENCES projects(project_key)
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_issues_project
                ON issues(project_key)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_issues_created
                ON issues(created)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_issues_updated
                ON issues(updated)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_issues_type
                ON issues(issue_type)
            """)

            conn.commit()

    def get_project_metadata(self, project_key: str) -> Optional[Dict]:
        """Get project sync metadata."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM projects WHERE project_key = ?",
                (project_key,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def update_project_metadata(
        self,
        project_key: str,
        last_created_date: Optional[str] = None,
        last_updated_date: Optional[str] = None,
        total_issues: Optional[int] = None
    ):
        """Update project sync metadata."""
        now = datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if project exists
            cursor.execute(
                "SELECT project_key FROM projects WHERE project_key = ?",
                (project_key,)
            )
            exists = cursor.fetchone()

            if exists:
                # Update existing project
                updates = ["last_sync_at = ?", "updated_at = ?"]
                params = [now, now]

                if last_created_date:
                    updates.append("last_created_date = ?")
                    params.append(last_created_date)
                if last_updated_date:
                    updates.append("last_updated_date = ?")
                    params.append(last_updated_date)
                if total_issues is not None:
                    updates.append("total_issues = ?")
                    params.append(total_issues)

                params.append(project_key)

                cursor.execute(
                    f"UPDATE projects SET {', '.join(updates)} WHERE project_key = ?",
                    params
                )
            else:
                # Insert new project
                cursor.execute(
                    """
                    INSERT INTO projects
                    (project_key, last_sync_at, last_created_date, last_updated_date,
                     total_issues, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (project_key, now, last_created_date, last_updated_date,
                     total_issues or 0, now, now)
                )

    def upsert_issues(self, project_key: str, issues: List[Dict]):
        """Insert or update issues in bulk."""
        now = datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            for issue in issues:
                # Extract fields
                issue_key = issue['key']
                issue_type = issue['type']
                status = issue['status']
                summary = issue.get('summary', '')
                created = issue['created']
                updated = issue['updated']
                resolved = issue.get('resolved')
                reporter = issue.get('reporter', '')
                assignee = issue.get('assignee', '')
                priority = issue.get('priority', '')
                labels = json.dumps(issue.get('labels', []))
                issue_data = json.dumps(issue)

                # Upsert issue
                cursor.execute(
                    """
                    INSERT INTO issues
                    (project_key, issue_key, issue_type, status, summary, created,
                     updated, resolved, reporter, assignee, priority, labels,
                     issue_data, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(issue_key) DO UPDATE SET
                        issue_type = excluded.issue_type,
                        status = excluded.status,
                        summary = excluded.summary,
                        updated = excluded.updated,
                        resolved = excluded.resolved,
                        assignee = excluded.assignee,
                        priority = excluded.priority,
                        labels = excluded.labels,
                        issue_data = excluded.issue_data,
                        fetched_at = excluded.fetched_at
                    """,
                    (project_key, issue_key, issue_type, status, summary, created,
                     updated, resolved, reporter, assignee, priority, labels,
                     issue_data, now)
                )

            # Update project metadata
            cursor.execute(
                "SELECT COUNT(*) FROM issues WHERE project_key = ?",
                (project_key,)
            )
            total_issues = cursor.fetchone()[0]

            # Get latest created and updated dates
            cursor.execute(
                """
                SELECT MAX(created) as max_created, MAX(updated) as max_updated
                FROM issues WHERE project_key = ?
                """,
                (project_key,)
            )
            row = cursor.fetchone()
            max_created = row[0] if row else None
            max_updated = row[1] if row else None

            self.update_project_metadata(
                project_key,
                last_created_date=max_created,
                last_updated_date=max_updated,
                total_issues=total_issues
            )

    def get_issues(
        self,
        project_key: str,
        issue_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Get issues from database with optional filtering."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT issue_data FROM issues WHERE project_key = ?"
            params = [project_key]

            if issue_types:
                placeholders = ','.join('?' * len(issue_types))
                query += f" AND issue_type IN ({placeholders})"
                params.extend(issue_types)

            if start_date:
                query += " AND created >= ?"
                params.append(start_date)

            if end_date:
                query += " AND created <= ?"
                params.append(end_date)

            query += " ORDER BY created ASC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [json.loads(row[0]) for row in rows]

    def get_all_issues(self, project_key: str) -> List[Dict]:
        """Get all issues for a project."""
        return self.get_issues(project_key)

    def get_issue_count(
        self,
        project_key: str,
        issue_types: Optional[List[str]] = None
    ) -> int:
        """Get count of issues."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT COUNT(*) FROM issues WHERE project_key = ?"
            params = [project_key]

            if issue_types:
                placeholders = ','.join('?' * len(issue_types))
                query += f" AND issue_type IN ({placeholders})"
                params.extend(issue_types)

            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def get_projects(self) -> List[Dict]:
        """Get all projects."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY last_sync_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_project(self, project_key: str):
        """Delete a project and all its issues."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM issues WHERE project_key = ?", (project_key,))
            cursor.execute("DELETE FROM projects WHERE project_key = ?", (project_key,))
