from __future__ import annotations

from app.schemas.analysis import AnalysisInput, AnalysisOutput
from app.analysis.prompt_builder import build_analysis_prompt
from app.analysis.evidence_extractor import extract_evidence


class AnalysisRequestBuilder:
    """Build complete analysis requests for the LLM."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def build_request(self, input_data: AnalysisInput) -> dict:
        """Build complete request payload for Ollama."""
        prompt = build_analysis_prompt(input_data)
        schema = AnalysisOutput.model_json_schema()

        structured_prompt = f"""{prompt}

IMPORTANT: Respond ONLY with valid JSON matching this schema:
{self._format_schema(schema)}

Do not include any explanation, markdown, or text outside the JSON object."""

        return {
            "model": self.model_name,
            "prompt": structured_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
            },
        }

    def _format_schema(self, schema: dict) -> str:
        """Format JSON schema for prompt inclusion."""
        import json
        return json.dumps(schema, indent=2)


def build_analysis_request(input_data: AnalysisInput, model_name: str) -> dict:
    """Convenience function to build analysis request."""
    builder = AnalysisRequestBuilder(model_name)
    return builder.build_request(input_data)