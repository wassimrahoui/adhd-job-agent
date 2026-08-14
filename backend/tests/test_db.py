import pytest
from pathlib import Path

from app.db import Database, init_db, close_db


class TestDatabase:
    @pytest.mark.asyncio
    async def test_database_initialization(self, test_db_path):
        """Test database initialization creates correct tables."""
        db = Database(test_db_path)
        await db.connect()
        
        # Check tables exist
        tables = await db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = {row['name'] for row in tables}
        
        assert 'profile' in table_names
        assert 'jobs' in table_names
        assert 'ai_analyses' in table_names
        
        # Check profile table structure
        profile_columns = await db.fetchall("PRAGMA table_info(profile)")
        profile_col_names = {row['name'] for row in profile_columns}
        assert 'id' in profile_col_names
        assert 'work_experience' in profile_col_names
        assert 'technical_skills' in profile_col_names
        assert 'desired_roles' in profile_col_names
        assert 'salary_min' in profile_col_names
        assert 'salary_max' in profile_col_names
        assert 'relevance_threshold' in profile_col_names
        
        # Check jobs table structure
        jobs_columns = await db.fetchall("PRAGMA table_info(jobs)")
        jobs_col_names = {row['name'] for row in jobs_columns}
        assert 'id' in jobs_col_names
        assert 'adzuna_id' in jobs_col_names
        assert 'title' in jobs_col_names
        assert 'company' in jobs_col_names
        assert 'passed_prefilter' in jobs_col_names
        assert 'raw_evidence' in jobs_col_names
        
        # Check ai_analyses table structure
        analyses_columns = await db.fetchall("PRAGMA table_info(ai_analyses)")
        analyses_col_names = {row['name'] for row in analyses_columns}
        assert 'id' in analyses_col_names
        assert 'job_id' in analyses_col_names
        assert 'model_used' in analyses_col_names
        assert 'score' in analyses_col_names
        assert 'recommendation' in analyses_col_names
        assert 'status' in analyses_col_names
        assert 'matching_skills' in analyses_col_names
        
        await db.close()

    @pytest.mark.asyncio
    async def test_database_indexes(self, test_db_path):
        """Test database indexes are created."""
        db = Database(test_db_path)
        await db.connect()
        
        indexes = await db.fetchall("SELECT name FROM sqlite_master WHERE type='index'")
        index_names = {row['name'] for row in indexes}
        
        # Check expected indexes
        assert 'idx_jobs_adzuna_id' in index_names
        assert 'idx_jobs_passed_prefilter' in index_names
        assert 'idx_jobs_discovered_at' in index_names
        assert 'idx_ai_analyses_job_id' in index_names
        assert 'idx_ai_analyses_created_at' in index_names
        
        await db.close()

    @pytest.mark.asyncio
    async def test_profile_unique_constraint(self, test_db_path):
        """Test profile table has unique constraint on id=1."""
        db = Database(test_db_path)
        await db.connect()
        
        # Insert first profile
        await db.execute(
            "INSERT INTO profile (id, work_experience) VALUES (1, 'First')"
        )
        await db._pool.commit()
        
        # Try to insert second profile with id=1 - should fail
        with pytest.raises(Exception):
            await db.execute(
                "INSERT INTO profile (id, work_experience) VALUES (1, 'Second')"
            )
            await db._pool.commit()
        
        await db.close()

    @pytest.mark.asyncio
    async def test_jobs_adzuna_id_unique(self, test_db_path):
        """Test jobs table has unique constraint on adzuna_id."""
        db = Database(test_db_path)
        await db.connect()
        
        # Insert first job
        await db.execute(
            "INSERT INTO jobs (adzuna_id, title) VALUES ('test-1', 'Job 1')"
        )
        await db._pool.commit()
        
        # Try to insert second job with same adzuna_id - should fail
        with pytest.raises(Exception):
            await db.execute(
                "INSERT INTO jobs (adzuna_id, title) VALUES ('test-1', 'Job 2')"
            )
            await db._pool.commit()
        
        await db.close()