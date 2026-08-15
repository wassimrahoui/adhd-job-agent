# AGENT_TASKS.md — ADHD Job Agent Implementation Task Tracker

## IMPORTANT: GLOBAL EXECUTION RULES

These rules apply to every task in this file.

### Rule 1 — One task at a time

The coding agent MUST execute exactly ONE task at a time.

It MUST NOT:
- implement an entire phase at once
- implement an entire layer at once
- combine multiple task IDs
- skip directly to a later task
- refactor unrelated code
- invent missing requirements
- create functionality that is explicitly excluded from this project

After completing one task, the agent MUST:
1. Run the required tests.
2. Verify the acceptance criteria.
3. Inspect the git diff.
4. Update this file.
5. Mark only that task as DONE.
6. Store useful long-term project information in Mem0.
7. Stop and wait for the next task.

### Rule 2 — Five-layer execution model

Phases 3–9 are divided into exactly five implementation layers:

- L1 — Foundation
- L2 — Component
- L3 — Logic
- L4 — Integration
- L5 — Verification

The agent MUST work through these layers sequentially.

Within each layer, every individual task is intentionally small and EASY.

The agent MUST NOT treat a complete layer as one task.

### Rule 3 — No shortcuts

The agent MUST implement the task according to its requirements.

It MUST NOT:
- replace required functionality with a placeholder
- create fake/mock production functionality
- silently remove requirements
- simplify away required validation
- skip tests
- assume functionality works without testing
- claim completion without evidence

### Rule 4 — No hallucinations

If something is unclear:
- inspect the repository
- inspect the relevant project documentation
- inspect related source files
- inspect previous task implementations
- use existing project conventions

If the required information still cannot be determined, STOP and report exactly what is missing.

Never invent:
- API fields
- database fields
- configuration values
- model capabilities
- external service behavior
- user requirements

### Rule 5 — Existing architecture has priority

Before modifying code, inspect the existing implementation.

Do not rewrite working components merely because another implementation would be possible.

Reuse existing:
- models
- repositories
- services
- configuration
- API patterns
- error handling
- testing utilities

unless the current task explicitly requires a change.

### Rule 6 — Mem0 project memory

The project uses Mem0 as the long-term project memory system.

Useful information discovered or established during development SHOULD be stored in Mem0.

Examples of useful memories:
- architectural decisions
- important implementation decisions
- API behavior
- database design decisions
- model configuration
- Ollama configuration
- important constraints
- testing conventions
- integration decisions
- known limitations
- decisions that future coding agents need to know

Do NOT store:
- temporary debugging output
- secrets
- API keys
- passwords
- tokens
- unnecessary logs
- information that is already obvious from the source code

Before making a major architectural decision, the agent SHOULD check relevant existing Mem0 memories.

After completing a task, the agent SHOULD add a useful memory when the task introduced information that future tasks should know.

### Rule 7 — Local LLM optimization

The local coding LLM has limited context compared with cloud models.

Therefore:
- keep each task narrowly scoped
- read only the documentation required by the current task
- inspect only relevant source files first
- avoid loading the entire repository unnecessarily
- do not repeat large documentation unnecessarily
- do not implement future tasks proactively

### Rule 8 — AI processing architecture

The project may use different models for different workloads.

The coding agent MUST NOT replace the selected AI architecture without an explicit task requiring it.

The intended architecture is:

- local coding LLM → software implementation
- large Ollama model → demanding local AI processing
- cloud LLM → tasks where a stronger model is intentionally selected, such as advanced job scoring
- deterministic Python logic → tasks that do not require an LLM

### Rule 9 — Explicitly removed functionality

The following functionality is NOT part of the current implementation scope:

1. Assist Me feature
2. Browser automation
3. Playwright automation
4. Automatic job applications
5. Automatic application tracking
6. Automatic email monitoring
7. Automatic email processing

These MUST NOT be reintroduced unless explicitly requested later.

The user handles email tracking separately.

### Rule 10 — Job tracking

Job application tracking is intentionally outside the current scope.

The application must focus on:
- discovering jobs
- normalizing jobs
- filtering jobs
- analyzing jobs
- scoring jobs
- presenting recommendations

Do not build application tracking functionality.

### Rule 11 — Testing

Every completed task must be testable.

A task is NOT complete merely because code was written.

Each task must:
- have a deterministic acceptance criterion
- have a test procedure
- pass the relevant tests
- leave the repository in a working state

### Rule 12 — Git

Do not make unrelated commits.

Each completed task should produce a focused commit.

Suggested format:

`feat: <task description>`

`fix: <task description>`

`test: <task description>`

`refactor: <task description>`

`chore: <task description>`

### Rule 13 — Task status

Valid statuses:

- TODO
- IN_PROGRESS
- DONE
- BLOCKED

Only change the current task to DONE after testing succeeds.

---

# Phase 1: Core Data Model (L1-L2)

## Task 1.1: Project Configuration & Setup (EASY)

