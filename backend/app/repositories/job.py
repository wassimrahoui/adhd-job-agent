from __future__ import annotations

import json
from typing import Optional, List
from datetime import datetime

from app.db import Database
from app.models import Job, JobCreate, JobUpdate, JobListItem


class JobRepository:
    def __init__(self, db: Database):
        self.db = db

    async def create_job(self, job_data: JobCreate) -> Job:
        """Create a new job."""
        now = datetime.utcnow()
        data = job_data.model_dump()
        
        # Handle JSON fields - always serialize list fields
        if isinstance(data.get("skills"), list):
            data["skills"] = json.dumps(data["skills"])
        # Always serialize raw_evidence if it's a dict
        if isinstance(data.get("raw_evidence"), dict):
            data["raw_evidence"] = json.dumps(data["raw_evidence"])
        
        columns = list(data.keys())
        placeholders = ", ".join(["?" for _ in columns])
        values = list(data.values())
        
        query = f"INSERT INTO jobs ({', '.join(columns)}, discovered_at) VALUES ({placeholders}, ?)"
        params = values + [now]
        cursor = await self.db.execute(query, tuple(params))
        await self.db._pool.commit()  # type: ignore[union-attr]
        
        job_id = cursor.lastrowid
        if job_id is None:
            raise RuntimeError("Failed to get lastrowid after insert")
        result = await self.get_job(job_id)
        if result is None:
            raise RuntimeError("Failed to retrieve job after creation")
        return result

    async def get_job(self, job_id: int) -> Optional[Job]:
        """Get a job by internal ID."""
        row = await self.db.fetchone("SELECT * FROM jobs WHERE id = ?", (job_id,))
        if not row:
            return None
        return self._row_to_job(row)

    async def get_job_by_adzuna_id(self, adzuna_id: str) -> Optional[Job]:
        """Get a job by Adzuna ID."""
        row = await self.db.fetchone("SELECT * FROM jobs WHERE adzuna_id = ?", (adzuna_id,))
        if not row:
            return None
        return self._row_to_job(row)

    async def list_jobs(
        self,
        limit: int = 50,
        offset: int = 0,
        passed_prefilter: Optional[bool] = None,
    ) -> List[JobListItem]:
        """List jobs with optional filter."""
        query = "SELECT * FROM jobs"
        params = []
        
        if passed_prefilter is not None:
            query += " WHERE passed_prefilter = ?"
            params.append(1 if passed_prefilter else 0)
        
        query += " ORDER BY discovered_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = await self.db.fetchall(query, tuple(params))
        return [self._row_to_job_list_item(row) for row in rows]

    async def update_job(self, job_id: int, job_data: JobUpdate) -> Optional[Job]:
        """Update a job."""
        existing = await self.get_job(job_id)
        if not existing:
            return None
        
        update_fields = []
        params = []
        
        data = job_data.model_dump(exclude_unset=True)
        
        for key, value in data.items():
            if key in ["skills"] and isinstance(value, list):
                value = json.dumps(value)
            if key in ["raw_evidence"] and isinstance(value, dict):
                value = json.dumps(value)
            update_fields.append(f"{key} = ?")
            params.append(value)
        
        if update_fields:
            params.append(job_id)
            query = f"UPDATE jobs SET {', '.join(update_fields)} WHERE id = ?"
            await self.db.execute(query, tuple(params))
            await self.db._pool.commit()  # type: ignore[union-attr]
        
        return await self.get_job(job_id)

    async def delete_job(self, job_id: int) -> bool:
        """Delete a job."""
        result = await self.db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        await self.db._pool.commit()  # type: ignore[union-attr]
        return result.rowcount > 0

    async def get_jobs_by_prefilter(self, passed: bool, limit: int = 100) -> List[Job]:
        """Get jobs filtered by prefilter status."""
        rows = await self.db.fetchall(
            "SELECT * FROM jobs WHERE passed_prefilter = ? ORDER BY discovered_at DESC LIMIT ?",
            (1 if passed else 0, limit)
        )
        return [self._row_to_job(row) for row in rows]

    def _row_to_job(self, row) -> Job:
        """Convert database row to Job model."""
        data = dict(row)
        
        # Parse JSON fields
        for key in ["skills"]:
            if data.get(key):
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    data[key] = []
            else:
                data[key] = []
        
        if data.get("raw_evidence"):
            try:
                data["raw_evidence"] = json.loads(data["raw_evidence"])
            except json.JSONDecodeError:
                data["raw_evidence"] = {}
        else:
            data["raw_evidence"] = {}
        
        return Job(**data)

    def _row_to_job_list_item(self, row) -> JobListItem:
        """Convert database row to JobListItem model."""
        data = dict(row)
        
        # Parse JSON fields
        for key in ["skills"]:
            if data.get(key):
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    data[key] = []
            else:
                data[key] = []
        
        return JobListItem(**data)