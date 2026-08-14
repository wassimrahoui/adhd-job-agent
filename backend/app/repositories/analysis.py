from __future__ import annotations

import json
from typing import Optional, List
from datetime import datetime

from app.db import Database
from app.models import AIAnalysis, AIAnalysisCreate, AIAnalysisResponse, AnalysisStatus


class AIAnalysisRepository:
    def __init__(self, db: Database):
        self.db = db

    async def create_analysis(self, analysis_data: AIAnalysisCreate) -> AIAnalysis:
        """Create a new AI analysis."""
        now = datetime.utcnow()
        data = analysis_data.model_dump()
        
        # Handle JSON fields - only serialize non-empty lists
        for key in ["matching_skills", "matching_experience", "missing_requirements", 
                   "unknown_requirements", "evidence"]:
            if data.get(key) and len(data[key]) > 0:
                data[key] = json.dumps([item.model_dump() if hasattr(item, 'model_dump') else item for item in data[key]])
            elif data.get(key) is not None:
                data[key] = json.dumps([])
        
        columns = list(data.keys())
        placeholders = ", ".join(["?" for _ in columns])
        values = list(data.values())
        
        query = f"INSERT INTO ai_analyses ({', '.join(columns)}, created_at) VALUES ({placeholders}, ?)"
        params = values + [now]
        cursor = await self.db.execute(query, tuple(params))
        await self.db._pool.commit()  # type: ignore[union-attr]
        
        analysis_id = cursor.lastrowid
        if analysis_id is None:
            raise RuntimeError("Failed to get lastrowid after insert")
        
        result = await self.get_analysis(analysis_id)
        if result is None:
            raise RuntimeError("Failed to retrieve analysis after creation")
        return result

    async def get_analysis(self, analysis_id: int) -> Optional[AIAnalysis]:
        """Get an analysis by ID."""
        row = await self.db.fetchone("SELECT * FROM ai_analyses WHERE id = ?", (analysis_id,))
        if not row:
            return None
        return self._row_to_analysis(row)

    async def get_analyses_for_job(self, job_id: int) -> List[AIAnalysis]:
        """Get all analyses for a job."""
        rows = await self.db.fetchall(
            "SELECT * FROM ai_analyses WHERE job_id = ? ORDER BY created_at DESC",
            (job_id,)
        )
        return [self._row_to_analysis(row) for row in rows]

    async def get_latest_analysis_for_job(self, job_id: int) -> Optional[AIAnalysis]:
        """Get the latest analysis for a job."""
        row = await self.db.fetchone(
            "SELECT * FROM ai_analyses WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
            (job_id,)
        )
        if not row:
            return None
        return self._row_to_analysis(row)

    def _row_to_analysis(self, row) -> AIAnalysis:
        """Convert database row to AIAnalysis model."""
        data = dict(row)
        
        # Parse JSON fields
        for key in ["matching_skills", "matching_experience", "missing_requirements", 
                   "unknown_requirements", "evidence"]:
            if data.get(key):
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    data[key] = []
            else:
                data[key] = []
        
        return AIAnalysis(**data)