- **Task ID**: T1.1
- **Task name**: Project configuration and virtual environment setup
- **Difficulty**: EASY
- **Objective**: Create pyproject.toml with FastAPI, Pydantic v2, SQLite dependencies and configure the Python project structure
- **Parent task**: Phase 1 Core Data Model
- **Documents to read**: 10-deployment-and-dev-workflow.md, 06-database-design.md
- **Source files to read**: none - new project
- **Files to modify**: backend/pyproject.toml, backend/requirements.txt
- **Dependencies**: none
- **Implementation requirements**:
  - pyproject.toml with project metadata
  - dependencies: fastapi, uvicorn, pydantic>=2, pydantic-settings, aiosqlite, python-dotenv, httpx, pytest, pytest-asyncio
  - requirements.txt generated from pyproject.toml
  - virtual environment already exists at backend/venv
- **Acceptance criteria**:
  - `pip install -e .` works in backend/
  - all dependencies resolve without conflicts
- **Test procedure**: Run `pip install -e .` and verify imports
- **Expected result**: Working Python environment
- **Commit message**: chore: add project configuration and dependencies
- **Status**: DONE

## Task 1.2: Database Models - Pydantic Schemas (EASY)

- **Task ID**: T1.2
- **Task name**: Create Pydantic models for profile, jobs, ai_analyses
- **Difficulty**: EASY
- **Objective**: Define Pydantic v2 models matching the database schema
- **Parent task**: Phase 1 Core Data Model
- **Documents to read**: 06-database-design.md, 02-ai-and-matching-architecture.md
- **Source files to read**: none - new models
- **Files to modify**: backend/app/models/__init__.py, backend/app/models/profile.py, backend/app/models/job.py, backend/app/models/analysis.py
- **Dependencies**: T1.1
- **Implementation requirements**:
  - Profile model with all documented profile fields
  - Job model with all documented job fields
  - AIAnalysis model with all documented analysis fields
  - Pydantic v2 typing
  - Optional fields where appropriate
  - JSON-compatible fields for complex data
  - No invented fields
- **Acceptance criteria**:
  - models import correctly
  - sample data validates correctly
  - invalid data is rejected appropriately
- **Test procedure**: Run model unit tests
- **Expected result**: Three functional Pydantic model groups
- **Commit message**: feat: add Pydantic models for profile, job, and AI analysis
- **Status**: DONE

## Task 1.3: Database Layer - SQLite Connection & Initialization (EASY)

- **Task ID**: T1.3
- **Task name**: SQLite connection, session management, and schema creation
- **Difficulty**: EASY
- **Objective**: Create the SQLite database layer
- **Parent task**: Phase 1 Core Data Model
- **Documents to read**: 06-database-design.md, 10-deployment-and-dev-workflow.md
- **Source files to read**: backend/app/models/
- **Files to modify**: backend/app/db/__init__.py, backend/app/db/session.py, backend/app/db/schema.sql, backend/app/db/init_db.py
- **Dependencies**: T1.2
- **Implementation requirements**:
  - aiosqlite
  - schema matching documentation
  - profile single-row behavior
  - jobs table
  - ai_analyses table
  - foreign keys
  - indexes
  - initialization logic
- **Acceptance criteria**:
  - database is created
  - tables exist
  - records can be inserted and queried
- **Test procedure**: initialize database and inspect schema
- **Expected result**: Working SQLite database
- **Commit message**: feat: add SQLite database layer
- **Status**: DONE

## Task 1.4: Database Repository/CRUD Operations (EASY)

- **Task ID**: T1.4
- **Task name**: Repository layer for Profile, Job, AIAnalysis
- **Difficulty**: EASY
- **Objective**: Implement asynchronous CRUD repositories
- **Parent task**: Phase 1 Core Data Model
- **Documents to read**: 06-database-design.md, 07-api-design.md
- **Source files to read**: backend/app/models/, backend/app/db/
- **Files to modify**: backend/app/repositories/
- **Dependencies**: T1.3
- **Implementation requirements**:
  - ProfileRepository
  - JobRepository
  - AIAnalysisRepository
  - async database operations
  - structured error handling
- **Acceptance criteria**:
  - CRUD operations work
  - data round-trips correctly
- **Test procedure**: repository tests
- **Expected result**: Functional repository layer
- **Commit message**: feat: add repository layer
- **Status**: DONE

## Task 1.5: FastAPI App Scaffolding & Health Endpoint (EASY)

- **Task ID**: T1.5
- **Task name**: FastAPI application structure and health endpoint
- **Difficulty**: EASY
- **Objective**: Create the base FastAPI application
- **Parent task**: Phase 1 Core Data Model
- **Documents to read**: 07-api-design.md, 10-deployment-and-dev-workflow.md
- **Source files to read**: backend/app/db/, backend/app/repositories/
- **Files to modify**: backend/app/main.py, backend/app/core/config.py, backend/app/api/__init__.py, backend/app/api/health.py
- **Dependencies**: T1.3, T1.4
- **Implementation requirements**:
  - FastAPI app
  - lifespan
  - configuration
  - /health
  - structured errors
  - CORS
- **Acceptance criteria**:
  - application starts
  - /health returns 200
