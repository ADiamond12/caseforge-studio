from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from .models import DossierResult


SAFE_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,160}$")


class DossierStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def persist(self, result: DossierResult) -> DossierResult:
        slug = self._build_slug(result)
        output_dir = (self.root / slug).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        markdown_path = output_dir / "dossier.md"
        json_path = output_dir / "dossier.json"
        summary_path = output_dir / "summary.txt"

        persisted = replace(
            result,
            slug=slug,
            output_dir=str(output_dir),
            markdown_path=str(markdown_path),
            json_path=str(json_path),
            summary_path=str(summary_path),
        )

        markdown_path.write_text(persisted.markdown, encoding="utf-8")
        json_path.write_text(json.dumps(persisted.to_dict(), indent=2), encoding="utf-8")
        summary_path.write_text(self._build_summary(persisted), encoding="utf-8")

        return persisted

    def load_record(self, slug: str) -> dict[str, object]:
        self._validate_slug(slug)
        path = (self.root / slug / "dossier.json").resolve()
        return json.loads(path.read_text(encoding="utf-8"))

    def list_records(self, *, limit: int = 10) -> list[dict[str, str]]:
        if not self.root.exists():
            return []

        records: list[dict[str, str]] = []
        for directory in self.root.iterdir():
            json_path = directory / "dossier.json"
            if not directory.is_dir() or not json_path.exists():
                continue

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            brief = payload.get("brief", {})
            planner = payload.get("planner", {})
            evaluator = payload.get("evaluator", {})
            records.append(
                {
                    "slug": str(payload.get("slug", directory.name)),
                    "title": str(planner.get("title", directory.name)),
                    "score": f"{evaluator.get('overall_score', 'unknown')}/100",
                    "recommendation": str(evaluator.get("recommendation", "unknown")),
                    "preset": str(brief.get("preset", "general")),
                    "provider": str(brief.get("provider", "deterministic")),
                    "provider_status": str(payload.get("provider_status", "deterministic")),
                    "goal": str(brief.get("goal", "unknown")),
                    "created_at": str(payload.get("created_at", "")),
                    "summary": self._summary_snippet(payload),
                }
            )
        records.sort(
            key=lambda record: self._parse_created_at(record.get("created_at", "")),
            reverse=True,
        )
        return records[:limit]

    @staticmethod
    def _build_slug(result: DossierResult) -> str:
        timestamp = result.created_at.strftime("%Y%m%d-%H%M%S")
        return f"{result.slug}-{timestamp}"

    @staticmethod
    def _build_summary(result: DossierResult) -> str:
        return "\n".join(
            [
                f"Title: {result.planner.title}",
                f"Score: {result.evaluator.overall_score}/100",
                f"Recommendation: {result.evaluator.recommendation}",
                f"Audience: {result.brief.audience}",
                f"Mode: {result.brief.mode}",
                f"Goal: {result.brief.goal}",
                f"Preset: {result.brief.preset}",
                f"Provider: {result.brief.provider}",
                f"Provider status: {result.provider_status}",
                f"Slug: {result.slug}",
            ]
        )

    @staticmethod
    def _summary_snippet(payload: dict[str, object]) -> str:
        planner = payload.get("planner", {})
        evaluator = payload.get("evaluator", {})
        brief = payload.get("brief", {})
        objective = str(planner.get("objective", "")).strip()
        recommendation = str(evaluator.get("recommendation", "")).strip()
        goal = str(brief.get("goal", "")).strip()
        preset = str(brief.get("preset", "")).strip()
        provider = str(brief.get("provider", "")).strip()
        summary = (
            f"Recommendation: {recommendation}. Preset: {preset}. Provider: {provider}. "
            f"{objective} Goal: {goal}."
        ).strip()
        return summary[:220]

    @staticmethod
    def _parse_created_at(value: str) -> datetime:
        text = str(value).strip()
        if not text:
            return datetime.min
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min

    @staticmethod
    def _validate_slug(slug: str) -> None:
        if not SAFE_SLUG_RE.fullmatch(str(slug).strip()):
            raise ValueError("invalid blueprint slug")
