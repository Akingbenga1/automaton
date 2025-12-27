"""Database module for tracking job applications"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import json


class ApplicationDatabase:
    """Manages job application tracking in SQLite"""

    def __init__(self, db_path: str = "data/applications.db"):
        self.db_path = db_path
        self._ensure_db_exists()
        self._init_schema()

    def _ensure_db_exists(self):
        """Ensure database directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_schema(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    platform TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    url TEXT,
                    description TEXT,
                    salary_min INTEGER,
                    salary_max INTEGER,
                    job_type TEXT,
                    work_mode TEXT,
                    match_score REAL,
                    applied_at TEXT NOT NULL,
                    status TEXT DEFAULT 'applied',
                    confirmation_number TEXT,
                    notes TEXT,
                    job_data TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_id ON applications(job_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_platform ON applications(platform)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_applied_at ON applications(applied_at)
            """)
            conn.commit()

    def has_applied(self, job_id: str) -> bool:
        """Check if already applied to this job"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE job_id = ?",
                (job_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def add_application(self, job_data: Dict) -> bool:
        """
        Add a new job application

        Args:
            job_data: Dictionary containing job information

        Returns:
            True if added successfully, False if duplicate
        """
        if self.has_applied(job_data.get("job_id")):
            return False

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO applications (
                    job_id, platform, title, company, location, url,
                    description, salary_min, salary_max, job_type,
                    work_mode, match_score, applied_at, status,
                    confirmation_number, notes, job_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_data.get("job_id"),
                job_data.get("platform"),
                job_data.get("title"),
                job_data.get("company"),
                job_data.get("location"),
                job_data.get("url"),
                job_data.get("description", ""),
                job_data.get("salary_min"),
                job_data.get("salary_max"),
                job_data.get("job_type"),
                job_data.get("work_mode"),
                job_data.get("match_score"),
                datetime.now().isoformat(),
                job_data.get("status", "applied"),
                job_data.get("confirmation_number"),
                job_data.get("notes"),
                json.dumps(job_data)
            ))
            conn.commit()
        return True

    def get_recent_applications(self, limit: int = 50) -> List[Dict]:
        """Get recent applications"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM applications
                ORDER BY applied_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_applications_by_platform(self, platform: str, limit: int = 50) -> List[Dict]:
        """Get applications for a specific platform"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM applications
                WHERE platform = ?
                ORDER BY applied_at DESC
                LIMIT ?
            """, (platform, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_applications_count(self, since: Optional[str] = None) -> int:
        """Get count of applications, optionally since a specific datetime"""
        with sqlite3.connect(self.db_path) as conn:
            if since:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM applications WHERE applied_at >= ?",
                    (since,)
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM applications")
            return cursor.fetchone()[0]

    def get_platform_count(self, platform: str, since: Optional[str] = None) -> int:
        """Get count of applications for a platform since a datetime"""
        with sqlite3.connect(self.db_path) as conn:
            if since:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM applications WHERE platform = ? AND applied_at >= ?",
                    (platform, since)
                )
            else:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM applications WHERE platform = ?",
                    (platform,)
                )
            return cursor.fetchone()[0]

    def update_status(self, job_id: str, status: str, notes: Optional[str] = None):
        """Update application status"""
        with sqlite3.connect(self.db_path) as conn:
            if notes:
                conn.execute(
                    "UPDATE applications SET status = ?, notes = ? WHERE job_id = ?",
                    (status, notes, job_id)
                )
            else:
                conn.execute(
                    "UPDATE applications SET status = ? WHERE job_id = ?",
                    (status, job_id)
                )
            conn.commit()

    def get_statistics(self) -> Dict:
        """Get application statistics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Total applications
            total = conn.execute("SELECT COUNT(*) as count FROM applications").fetchone()["count"]

            # By platform
            by_platform = {}
            cursor = conn.execute("""
                SELECT platform, COUNT(*) as count
                FROM applications
                GROUP BY platform
            """)
            for row in cursor:
                by_platform[row["platform"]] = row["count"]

            # By status
            by_status = {}
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM applications
                GROUP BY status
            """)
            for row in cursor:
                by_status[row["status"]] = row["count"]

            # Average match score
            avg_score = conn.execute(
                "SELECT AVG(match_score) as avg FROM applications WHERE match_score IS NOT NULL"
            ).fetchone()["avg"]

            return {
                "total": total,
                "by_platform": by_platform,
                "by_status": by_status,
                "average_match_score": round(avg_score, 2) if avg_score else 0
            }