- **Test procedure**: run server and query /health
- **Expected result**: Working FastAPI application
- **Commit message**: feat: add FastAPI app scaffolding
- **Status**: DONE

## Task 1.6: Profile API Endpoints (EASY)

- **Task ID**: T1.6
- **Task name**: GET /profile and PUT /profile
- **Difficulty**: EASY
- **Objective**: Implement profile endpoints
- **Parent task**: Phase 1 Core Data Model
- **Documents to read**: 07-api-design.md
- **Source files to read**: backend/app/main.py, backend/app/repositories/profile.py, backend/app/models/profile.py
- **Files to modify**: backend/app/api/profile.py, backend/app/schemas/profile.py
- **Dependencies**: T1.5, T1.4
- **Implementation requirements**:
  - GET /profile
  - PUT /profile
  - Pydantic request/response schemas
  - structured errors
- **Acceptance criteria**:
  - GET returns 404 when absent
  - PUT creates profile
  - PUT updates profile
- **Test procedure**: API integration tests
- **Expected result**: Working profile API
- **Commit message**: feat: add profile API endpoints
- **Status**: DONE

## Task 1.7: Jobs List & Detail API Endpoints (EASY)

- **Task ID**: T1.7
- **Task name**: GET /jobs and GET /jobs/{id}
- **Difficulty**: EASY
- **Objective**: Implement job listing and detail endpoints
- **Parent task**: Phase 1 Core Data Model
- **Documents to read**: 07-api-design.md
- **Source files to read**: backend/app/repositories/job.py, backend/app/repositories/analysis.py, backend/app/models/
- **Files to modify**: backend/app/api/jobs.py, backend/app/schemas/job.py
- **Dependencies**: T1.5, T1.4
- **Implementation requirements**:
  - pagination
  - latest analysis
  - score sorting
  - detail endpoint
  - structured errors
- **Acceptance criteria**:
  - correct response structures
  - correct 404 behavior
- **Test procedure**: API integration tests
- **Expected result**: Working jobs API
- **Commit message**: feat: add jobs list and detail endpoints
- **Status**: DONE

## Task 1.8: Unit Tests for Models & Database (EASY)

- **Task ID**: T1.8
- **Task name**: Unit tests for models and database
- **Difficulty**: EASY
- **Objective**: Test the Phase 1 foundation
- **Parent task**: Phase 1 Core Data Model
- **Documents to read**: 09-testing-strategy.md
- **Source files to read**: backend/app/models/, backend/app/db/, backend/app/repositories/
- **Files to modify**: backend/tests/
- **Dependencies**: T1.2, T1.3, T1.4
- **Implementation requirements**:
  - model tests
  - database tests
  - repository tests
  - async fixtures
- **Acceptance criteria**:
  - Phase 1 tests pass
- **Test procedure**: `pytest backend/tests/`
- **Expected result**: Passing Phase 1 test suite
- **Commit message**: test: add Phase 1 tests
- **Status**: DONE

---

# Phase 2: Job Search (L3)

## Task 2.1: JobSourceAdapter Interface & RawJobRecord Schema (EASY)

- **Task ID**: T2.1
- **Task name**: JobSourceAdapter interface and RawJobRecord
- **Difficulty**: EASY
- **Objective**: Define job-source abstraction
- **Dependencies**: T1.2, T1.4
- **Implementation requirements**:
  - JobSourceAdapter
  - RawJobRecord
  - Adzuna exceptions
  - async type hints
- **Acceptance criteria**:
  - imports work
  - sample response validates
- **Test procedure**: schema tests
- **Commit message**: feat: add JobSourceAdapter interface
- **Status**: DONE

## Task 2.2: AdzunaSourceAdapter Implementation (EASY)

- **Task ID**: T2.2
- **Task name**: Adzuna HTTP client
- **Difficulty**: EASY
- **Objective**: Implement Adzuna adapter
- **Dependencies**: T2.1
- **Implementation requirements**:
  - httpx
  - authentication
  - pagination
  - parsing
  - quota detection
- **Acceptance criteria**:
  - adapter works with fixtures
- **Test procedure**: fixture tests
- **Commit message**: feat: add AdzunaSourceAdapter
- **Status**: DONE

## Task 2.3: Query Parameter Builder from Profile (EASY)

- **Task ID**: T2.3
- **Task name**: Build Adzuna query parameters
- **Difficulty**: EASY
- **Objective**: Convert profile preferences into deterministic query parameters
- **Dependencies**: T2.1, T1.6
- **Implementation requirements**:
  - desired roles
  - locations
  - salary
  - remote preference
  - excluded keywords
- **Acceptance criteria**:
  - deterministic output
- **Test procedure**: unit tests
- **Commit message**: feat: add Adzuna query builder
- **Status**: DONE

## Task 2.4: Job Normalization & Deduplication (EASY)

- **Task ID**: T2.4
- **Task name**: Normalize and deduplicate jobs
- **Difficulty**: EASY
- **Objective**: Convert raw Adzuna data into canonical jobs
- **Dependencies**: T2.1, T1.4
- **Implementation requirements**:
  - normalization
  - deduplication
  - raw evidence preservation
  - never invent missing values
