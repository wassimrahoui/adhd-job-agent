from __future__ import annotations

import json
from typing import Optional
from datetime import datetime

from app.db import Database
from app.models import Profile, ProfileCreate, ProfileUpdate


class ProfileRepository:
    def __init__(self, db: Database):
        self.db = db

    async def get_profile(self) -> Optional[Profile]:
        """Get the single user profile (id=1)."""
        row = await self.db.fetchone("SELECT * FROM profile WHERE id = 1")
        if not row:
            return None
        return self._row_to_profile(row)

    async def upsert_profile(self, profile_data: ProfileCreate | ProfileUpdate) -> Profile:
        """Create or update the single user profile."""
        existing = await self.get_profile()
        now = datetime.utcnow()
        
        if existing:
            # Update existing profile
            update_fields = []
            params = []
            
            data = profile_data.model_dump(exclude_unset=True) if isinstance(profile_data, ProfileUpdate) else profile_data.model_dump()
            
            for key, value in data.items():
                if key in ["technical_skills", "certifications", "languages", "desired_roles", 
                          "location_preferences", "excluded_keywords"] and value is not None:
                    value = json.dumps(value)
                update_fields.append(f"{key} = ?")
                params.append(value)
            
            if update_fields:
                params.append(now)
                params.append(1)
                query = f"UPDATE profile SET {', '.join(update_fields)}, updated_at = ? WHERE id = ?"
                await self.db.execute(query, tuple(params))
                await self.db._pool.commit()  # type: ignore[union-attr]
            
            result = await self.get_profile()
            if result is None:
                raise RuntimeError("Failed to retrieve profile after update")
            return result
        else:
            # Create new profile
            data = profile_data.model_dump()
            
            for key in ["technical_skills", "certifications", "languages", "desired_roles", 
                       "location_preferences", "excluded_keywords"]:
                if key in data and data[key] is not None:
                    data[key] = json.dumps(data[key])
            
            columns = list(data.keys())
            placeholders = ", ".join(["?" for _ in columns])
            values = list(data.values())
            
            query = f"INSERT INTO profile (id, {', '.join(columns)}, created_at, updated_at) VALUES (1, {placeholders}, ?, ?)"
            params = values + [now, now]
            await self.db.execute(query, tuple(params))
            await self.db._pool.commit()  # type: ignore[union-attr]
            
            result = await self.get_profile()
            if result is None:
                raise RuntimeError("Failed to retrieve profile after creation")
            return result

    def _row_to_profile(self, row) -> Profile:
        """Convert database row to Profile model."""
        data = dict(row)
        
        # Parse JSON fields
        for key in ["technical_skills", "certifications", "languages", "desired_roles", 
                   "location_preferences", "excluded_keywords"]:
            if data.get(key):
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    data[key] = []
            else:
                data[key] = []
        
        return Profile(**data)