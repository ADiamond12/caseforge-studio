from __future__ import annotations

from pathlib import Path

from .models import DossierResult, ProjectBrief
from .pipeline import DossierPipeline
from .providers import ProviderRegistry
from .storage import DossierStorage


class DossierService:
    def __init__(self, output_root: Path | None = None) -> None:
        project_root = Path(__file__).resolve().parent.parent
        self.output_root = (output_root or project_root / "outputs").resolve()
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.pipeline = DossierPipeline()
        self.providers = ProviderRegistry()
        self.storage = DossierStorage(self.output_root)

    def generate(self, brief: ProjectBrief) -> DossierResult:
        staged = self.providers.apply(brief, self.pipeline.run(brief))
        return self.storage.persist(staged)

    def preview(self, brief: ProjectBrief) -> DossierResult:
        return self.providers.apply(brief, self.pipeline.run(brief))

    def generate_from_payload(self, payload: dict[str, object]) -> DossierResult:
        return self.generate(self._brief_from_payload(payload))

    def preview_from_payload(self, payload: dict[str, object]) -> DossierResult:
        return self.preview(self._brief_from_payload(payload))

    def to_public_payload(self, result: DossierResult) -> dict[str, object]:
        payload = result.to_public_dict()
        payload["preview"] = False
        payload["persisted"] = True
        payload["preset"] = result.brief.preset
        payload["provider"] = result.brief.provider
        return payload

    def preview_public_payload(self, result: DossierResult) -> dict[str, object]:
        payload = result.to_public_dict()
        payload["preview"] = True
        payload["persisted"] = False
        payload["preset"] = result.brief.preset
        payload["provider"] = result.brief.provider
        return payload

    def load_record(self, slug: str) -> dict[str, object]:
        return self.storage.load_record(slug)

    def load_public_payload(self, slug: str) -> dict[str, object]:
        record = self.load_record(slug)
        overlay = record.get("provider_overlay")
        overlay_dict = overlay if isinstance(overlay, dict) else {}
        markdown_path = self._public_record_path(record, "markdown_path", slug)
        json_path = self._public_record_path(record, "json_path", slug)
        summary_path = self._public_record_path(record, "summary_path", slug)
        return {
            "slug": record.get("slug", slug),
            "title": record.get("planner", {}).get("title", slug),
            "summary": self._record_summary(record),
            "insights": self._record_insights(record),
            "sections": self._record_sections(record),
            "markdownPath": markdown_path,
            "markdown_path": markdown_path,
            "jsonPath": json_path,
            "json_path": json_path,
            "summaryPath": summary_path,
            "summary_path": summary_path,
            "preset": record.get("brief", {}).get("preset", "general"),
            "provider": record.get("brief", {}).get("provider", "deterministic"),
            "providerModel": overlay_dict.get("model") or record.get("brief", {}).get("provider_model"),
            "provider_model": overlay_dict.get("model") or record.get("brief", {}).get("provider_model"),
            "providerStatus": record.get("provider_status", "deterministic"),
            "provider_status": record.get("provider_status", "deterministic"),
            "providerMessage": record.get("provider_message", ""),
            "provider_message": record.get("provider_message", ""),
            "persisted": True,
            "preview": False,
            "dossier": record,
        }

    def list_records(self, *, limit: int = 10) -> list[dict[str, str]]:
        return self.storage.list_records(limit=limit)

    def compare_records(self, slugs: list[str]) -> dict[str, object]:
        ordered_slugs = self._normalize_compare_slugs(slugs)
        if len(ordered_slugs) != 2:
            raise ValueError("exactly two unique dossier slugs are required")

        items = [self._comparison_item(self.load_record(slug), slug) for slug in ordered_slugs]
        score_delta = abs(items[0]["score_value"] - items[1]["score_value"])
        winner_slug = None
        if items[0]["score_value"] != items[1]["score_value"]:
            winner_slug = max(items, key=lambda item: item["score_value"])["slug"]

        return {
            "items": items,
            "winner_slug": winner_slug,
            "score_delta": score_delta,
            "summary": self._comparison_summary(items, winner_slug, score_delta),
        }

    def _brief_from_payload(self, payload: dict[str, object]) -> ProjectBrief:
        return ProjectBrief(
            brief=str(payload.get("brief", "")).strip(),
            title=self._optional_text(payload.get("title")),
            audience=self._fallback_text(payload.get("audience"), "Hiring manager"),
            mode=self._fallback_text(payload.get("mode"), "AI assistant"),
            goal=self._fallback_text(payload.get("goal"), "Show systems thinking"),
            preset=self._fallback_text(payload.get("preset"), "general"),
            provider=self._fallback_text(payload.get("provider"), "deterministic"),
            provider_model=self._optional_text(payload.get("providerModel") or payload.get("provider_model")),
        )

    @staticmethod
    def _record_summary(record: dict[str, object]) -> str:
        overlay = record.get("provider_overlay")
        if isinstance(overlay, dict) and isinstance(overlay.get("summary"), str) and overlay.get("summary", "").strip():
            return overlay["summary"].strip()
        planner = record.get("planner", {})
        evaluator = record.get("evaluator", {})
        brief = record.get("brief", {})
        return (
            f"{planner.get('objective', 'No planner objective available.')} "
            f"Recommendation: {evaluator.get('recommendation', 'unknown')}. "
            f"Goal: {brief.get('goal', 'unknown')}. "
            f"Provider: {brief.get('provider', 'deterministic')}."
        )

    @staticmethod
    def _record_insights(record: dict[str, object]) -> list[str]:
        overlay = record.get("provider_overlay")
        provider_line = f"Provider: {record.get('brief', {}).get('provider', 'deterministic')} ({record.get('provider_status', 'deterministic')})"
        if isinstance(overlay, dict) and isinstance(overlay.get("insights"), list) and overlay["insights"]:
            trimmed = [str(item).strip() for item in overlay["insights"] if str(item).strip()]
            trimmed.extend(
                [
                    f"Preset: {record.get('brief', {}).get('preset', 'general')}",
                    provider_line,
                ]
            )
            return trimmed

        return [
            f"Score: {record.get('evaluator', {}).get('overall_score', 'unknown')}/100",
            f"Mode: {record.get('brief', {}).get('mode', 'unknown')}",
            f"Goal: {record.get('brief', {}).get('goal', 'unknown')}",
            f"Preset: {record.get('brief', {}).get('preset', 'general')}",
            provider_line,
        ]

    @staticmethod
    def _record_sections(record: dict[str, object]) -> list[dict[str, str]]:
        overlay = record.get("provider_overlay")
        if isinstance(overlay, dict) and isinstance(overlay.get("sections"), list) and overlay["sections"]:
            return [
                {
                    "label": str(section.get("label", "")).strip(),
                    "title": str(section.get("title", "")).strip(),
                    "body": str(section.get("body", "")).strip(),
                }
                for section in overlay["sections"]
                if isinstance(section, dict)
            ]

        return [
            {
                "label": "Problem",
                "title": "What this project solves",
                "body": record.get("planner", {}).get("objective", "No planner objective available."),
            },
            {
                "label": "Audience",
                "title": "Who the demo is aimed at",
                "body": (
                    f"The dossier is optimized for {record.get('brief', {}).get('audience', 'review').lower()} "
                    f"review and tuned to show {record.get('brief', {}).get('goal', 'project judgment').lower()}."
                ),
            },
            {
                "label": "Approach",
                "title": "How the pipeline works",
                "body": record.get("storyteller", {}).get("elevator_pitch", "No storyteller pitch available."),
            },
            {
                "label": "Architecture",
                "title": "What to build",
                "body": record.get("architect", {}).get("architecture_summary", "No architecture summary available."),
            },
            {
                "label": "Tradeoffs",
                "title": "Risks and mitigation",
                "body": DossierService._record_tradeoff(record),
            },
            {
                "label": "Interview story",
                "title": "How to present it",
                "body": record.get("storyteller", {}).get("interviewer_hook", "No interviewer hook available."),
            },
        ]

    @staticmethod
    def _record_tradeoff(record: dict[str, object]) -> str:
        risks = record.get("evaluator", {}).get("risks", [])
        mitigations = record.get("evaluator", {}).get("mitigations", [])
        if not risks and not mitigations:
            return "No tradeoff data available."
        risk = risks[0] if risks else "No risk recorded."
        mitigation = mitigations[0] if mitigations else "No mitigation recorded."
        return f"Top risk: {risk} Main mitigation: {mitigation}"

    @staticmethod
    def _optional_text(value: object) -> str | None:
        text = str(value).strip() if value is not None else ""
        return text or None

    @staticmethod
    def _public_record_path(record: dict[str, object], key: str, slug: str) -> str:
        raw = str(record.get(key, "") or "").strip()
        if not raw:
            return ""

        path = Path(raw)
        normalized = path.as_posix()
        if normalized.startswith("outputs/"):
            return normalized

        return (Path("outputs") / slug / path.name).as_posix()

    @staticmethod
    def _fallback_text(value: object, default: str) -> str:
        text = str(value).strip() if value is not None else ""
        return text or default

    @staticmethod
    def _normalize_compare_slugs(slugs: list[str]) -> list[str]:
        ordered: list[str] = []
        seen: set[str] = set()
        for slug in slugs:
            cleaned = str(slug).strip()
            if not cleaned or cleaned in seen:
                continue
            ordered.append(cleaned)
            seen.add(cleaned)
        return ordered

    @staticmethod
    def _comparison_item(record: dict[str, object], slug: str) -> dict[str, object]:
        evaluator = record.get("evaluator", {})
        brief = record.get("brief", {})
        strengths = evaluator.get("strengths", [])
        risks = evaluator.get("risks", [])
        score_value = int(evaluator.get("overall_score", 0) or 0)
        return {
            "slug": slug,
            "title": str(record.get("planner", {}).get("title", slug)),
            "score": f"{score_value}/100",
            "score_value": score_value,
            "recommendation": str(evaluator.get("recommendation", "unknown")),
            "preset": str(brief.get("preset", "general")),
            "provider": str(brief.get("provider", "deterministic")),
            "provider_status": str(record.get("provider_status", "deterministic")),
            "goal": str(brief.get("goal", "unknown")),
            "summary": DossierService._record_summary(record),
            "top_strength": str(strengths[0] if strengths else "No strength recorded."),
            "top_risk": str(risks[0] if risks else "No risk recorded."),
        }

    @staticmethod
    def _comparison_summary(items: list[dict[str, object]], winner_slug: str | None, score_delta: int) -> str:
        left = items[0]
        right = items[1]
        if winner_slug is None:
            return (
                f"{left['title']} and {right['title']} are tied on score. "
                f"Use preset, provider path, and risk profile to decide which run tells the stronger interview story."
            )

        winner = left if left["slug"] == winner_slug else right
        loser = right if winner is left else left
        return (
            f"{winner['title']} leads {loser['title']} by {score_delta} points. "
            f"Recommendation: {winner['recommendation']}. "
            f"Compare the provider path and top risk before choosing the demo artifact."
        )