- **Acceptance criteria**:
  - normalized jobs validate
  - duplicates detected
- **Test procedure**: unit tests
- **Commit message**: feat: add job normalization and deduplication
- **Status**: DONE

## Task 2.5: POST /jobs/search Endpoint (EASY)

- **Task ID**: T2.5
- **Task name**: Job search orchestration endpoint
- **Difficulty**: EASY
- **Objective**: Connect profile, query builder, Adzuna, normalization and database
- **Dependencies**: T2.2, T2.3, T2.4, T1.7
- **Implementation requirements**:
  - current profile
  - Adzuna search
  - pagination
  - normalization
  - deduplication
  - persistence
  - summary response
- **Acceptance criteria**:
  - jobs are discovered and stored
- **Test procedure**: mocked integration tests
- **Commit message**: feat: add jobs search endpoint
- **Status**: DONE

## Task 2.6: Quota Handling (EASY)

- **Task ID**: T2.6
- **Task name**: Adzuna quota handling
- **Difficulty**: EASY
- **Objective**: Gracefully handle quota exhaustion
- **Dependencies**: T2.2, T2.5
- **Implementation requirements**:
  - detect quota
  - stop pagination
  - preserve fetched jobs
  - return explicit status
- **Acceptance criteria**:
  - partial results survive quota exhaustion
- **Test procedure**: quota fixture
- **Commit message**: feat: add Adzuna quota handling
- **Status**: DONE

## Task 2.7: Search API Tests (EASY)

- **Task ID**: T2.7
- **Task name**: Search integration tests
- **Difficulty**: EASY
- **Objective**: Test the complete search pipeline
- **Dependencies**: T2.5, T2.6
- **Implementation requirements**:
  - successful search
  - pagination
  - deduplication
  - quota
  - missing profile
- **Acceptance criteria**:
  - tests pass
- **Test procedure**: pytest
- **Commit message**: test: add search integration tests
- **Status**: DONE

---

# Five-Layer Architecture for Phases 3–9

Every phase below MUST be implemented using the following structure:

