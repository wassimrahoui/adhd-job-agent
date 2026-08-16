from __future__ import annotations

from app.schemas.processing import (
    ProcessingJobState,
    ProcessingRequest,
    JobProcessingResult,
    ProcessingResponse,
)


class TestProcessingJobState:
    def test_all_states_present(self):
        values = {s.value for s in ProcessingJobState}
        assert values == {
            "pending",
            "analyzing",
            "scoring",
            "recommending",
            "completed",
            "failed",
            "skipped",
        }


class TestProcessingRequest:
    def test_defaults(self):
        req = ProcessingRequest()
        assert req.only_passed is True
        assert req.limit == 50
        assert req.skip_existing is True

    def test_custom_values(self):
        req = ProcessingRequest(only_passed=False, limit=10, skip_existing=False)
        assert req.only_passed is False
        assert req.limit == 10
        assert req.skip_existing is False

    def test_limit_bounds(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProcessingRequest(limit=0)
        with pytest.raises(ValidationError):
            ProcessingRequest(limit=201)


class TestJobProcessingResult:
    def test_completed_result_no_error(self):
        result = JobProcessingResult(job_id=1, state=ProcessingJobState.COMPLETED)
        assert result.error is None

    def test_failed_result_with_error(self):
        result = JobProcessingResult(job_id=2, state=ProcessingJobState.FAILED, error="scoring: boom")
        assert result.error == "scoring: boom"


class TestProcessingResponse:
    def test_empty_response(self):
        resp = ProcessingResponse(jobs_total=0, processed=0, failed=0, skipped=0)
        assert resp.results == []

    def test_response_with_results(self):
        results = [
            JobProcessingResult(job_id=1, state=ProcessingJobState.COMPLETED),
            JobProcessingResult(job_id=2, state=ProcessingJobState.FAILED, error="analyzing: timeout"),
        ]
        resp = ProcessingResponse(jobs_total=2, processed=1, failed=1, skipped=0, results=results)
        assert len(resp.results) == 2
        assert resp.processed + resp.failed + resp.skipped == resp.jobs_total
