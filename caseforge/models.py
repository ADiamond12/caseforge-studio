from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProjectBrief:
    brief: str
    title: str | None = None
    audience: str = "interview"
    mode: str = "AI assistant"
    goal: str = "Show systems thinking"
    preset: str = "general"
    provider: str = "deterministic"
    provider_model: str | None = None


@dataclass(frozen=True, slots=True)
class PlannerResult:
    title: str
    objective: str
    audience: str
    themes: tuple[str, ...]
    assumptions: tuple[str, ...]
    success_metrics: tuple[str, ...]
    scope: tuple[str, ...]
    delivery_plan: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArchitectResult:
    architecture_summary: str
    modules: tuple[str, ...]
    data_flow: tuple[str, ...]
    api_surface: tuple[str, ...]
    persistence_plan: tuple[str, ...]
    implementation_notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvaluatorResult:
    overall_score: int
    strengths: tuple[str, ...]
    risks: tuple[str, ...]
    mitigations: tuple[str, ...]
    recommendation: str


@dataclass(frozen=True, slots=True)
class StorytellerResult:
    elevator_pitch: str
    interviewer_hook: str
    demo_script: tuple[str, ...]
    talking_points: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DossierSection:
    label: str
    title: str
    body: str


@dataclass(frozen=True, slots=True)
class ProviderOverlay:
    provider: str
    model: str
    summary: str
    insights: tuple[str, ...]
    sections: tuple[DossierSection, ...]


@dataclass(frozen=True, slots=True)
class DossierResult:
    brief: ProjectBrief
    created_at: datetime
    slug: str
    planner: PlannerResult
    architect: ArchitectResult
    evaluator: EvaluatorResult
    storyteller: StorytellerResult
    markdown: str
    output_dir: str
    markdown_path: str
    json_path: str
    summary_path: str
    provider_status: str = "deterministic"
    provider_message: str = "Deterministic pipeline used."
    provider_overlay: ProviderOverlay | None = None

    def _public_paths(self) -> tuple[str, str, str, str]:
        if not self.output_dir:
            return "", "", "", ""

        output_dir = Path("outputs") / Path(self.output_dir).name
        markdown_path = output_dir / Path(self.markdown_path).name if self.markdown_path else Path()
        json_path = output_dir / Path(self.json_path).name if self.json_path else Path()
        summary_path = output_dir / Path(self.summary_path).name if self.summary_path else Path()
        return (
            output_dir.as_posix(),
            markdown_path.as_posix() if self.markdown_path else "",
            json_path.as_posix() if self.json_path else "",
            summary_path.as_posix() if self.summary_path else "",
        )

    def to_dict(self) -> dict[str, object]:
        output_dir, markdown_path, json_path, summary_path = self._public_paths()
        return {
            "brief": asdict(self.brief),
            "created_at": self.created_at.astimezone(timezone.utc).isoformat(),
            "slug": self.slug,
            "planner": asdict(self.planner),
            "architect": asdict(self.architect),
            "evaluator": asdict(self.evaluator),
            "storyteller": asdict(self.storyteller),
            "markdown": self.markdown,
            "output_dir": output_dir,
            "markdown_path": markdown_path,
            "json_path": json_path,
            "summary_path": summary_path,
            "provider_status": self.provider_status,
            "provider_message": self.provider_message,
            "provider_overlay": asdict(self.provider_overlay) if self.provider_overlay else None,
        }

    def summary_text(self) -> str:
        if self.provider_overlay is not None:
            return self.provider_overlay.summary
        return (
            f"{self.planner.objective} "
            f"Recommendation: {self.evaluator.recommendation}. "
            f"Goal: {self.brief.goal}. "
            f"Preset: {self.brief.preset}. "
            f"Provider: {self.brief.provider}."
        )

    def insights(self) -> tuple[str, ...]:
        base = (
            f"Score: {self.evaluator.overall_score}/100",
            f"Mode: {self.brief.mode}",
            f"Goal: {self.brief.goal}",
            f"Preset: {self.brief.preset}",
            f"Provider: {self.brief.provider} ({self.provider_status})",
        )
        if self.provider_overlay is None:
            return base
        merged = list(self.provider_overlay.insights[:3])
        merged.extend((f"Preset: {self.brief.preset}", f"Provider: {self.brief.provider} ({self.provider_status})"))
        return tuple(merged)

    def sections(self) -> tuple[DossierSection, ...]:
        if self.provider_overlay is not None:
            return self.provider_overlay.sections
        return (
            DossierSection(
                label="Problem",
                title="What this project solves",
                body=self.planner.objective,
            ),
            DossierSection(
                label="Audience",
                title="Who the demo is aimed at",
                body=(
                    f"The dossier is optimized for {self.brief.audience.lower()} review and tuned to "
                    f"show {self.brief.goal.lower()} through a {self.brief.mode.lower()} lens."
                ),
            ),
            DossierSection(
                label="Approach",
                title="How the pipeline works",
                body=self.storyteller.elevator_pitch,
            ),
            DossierSection(
                label="Architecture",
                title="What to build",
                body=self.architect.architecture_summary,
            ),
            DossierSection(
                label="Tradeoffs",
                title="Risks and mitigation",
                body=(
                    f"Top risk: {self.evaluator.risks[0]} "
                    f"Main mitigation: {self.evaluator.mitigations[0]}"
                ),
            ),
            DossierSection(
                label="Interview story",
                title="How to present it",
                body=self.storyteller.interviewer_hook,
            ),
        )

    def to_public_dict(self) -> dict[str, object]:
        _, markdown_path, json_path, summary_path = self._public_paths()
        return {
            "slug": self.slug,
            "title": self.planner.title,
            "summary": self.summary_text(),
            "insights": list(self.insights()),
            "sections": [asdict(section) for section in self.sections()],
            "markdownPath": markdown_path,
            "markdown_path": markdown_path,
            "jsonPath": json_path,
            "json_path": json_path,
            "summaryPath": summary_path,
            "summary_path": summary_path,
            "preset": self.brief.preset,
            "provider": self.brief.provider,
            "providerModel": self.provider_overlay.model if self.provider_overlay else self.brief.provider_model,
            "provider_model": self.provider_overlay.model if self.provider_overlay else self.brief.provider_model,
            "providerStatus": self.provider_status,
            "provider_status": self.provider_status,
            "providerMessage": self.provider_message,
            "provider_message": self.provider_message,
            "dossier": self.to_dict(),
        }