```text
Phase
├── Layer 1 — Foundation
├── Layer 2 — Component
├── Layer 3 — Logic
├── Layer 4 — Integration
└── Layer 5 — Verification
````

The purpose is to prevent the local LLM from receiving an oversized implementation task.

---

# Phase 3: Job Filtering / Pre-Filtering

## Layer 1 — Foundation

### T3.1.1: Define pre-filter input schema

* **Difficulty**: EASY
* **Dependencies**: Phase 2
* **Objective**: Define the data structure used by deterministic pre-filtering.
* **Requirements**:

  * job input
  * profile input
  * explicit filter result
  * no LLM usage
* **Acceptance criteria**: Schema validates valid input and rejects invalid input.
* **Test**: Unit tests.
* **Status**: DONE

### T3.1.2: Define pre-filter result schema

* **Difficulty**: EASY
* **Dependencies**: T3.1.1
* **Objective**: Define pass/fail/unknown filter results.
* **Acceptance criteria**: Result is serializable and deterministic.
* **Test**: Unit tests.
* **Status**: DONE

### T3.1.3: Define filter configuration

* **Difficulty**: EASY
* **Dependencies**: T3.1.1
* **Objective**: Define configurable thresholds and rules.
* **Acceptance criteria**: Configuration loads correctly.
* **Test**: Configuration test.
* **Status**: DONE

## Layer 2 — Component

### T3.2.1: Implement location filter

* **Difficulty**: EASY
* **Dependencies**: T3.1.1
* **Objective**: Compare job location against profile location preferences.
* **Acceptance criteria**: Matching and non-matching locations are handled correctly.
* **Test**: Unit tests.
* **Status**: DONE

### T3.2.2: Implement salary filter

* **Difficulty**: EASY
* **Dependencies**: T3.1.1
* **Objective**: Compare available salary information against profile minimum.
* **Acceptance criteria**: Missing salary never causes invented values.
* **Test**: Unit tests.
* **Status**: DONE

### T3.2.3: Implement employment filter

* **Difficulty**: EASY
* **Dependencies**: T3.1.1
* **Objective**: Filter employment types and work modes.
* **Acceptance criteria**: Rules are deterministic.
* **Test**: Unit tests.
* **Status**: DONE

### T3.2.4: Implement excluded-keyword filter

* **Difficulty**: EASY
* **Dependencies**: T3.1.1
* **Objective**: Reject jobs containing explicitly excluded keywords.
* **Acceptance criteria**: Case-insensitive matching works.
* **Test**: Unit tests.
* **Status**: DONE

## Layer 3 — Logic

### T3.3.1: Implement filter pipeline

* **Difficulty**: EASY
* **Dependencies**: T3.2.1, T3.2.2, T3.2.3, T3.2.4
* **Objective**: Run deterministic filters in defined order.
* **Acceptance criteria**: Same input always produces same result.
* **Test**: Pipeline tests.
* **Status**: DONE

### T3.3.2: Implement filter reason collection

* **Difficulty**: EASY
* **Dependencies**: T3.3.1
* **Objective**: Record why a job passed or failed.
* **Acceptance criteria**: Reasons are explicit and machine-readable.
* **Test**: Unit tests.
* **Status**: DONE

### T3.3.3: Implement passed_prefilter persistence

* **Difficulty**: EASY
* **Dependencies**: T3.3.1
* **Objective**: Store the pre-filter result on the Job record.
* **Acceptance criteria**: Database value matches filtering result.
* **Test**: Repository test.
* **Status**: DONE

## Layer 4 — Integration

### T3.4.1: Connect filtering to job search

* **Difficulty**: EASY
* **Dependencies**: T3.3.1, T3.3.3
* **Objective**: Apply filtering after normalization.
* **Acceptance criteria**: Search pipeline records filter state.
* **Test**: Integration test.
* **Status**: DONE

### T3.4.2: Expose filtering state through API

* **Difficulty**: EASY
* **Dependencies**: T3.4.1
* **Objective**: Include filtering state in job responses.
* **Acceptance criteria**: API returns correct state.
* **Test**: API test.
* **Status**: DONE

## Layer 5 — Verification

### T3.5.1: Pre-filter unit test suite

* **Difficulty**: EASY
* **Dependencies**: Layers 1–3
* **Objective**: Test all deterministic filters.
* **Acceptance criteria**: All tests pass.
* **Status**: DONE

### T3.5.2: Pre-filter integration tests

* **Difficulty**: EASY
* **Dependencies**: Layer 4
* **Objective**: Test filtering inside the search pipeline.
* **Acceptance criteria**: End-to-end pipeline behaves correctly.
* **Status**: DONE

### T3.5.3: Phase 3 regression verification

* **Difficulty**: EASY
* **Dependencies**: T3.5.1, T3.5.2
* **Objective**: Ensure Phase 1–2 behavior remains functional.
* **Acceptance criteria**: Full relevant test suite passes.
* **Status**: DONE

---

# Phase 4: Job Analysis Pipeline

## Layer 1 — Foundation

### T4.1.1: Define analysis input schema

* **Difficulty**: EASY
* **Dependencies**: Phase 3
* **Objective**: Define the exact data supplied to the analysis model.
* **Acceptance criteria**: Schema validates.
* **Status**: DONE

### T4.1.2: Define analysis output schema

* **Difficulty**: EASY
* **Dependencies**: T4.1.1
* **Objective**: Define structured AI analysis output.
* **Acceptance criteria**: Output can be validated without accepting arbitrary malformed data.
* **Status**: DONE

### T4.1.3: Define analysis status values

* **Difficulty**: EASY
* **Dependencies**: T4.1.2
* **Objective**: Define pending/success/failed states.
* **Acceptance criteria**: Status values are centralized.
* **Status**: DONE

## Layer 2 — Component

### T4.2.1: Create analysis prompt builder

* **Difficulty**: EASY
* **Dependencies**: T4.1.1
* **Objective**: Build deterministic prompts from profile and job evidence.
* **Requirements**:

  * no invented job facts
  * no invented profile facts
  * evidence must remain traceable
* **Status**: DONE

### T4.2.2: Create Ollama analysis client

* **Difficulty**: EASY
* **Dependencies**: T4.1.1
* **Objective**: Create client for the configured large Ollama model.
* **Acceptance criteria**: Client sends and receives structured requests.
* **Status**: DONE

### T4.2.3: Create analysis response parser

* **Difficulty**: EASY
* **Dependencies**: T4.1.2
* **Objective**: Parse model output into validated schema.
* **Status**: DONE

## Layer 3 — Logic

### T4.3.1: Implement evidence extraction

* **Difficulty**: EASY
* **Dependencies**: T4.2.1
* **Objective**: Extract relevant evidence from job/profile data.
* **Status**: DONE

### T4.3.2: Implement analysis request construction

* **Difficulty**: EASY
* **Dependencies**: T4.2.1, T4.3.1
* **Objective**: Construct complete model request.
* **Status**: DONE

### T4.3.3: Implement invalid-output handling

* **Difficulty**: EASY
* **Dependencies**: T4.2.3
* **Objective**: Safely handle malformed LLM responses.
* **Status**: DONE

## Layer 4 — Integration

### T4.4.1: Connect analysis to Ollama

* **Difficulty**: EASY
* **Dependencies**: T4.2.2, T4.3.2
* **Status**: DONE

### T4.4.2: Persist AI analysis

* **Difficulty**: EASY
* **Dependencies**: T4.2.3, T4.4.1
* **Status**: DONE

### T4.4.3: Connect analysis to filtered jobs

* **Difficulty**: EASY
* **Dependencies**: T3.4.1, T4.4.2
* **Status**: DONE

## Layer 5 — Verification

### T4.5.1: Test prompt construction

* **Difficulty**: EASY
* **Status**: DONE

### T4.5.2: Test structured model parsing

* **Difficulty**: EASY
* **Status**: DONE

### T4.5.3: Test analysis pipeline

* **Difficulty**: EASY
* **Status**: DONE

---

# Phase 5: AI Job Scoring

The scoring component may use a cloud LLM because scoring quality is more important than using the local model for this specific workload.

The implementation MUST remain evidence-based and MUST NOT invent qualifications.

## Layer 1 — Foundation

### T5.1.1: Define scoring input

* **Difficulty**: EASY
* **Dependencies**: Phase 4
* **Status**: DONE

### T5.1.2: Define scoring output

* **Difficulty**: EASY
* **Dependencies**: T5.1.1
* **Status**: DONE

### T5.1.3: Define scoring scale and thresholds

* **Difficulty**: EASY
* **Dependencies**: T5.1.2
* **Status**: DONE

## Layer 2 — Component

### T5.2.1: Create scoring prompt

* **Difficulty**: EASY
* **Dependencies**: T5.1.1
* **Status**: DONE

### T5.2.2: Create cloud LLM scoring client

* **Difficulty**: EASY
* **Dependencies**: T5.1.1
* **Status**: DONE

### T5.2.3: Create scoring response validator

* **Difficulty**: EASY
* **Dependencies**: T5.1.2
* **Status**: DONE

## Layer 3 — Logic

### T5.3.1: Implement skills scoring

* **Difficulty**: EASY
* **Dependencies**: T5.2.1
* **Status**: DONE

### T5.3.2: Implement experience scoring

* **Difficulty**: EASY
* **Dependencies**: T5.2.1
* **Status**: DONE

### T5.3.3: Implement requirements scoring

* **Difficulty**: EASY
* **Dependencies**: T5.2.1
* **Status**: DONE

### T5.3.4: Implement evidence-based final score

* **Difficulty**: EASY
* **Dependencies**: T5.3.1, T5.3.2, T5.3.3
* **Status**: DONE

## Layer 4 — Integration

### T5.4.1: Connect scoring client

* **Difficulty**: EASY
* **Dependencies**: T5.2.2, T5.3.4
* **Status**: DONE

### T5.4.2: Persist score

* **Difficulty**: EASY
* **Dependencies**: T5.2.3, T5.4.1
* **Status**: DONE

### T5.4.3: Connect score to job API

* **Difficulty**: EASY
* **Dependencies**: T5.4.2
* **Status**: DONE

## Layer 5 — Verification

### T5.5.1: Score validation tests

* **Difficulty**: EASY
* **Status**: DONE

### T5.5.2: Hallucination-resistance tests

* **Difficulty**: EASY
* **Objective**: Ensure missing information becomes UNKNOWN rather than invented.
* **Status**: DONE

### T5.5.3: Full scoring integration tests

* **Difficulty**: EASY
* **Status**: DONE

---

# Phase 6: Recommendation Engine

## Layer 1 — Foundation

### T6.1.1: Define recommendation categories

* **Difficulty**: EASY
* **Dependencies**: Phase 5
* **Status**: DONE

### T6.1.2: Define recommendation schema

* **Difficulty**: EASY
* **Dependencies**: T6.1.1
* **Status**: DONE

### T6.1.3: Define recommendation thresholds

* **Difficulty**: EASY
* **Dependencies**: T6.1.2
* **Status**: DONE

## Layer 2 — Component

### T6.2.1: Create recommendation evaluator

* **Difficulty**: EASY
* **Dependencies**: T6.1.2
* **Status**: DONE

### T6.2.2: Create explanation generator

* **Difficulty**: EASY
* **Dependencies**: T6.1.2
* **Status**: DONE

### T6.2.3: Create evidence formatter

* **Difficulty**: EASY
* **Dependencies**: T6.1.2
* **Status**: DONE

## Layer 3 — Logic

### T6.3.1: Implement recommendation rules

* **Difficulty**: EASY
* **Dependencies**: T6.2.1
* **Status**: DONE

### T6.3.2: Implement confidence handling

* **Difficulty**: EASY
* **Dependencies**: T6.2.1
* **Status**: DONE

### T6.3.3: Implement missing/unknown requirement handling

* **Difficulty**: EASY
* **Dependencies**: T6.2.3
* **Status**: TODO

## Layer 4 — Integration

### T6.4.1: Connect recommendation to score

* **Difficulty**: EASY
* **Dependencies**: T6.3.1
* **Status**: DONE

### T6.4.2: Persist recommendation

* **Difficulty**: EASY
* **Dependencies**: T6.4.1
* **Status**: DONE

### T6.4.3: Expose recommendation through API

* **Difficulty**: EASY
* **Dependencies**: T6.4.2
* **Status**: DONE

## Layer 5 — Verification

### T6.5.1: Recommendation unit tests

* **Difficulty**: EASY
* **Status**: TODO

### T6.5.2: Edge-case tests

* **Difficulty**: EASY
* **Status**: TODO

### T6.5.3: Full recommendation integration tests

* **Difficulty**: EASY
* **Status**: TODO

---

# Phase 7: AI Processing Orchestration

This phase coordinates the existing components.

It MUST NOT introduce browser automation, automatic applications, application tracking, or email monitoring.

## Layer 1 — Foundation

### T7.1.1: Define processing job state

* **Difficulty**: EASY
* **Status**: TODO

### T7.1.2: Define processing request schema

* **Difficulty**: EASY
* **Dependencies**: T7.1.1
* **Status**: TODO

### T7.1.3: Define processing response schema

* **Difficulty**: EASY
* **Dependencies**: T7.1.2
* **Status**: TODO

## Layer 2 — Component

### T7.2.1: Create analysis service

* **Difficulty**: EASY
* **Dependencies**: Phase 4
* **Status**: TODO

### T7.2.2: Create scoring service

* **Difficulty**: EASY
* **Dependencies**: Phase 5
* **Status**: TODO

### T7.2.3: Create recommendation service

* **Difficulty**: EASY
* **Dependencies**: Phase 6
* **Status**: TODO

## Layer 3 — Logic

### T7.3.1: Implement sequential processing

* **Difficulty**: EASY
* **Dependencies**: T7.2.1, T7.2.2, T7.2.3
* **Status**: TODO

### T7.3.2: Implement failure isolation

* **Difficulty**: EASY
* **Dependencies**: T7.3.1
* **Status**: TODO

### T7.3.3: Implement processing status

* **Difficulty**: EASY
* **Dependencies**: T7.3.1
* **Status**: TODO

## Layer 4 — Integration

### T7.4.1: Connect jobs to analysis

* **Difficulty**: EASY
* **Dependencies**: T7.3.1
* **Status**: TODO

### T7.4.2: Connect analysis to scoring

* **Difficulty**: EASY
* **Dependencies**: T7.4.1
* **Status**: TODO

### T7.4.3: Connect scoring to recommendations

* **Difficulty**: EASY
* **Dependencies**: T7.4.2
* **Status**: TODO

### T7.4.4: Create processing API endpoint

* **Difficulty**: EASY
* **Dependencies**: T7.4.3
* **Status**: TODO

## Layer 5 — Verification

### T7.5.1: Processing unit tests

* **Difficulty**: EASY
* **Status**: TODO

### T7.5.2: Failure handling tests

* **Difficulty**: EASY
* **Status**: TODO

### T7.5.3: Full processing pipeline test

* **Difficulty**: EASY
* **Status**: TODO

---

# Phase 8: Frontend / User Interface

The frontend MUST focus on viewing and managing job information.

No Assist Me feature is permitted.

No browser automation is permitted.

No automatic application functionality is permitted.

## Layer 1 — Foundation

### T8.1.1: Create frontend project structure

* **Difficulty**: EASY
* **Status**: TODO

### T8.1.2: Create API client

* **Difficulty**: EASY
* **Dependencies**: T8.1.1
* **Status**: TODO

### T8.1.3: Create frontend configuration

* **Difficulty**: EASY
* **Dependencies**: T8.1.1
* **Status**: TODO

## Layer 2 — Component

### T8.2.1: Create profile page

* **Difficulty**: EASY
* **Dependencies**: T8.1.2
* **Status**: TODO

### T8.2.2: Create jobs list page

* **Difficulty**: EASY
* **Dependencies**: T8.1.2
* **Status**: TODO

### T8.2.3: Create job detail page

* **Difficulty**: EASY
* **Dependencies**: T8.1.2
* **Status**: TODO

### T8.2.4: Create search control

* **Difficulty**: EASY
* **Dependencies**: T8.1.2
* **Status**: TODO

## Layer 3 — Logic

### T8.3.1: Implement job list state

* **Difficulty**: EASY
* **Dependencies**: T8.2.2
* **Status**: TODO

### T8.3.2: Implement score/recommendation display logic

* **Difficulty**: EASY
* **Dependencies**: T8.2.2
* **Status**: TODO

### T8.3.3: Implement filtering and sorting controls

* **Difficulty**: EASY
* **Dependencies**: T8.3.1
* **Status**: TODO

### T8.3.4: Implement job detail evidence display

* **Difficulty**: EASY
* **Dependencies**: T8.2.3
* **Status**: TODO

## Layer 4 — Integration

### T8.4.1: Connect profile UI to API

* **Difficulty**: EASY
* **Dependencies**: T8.2.1
* **Status**: TODO

### T8.4.2: Connect job list to API

* **Difficulty**: EASY
* **Dependencies**: T8.2.2
* **Status**: TODO

### T8.4.3: Connect job detail to API

* **Difficulty**: EASY
* **Dependencies**: T8.2.3
* **Status**: TODO

### T8.4.4: Connect search to API

* **Difficulty**: EASY
* **Dependencies**: T8.2.4
* **Status**: TODO

## Layer 5 — Verification

### T8.5.1: Frontend component tests

* **Difficulty**: EASY
* **Status**: TODO

### T8.5.2: API integration tests

* **Difficulty**: EASY
* **Status**: TODO

### T8.5.3: UI workflow verification

* **Difficulty**: EASY
* **Status**: TODO

---

# Phase 9: Final Integration, Security, Testing and Deployment

## Layer 1 — Foundation

### T9.1.1: Review configuration and secrets

* **Difficulty**: EASY
* **Objective**: Ensure secrets are configuration-driven and not hardcoded.
* **Status**: TODO

### T9.1.2: Review logging configuration

* **Difficulty**: EASY
* **Status**: TODO

### T9.1.3: Review error handling

* **Difficulty**: EASY
* **Status**: TODO

### T9.1.4: Review dependency versions

* **Difficulty**: EASY
* **Status**: TODO

## Layer 2 — Component

### T9.2.1: Add security middleware

* **Difficulty**: EASY
* **Status**: TODO

### T9.2.2: Add input validation review

* **Difficulty**: EASY
* **Status**: TODO

### T9.2.3: Add API error sanitization

* **Difficulty**: EASY
* **Status**: TODO

### T9.2.4: Add LLM output validation

* **Difficulty**: EASY
* **Status**: TODO

## Layer 3 — Logic

### T9.3.1: Implement safe failure behavior

* **Difficulty**: EASY
* **Status**: TODO

### T9.3.2: Implement AI timeout handling

* **Difficulty**: EASY
* **Status**: TODO

### T9.3.3: Implement external API failure handling

* **Difficulty**: EASY
* **Status**: TODO

### T9.3.4: Implement database failure handling

* **Difficulty**: EASY
* **Status**: TODO

## Layer 4 — Integration

### T9.4.1: Run complete backend integration

* **Difficulty**: EASY
* **Dependencies**: Phases 1–7
* **Status**: TODO

### T9.4.2: Run frontend/backend integration

* **Difficulty**: EASY
* **Dependencies**: Phase 8
* **Status**: TODO

### T9.4.3: Verify Ollama integration

* **Difficulty**: EASY
* **Dependencies**: Phase 4
* **Status**: TODO

### T9.4.4: Verify cloud scoring integration

* **Difficulty**: EASY
* **Dependencies**: Phase 5
* **Status**: TODO

## Layer 5 — Verification

### T9.5.1: Run complete automated test suite

* **Difficulty**: EASY
* **Objective**: Run all available tests.
* **Acceptance criteria**: All tests pass.
* **Status**: TODO

### T9.5.2: Run security verification

* **Difficulty**: EASY
* **Objective**: Verify secrets, validation, error handling and exposed endpoints.
* **Acceptance criteria**: No known critical security issue remains.
* **Status**: TODO

### T9.5.3: Run complete user workflow test

* **Difficulty**: EASY
* **Objective**: Verify:

  1. profile configuration
  2. job search
  3. normalization
  4. pre-filtering
  5. AI analysis
  6. scoring
  7. recommendation
  8. frontend display
* **Acceptance criteria**: Complete workflow succeeds.
* **Status**: TODO

### T9.5.4: Final documentation verification

* **Difficulty**: EASY
* **Objective**: Ensure documentation matches the actual implementation.
* **Acceptance criteria**: No obsolete functionality is documented as active.
* **Status**: TODO

### T9.5.5: Final repository verification

* **Difficulty**: EASY
* **Objective**: Verify clean repository state and focused commits.
* **Acceptance criteria**:

  * tests pass
  * no accidental files
  * no secrets
  * no unrelated modifications
  * architecture matches documentation
* **Status**: TODO

---

# FINAL IMPLEMENTATION ORDER

The coding agent MUST follow this order:

```text
Phase 1
  ↓
