from __future__ import annotations

import json
import re
from typing import Optional

from pydantic import ValidationError

from app.schemas.analysis import AnalysisOutput, AnalysisStatus


class ResponseParserError(Exception):
    """Base exception for response parser errors."""
    def __init__(self, message: str, error_code: str = "PARSER_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class JSONParseError(ResponseParserError):
    def __init__(self, message: str = "Failed to parse JSON from response"):
        super().__init__(message, "JSON_PARSE_ERROR")


class SchemaValidationError(ResponseParserError):
    def __init__(self, message: str = "Response validation failed"):
        super().__init__(message, "VALIDATION_ERROR")


def extract_json(text: str) -> str:
    """Extract JSON object from text that may contain extra content."""
    text = text.strip()
    
    # Try direct JSON first
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object in markdown code blocks
    code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in matches:
        try:
            json.loads(match)
            return match
        except json.JSONDecodeError:
            continue
    
    # Try to find first complete JSON object
    brace_count = 0
    start_idx = -1
    for i, char in enumerate(text):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            if brace_count > 0:
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    candidate = text[start_idx:i+1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        continue
    
    raise JSONParseError(f"No valid JSON object found in response: {text[:200]}")


def parse_analysis_response(response_text: str, model_used: str) -> AnalysisOutput:
    """Parse LLM response into validated AnalysisOutput."""
    try:
        json_text = extract_json(response_text)
        data = json.loads(json_text)
    except JSONParseError:
        raise
    except json.JSONDecodeError as e:
        raise JSONParseError(f"Invalid JSON: {e}")
    
    # Ensure model_used is set
    data["model_used"] = model_used
    
    # Set default status if not provided
    if "status" not in data:
        data["status"] = AnalysisStatus.SUCCESS
    
    try:
        return AnalysisOutput.model_validate(data)
    except ValidationError as e:
        raise SchemaValidationError(f"Response validation failed: {e}")


def parse_analysis_response_safe(response_text: str, model_used: str) -> tuple[Optional[AnalysisOutput], Optional[str]]:
    """Parse response safely, returning (result, error_message)."""
    try:
        result = parse_analysis_response(response_text, model_used)
        return result, None
    except ResponseParserError as e:
        return None, e.message
    except Exception as e:
        return None, f"Unexpected error: {e}"