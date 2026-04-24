from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .markdown import render_markdown
from .models import DossierResult, DossierSection, ProjectBrief, ProviderOverlay


class ProviderError(RuntimeError):
    pass


class DossierProvider(ABC):
    name: str

    @abstractmethod
    def apply(self, brief: ProjectBrief, result: DossierResult) -> DossierResult:
        raise NotImplementedError


class DeterministicProvider(DossierProvider):
    name = "deterministic"

    def apply(self, brief: ProjectBrief, result: DossierResult) -> DossierResult:
        return replace(
            result,
            provider_status="deterministic",
            provider_message="Deterministic pipeline used.",
            markdown=_render_result_markdown(
                result,
                provider_status="deterministic",
                provider_message="Deterministic pipeline used.",
                provider_overlay=None,
            ),
        )


class OpenAIResponsesProvider(DossierProvider):
    name = "openai"

    def apply(self, brief: ProjectBrief, result: DossierResult) -> DossierResult:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderError("OPENAI_API_KEY is not set; falling back to deterministic mode.")

        model = brief.provider_model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
        endpoint = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/responses")
        payload = self._build_payload(brief, result, model)

        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=45) as response:
                raw_response = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:  # pragma: no cover - exercised via ProviderError behavior
            raise ProviderError(f"OpenAI request failed with status {exc.code}; falling back to deterministic mode.") from exc
        except URLError as exc:  # pragma: no cover - exercised via ProviderError behavior
            raise ProviderError(f"Could not reach OpenAI endpoint: {exc.reason}; falling back to deterministic mode.") from exc
        except TimeoutError as exc:  # pragma: no cover
            raise ProviderError("OpenAI request timed out; falling back to deterministic mode.") from exc

        overlay = self._parse_overlay(raw_response, model=model)
        message = f"Live OpenAI overlay generated with {model}."
        return replace(
            result,
            provider_status="live",
            provider_message=message,
            provider_overlay=overlay,
            markdown=_render_result_markdown(
                result,
                provider_status="live",
                provider_message=message,
                provider_overlay=overlay,
            ),
        )

    def _build_payload(self, brief: ProjectBrief, result: DossierResult, model: str) -> dict[str, object]:
        prompt = "\n\n".join(
            [
                "You are refining the public-facing output of an implementation-ready project blueprint.",
                "Return only JSON that follows the schema.",
                "Keep the output concise, concrete, and industry-ready.",
                f"Brief:\n{brief.brief.strip()}",
                f"Audience: {brief.audience}",
                f"Mode: {brief.mode}",
                f"Goal: {brief.goal}",
                f"Preset: {brief.preset}",
                "Deterministic blueprint context:",
                result.markdown,
            ]
        )
        return {
            "model": model,
            "store": False,
            "input": prompt,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "caseforge_public_overlay",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["summary", "insights", "sections"],
                        "properties": {
                            "summary": {"type": "string"},
                            "insights": {
                                "type": "array",
                                "minItems": 3,
                                "maxItems": 4,
                                "items": {"type": "string"},
                            },
                            "sections": {
                                "type": "array",
                                "minItems": 6,
                                "maxItems": 6,
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["label", "title", "body"],
                                    "properties": {
                                        "label": {"type": "string"},
                                        "title": {"type": "string"},
                                        "body": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                }
            },
        }

    def _parse_overlay(self, response_json: dict[str, object], *, model: str) -> ProviderOverlay:
        text = self._extract_output_text(response_json)
        if not text:
            raise ProviderError("OpenAI returned no output text; falling back to deterministic mode.")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError("OpenAI returned invalid JSON; falling back to deterministic mode.") from exc

        sections = tuple(
            DossierSection(
                label=str(section.get("label", "")).strip(),
                title=str(section.get("title", "")).strip(),
                body=str(section.get("body", "")).strip(),
            )
            for section in parsed.get("sections", [])
        )
        if not sections:
            raise ProviderError("OpenAI overlay returned no sections; falling back to deterministic mode.")

        return ProviderOverlay(
            provider=self.name,
            model=model,
            summary=str(parsed.get("summary", "")).strip(),
            insights=tuple(str(item).strip() for item in parsed.get("insights", []) if str(item).strip()),
            sections=sections,
        )

    @staticmethod
    def _extract_output_text(response_json: dict[str, object]) -> str:
        direct = response_json.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()

        parts: list[str] = []
        for item in response_json.get("output", []):
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if not isinstance(content, dict):
                    continue
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n".join(parts).strip()


class ProviderRegistry:
    def __init__(self, providers: Iterable[DossierProvider] | None = None) -> None:
        provider_list = providers or (DeterministicProvider(), OpenAIResponsesProvider())
        self.providers = {provider.name: provider for provider in provider_list}

    def apply(self, brief: ProjectBrief, result: DossierResult) -> DossierResult:
        provider_name = brief.provider.strip().lower() or "deterministic"
        provider = self.providers.get(provider_name)
        if provider is None:
            message = f"Unknown provider '{provider_name}'; falling back to deterministic mode."
            return replace(
                self.providers["deterministic"].apply(replace(brief, provider="deterministic"), result),
                provider_status="fallback",
                provider_message=message,
                markdown=_render_result_markdown(
                    result,
                    provider_status="fallback",
                    provider_message=message,
                    provider_overlay=None,
                ),
            )

        if provider_name == "deterministic":
            return provider.apply(brief, result)

        try:
            return provider.apply(brief, result)
        except ProviderError as exc:
            message = str(exc)
            return replace(
                self.providers["deterministic"].apply(replace(brief, provider="deterministic"), result),
                provider_status="fallback",
                provider_message=message,
                markdown=_render_result_markdown(
                    result,
                    provider_status="fallback",
                    provider_message=message,
                    provider_overlay=None,
                ),
            )


def _render_result_markdown(
    result: DossierResult,
    *,
    provider_status: str,
    provider_message: str,
    provider_overlay: ProviderOverlay | None,
) -> str:
    return render_markdown(
        result.brief,
        result.planner,
        result.architect,
        result.evaluator,
        result.storyteller,
        created_at=result.created_at,
        provider_status=provider_status,
        provider_message=provider_message,
        provider_overlay=provider_overlay,
    )