Phase 2
  ↓
Phase 3
  ├── L1 Foundation
  ├── L2 Component
  ├── L3 Logic
  ├── L4 Integration
  └── L5 Verification
  ↓
Phase 4
  ├── L1 Foundation
  ├── L2 Component
  ├── L3 Logic
  ├── L4 Integration
  └── L5 Verification
  ↓
Phase 5
  ├── L1 Foundation
  ├── L2 Component
  ├── L3 Logic
  ├── L4 Integration
  └── L5 Verification
  ↓
Phase 6
  ├── L1 Foundation
  ├── L2 Component
  ├── L3 Logic
  ├── L4 Integration
  └── L5 Verification
  ↓
Phase 7
  ├── L1 Foundation
  ├── L2 Component
  ├── L3 Logic
  ├── L4 Integration
  └── L5 Verification
  ↓
Phase 8
  ├── L1 Foundation
  ├── L2 Component
  ├── L3 Logic
  ├── L4 Integration
  └── L5 Verification
  ↓
Phase 9
  ├── L1 Foundation
  ├── L2 Component
  ├── L3 Logic
  ├── L4 Integration
  └── L5 Verification
```

# FINAL AGENT BEHAVIOR

The agent MUST NOT say:

> "I will implement Phase 5."

Instead it MUST say:

> "I will identify the first TODO task whose dependencies are satisfied and implement only that task."

After completion:

> "Task completed, tests passed, acceptance criteria verified, task marked DONE, relevant project memory updated in Mem0. Stopping."

Then it MUST STOP.

The next task is started only by the next agent invocation.
