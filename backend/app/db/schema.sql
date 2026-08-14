-- SQLite Schema for ADHD Job Agent
-- Three tables: profile, jobs, ai_analyses

-- Profile table - single row (id=1)
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    work_experience TEXT,
    technical_skills TEXT, -- JSON array
    networking_experience TEXT,
    education TEXT,
    certifications TEXT, -- JSON array
    languages TEXT, -- JSON array
    desired_roles TEXT, -- JSON array
    location_preferences TEXT, -- JSON array
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT DEFAULT 'USD',
    remote_preference TEXT DEFAULT 'any',
    experience_level TEXT DEFAULT 'any',
    excluded_keywords TEXT, -- JSON array
    relevance_threshold INTEGER DEFAULT 50,
    resume_text TEXT,
    resume_file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jobs table - one row per canonical, deduplicated job
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adzuna_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    work_mode TEXT,
    employment_type TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT,
    salary_is_predicted BOOLEAN DEFAULT 0,
    description TEXT,
    requirements TEXT,
    skills TEXT, -- JSON array
    redirect_url TEXT,
    posted_at TIMESTAMP,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_evidence TEXT, -- JSON object
    passed_prefilter BOOLEAN DEFAULT 0
);

-- Indexes for jobs
CREATE INDEX IF NOT EXISTS idx_jobs_adzuna_id ON jobs(adzuna_id);
CREATE INDEX IF NOT EXISTS idx_jobs_passed_prefilter ON jobs(passed_prefilter);
CREATE INDEX IF NOT EXISTS idx_jobs_discovered_at ON jobs(discovered_at);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);

-- AI Analyses table - one row per analysis run on a job
CREATE TABLE IF NOT EXISTS ai_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    model_used TEXT NOT NULL,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    recommendation TEXT,
    confidence TEXT,
    matching_skills TEXT, -- JSON array
    matching_experience TEXT, -- JSON array
    missing_requirements TEXT, -- JSON array
    unknown_requirements TEXT, -- JSON array
    explanation TEXT,
    evidence TEXT, -- JSON array
    status TEXT NOT NULL DEFAULT 'ai_unavailable',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for ai_analyses
CREATE INDEX IF NOT EXISTS idx_ai_analyses_job_id ON ai_analyses(job_id);
CREATE INDEX IF NOT EXISTS idx_ai_analyses_created_at ON ai_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_analyses_status ON ai_analyses(status);

-- Trigger to update profile updated_at
CREATE TRIGGER IF NOT EXISTS update_profile_timestamp
AFTER UPDATE ON profile
BEGIN
    UPDATE profile SET updated_at = CURRENT_TIMESTAMP WHERE id = 1;
END;