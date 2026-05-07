from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .markdown import render_markdown
from .models import (
    ArchitectResult,
    DossierResult,
    EvaluatorResult,
    PlannerResult,
    ProjectBrief,
    StorytellerResult,
)
from .utils import choose_best_title, significant_tokens, slugify, tokenize


DOMAIN_MAP: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ai", ("ai", "agent", "llm", "model", "prompt", "copilot", "rag", "embeddings")),
    ("product", ("dashboard", "workflow", "platform", "tool", "portal", "product", "system")),
    ("backend", ("api", "service", "server", "queue", "db", "database", "pipeline")),
    ("frontend", ("ui", "ux", "web", "visual", "interface", "dashboard", "frontend")),
    ("data", ("data", "analytics", "report", "insight", "metrics", "lake", "warehouse")),
    ("automation", ("automate", "automation", "scheduler", "workflow", "ops", "task")),
    ("learning", ("study", "education", "course", "learn", "practice", "tutor")),
)

PRESET_BONUS: dict[str, int] = {
    "general": 0,
    "product": 2,
    "ml": 3,
    "full-stack": 3,
    "founder": 2,
}


@dataclass(frozen=True, slots=True)
class DossierPipeline:
    def run(self, brief: ProjectBrief, *, created_at: datetime | None = None) -> DossierResult:
        created_at = created_at or datetime.now(timezone.utc)
        planner = self._plan(brief)
        architect = self._architect(brief, planner)
        evaluator = self._evaluate(brief, planner, architect)
        storyteller = self._storytell(planner, evaluator)
        slug = slugify(planner.title)
        markdown = render_markdown(brief, planner, architect, evaluator, storyteller, created_at=created_at)
        return DossierResult(
            brief=brief,
            created_at=created_at,
            slug=slug,
            planner=planner,
            architect=architect,
            evaluator=evaluator,
            storyteller=storyteller,
            markdown=markdown,
            output_dir="",
            markdown_path="",
            json_path="",
            summary_path="",
        )

    def _plan(self, brief: ProjectBrief) -> PlannerResult:
        title = choose_best_title(brief.brief, brief.title)
        tokens = significant_tokens(brief.brief, limit=8)
        themes = self._themes_for_tokens(tokens)
        objective = self._objective(title, tokens, themes, brief.audience)
        assumptions = self._assumptions(tokens, brief.audience)
        success_metrics = self._success_metrics(tokens, themes)
        scope = self._scope(tokens, themes)
        delivery_plan = self._delivery_plan(themes, success_metrics)
        return PlannerResult(
            title=title,
            objective=objective,
            audience=brief.audience,
            themes=themes,
            assumptions=assumptions,
            success_metrics=success_metrics,
            scope=scope,
            delivery_plan=delivery_plan,
        )

    def _architect(self, brief: ProjectBrief, planner: PlannerResult) -> ArchitectResult:
        modules = self._module_plan(planner.themes, brief.brief)
        data_flow = self._data_flow(planner.themes)
        api_surface = self._api_surface(planner.themes)
        persistence = self._persistence_plan(planner.themes)
        architecture_summary = self._architecture_summary(planner.title, planner.objective, planner.themes)
        implementation_notes = self._implementation_notes(planner.themes, planner.scope)
        return ArchitectResult(
            architecture_summary=architecture_summary,
            modules=modules,
            data_flow=data_flow,
            api_surface=api_surface,
            persistence_plan=persistence,
            implementation_notes=implementation_notes,
        )

    def _evaluate(self, brief: ProjectBrief, planner: PlannerResult, architect: ArchitectResult) -> EvaluatorResult:
        score = 68
        score += 8 if "ai" in planner.themes else 0
        score += 6 if len(planner.scope) >= 4 else 0
        score += 4 if len(architect.modules) >= 5 else 0
        score += min(10, len(significant_tokens(brief.brief, limit=12)))
        score += PRESET_BONUS.get(brief.preset, 0)
        score = min(score, 100)
        strengths = self._strengths(planner, architect, brief)
        risks = self._risks(planner, brief)
        mitigations = self._mitigations(risks, planner, brief)
        recommendation = self._recommendation(score, brief.preset)
        return EvaluatorResult(
            overall_score=score,
            strengths=strengths,
            risks=risks,
            mitigations=mitigations,
            recommendation=recommendation,
        )

    def _storytell(self, planner: PlannerResult, evaluator: EvaluatorResult) -> StorytellerResult:
        hook = self._hook(planner, evaluator)
        pitch = (
            f"{planner.title} turns a rough brief into a structured build plan, architecture outline, "
            f"and implementation blueprint for {planner.audience.lower()}."
        )
        demo_script = (
            "Start from a brief in the CLI or API.",
            "Review the generated blueprint sections and scored recommendations.",
            "Export the markdown bundle and note the persistence path.",
            "Explain how the deterministic pipeline keeps outputs explainable and reproducible.",
        )
        first_talking_point = (
            "Deterministic staged planning without external model calls."
            if "ai" not in planner.themes
            else "Deterministic AI-style orchestration without external model calls."
        )
        talking_points = (
            first_talking_point,
            "Small, testable stages with clean boundaries.",
            "Markdown-first output that is easy to review during planning or implementation.",
            "HTTP API and CLI share the same core service layer.",
        )
        return StorytellerResult(
            elevator_pitch=pitch,
            delivery_hook=hook,
            demo_script=demo_script,
            talking_points=talking_points,
        )

    def _themes_for_tokens(self, tokens: tuple[str, ...]) -> tuple[str, ...]:
        themes: list[str] = []
        token_set = set(tokens)
        for theme, keywords in DOMAIN_MAP:
            if token_set.intersection(keywords):
                themes.append(theme)
        if "ai" not in themes and token_set.intersection({"agent", "llm", "model", "prompt"}):
            themes.insert(0, "ai")
        if not themes:
            themes.append("product")
        return tuple(dict.fromkeys(themes))

    def _objective(self, title: str, tokens: tuple[str, ...], themes: tuple[str, ...], audience: str) -> str:
        lead_theme = themes[0] if themes else "product"
        token_phrase = ", ".join(tokens[:3]) if tokens else "the submitted brief"
        return (
            f"Turn {title} into a plan {audience.lower()} can review quickly, with emphasis on "
            f"{lead_theme} decisions and the concrete inputs: {token_phrase}."
        )

    def _assumptions(self, tokens: tuple[str, ...], audience: str) -> tuple[str, ...]:
        assumptions = [
            f"The intended audience is {audience}.",
            "The project should be easy to validate without external infrastructure.",
        ]
        if "ai" in tokens or "agent" in tokens:
            assumptions.append("The project should explain its AI layer clearly instead of hiding it.")
        else:
            assumptions.append("The project should still feel modern and automation-forward.")
        return tuple(assumptions)

    def _success_metrics(self, tokens: tuple[str, ...], themes: tuple[str, ...]) -> tuple[str, ...]:
        metrics = [
            "A clear end-to-end path from input brief to exported blueprint.",
            "A deterministic output that repeats for the same brief.",
            "A practical implementation narrative with concrete delivery checkpoints.",
        ]
        if "ai" in themes:
            metrics.append("A visible multi-stage breakdown that is simple to audit and extend.")
        if "data" in tokens:
            metrics.append("A structured report that makes the project feel measurable and rigorous.")
        return tuple(metrics)

    def _scope(self, tokens: tuple[str, ...], themes: tuple[str, ...]) -> tuple[str, ...]:
        scope = [
            "Brief intake and normalization",
            "Four-stage deterministic pipeline",
            "Markdown blueprint export",
            "Local file persistence",
            "JSON API for external integration",
        ]
        if "ui" in tokens or "frontend" in themes:
            scope.append("Optional web front-end integration")
        return tuple(scope)

    def _delivery_plan(self, themes: tuple[str, ...], success_metrics: tuple[str, ...]) -> tuple[str, ...]:
        steps = [
            "Define the brief and expected audience",
            "Run the planner stage",
            "Shape the architecture and execution plan",
            "Score the project for implementation readiness",
            "Package the blueprint and persist the output",
        ]
        if "ai" in themes:
            steps.append("Present the agent breakdown as an explainable AI workflow")
        if success_metrics:
            steps.append("Use the success metrics as the final validation checklist")
        return tuple(steps)

    def _module_plan(self, themes: tuple[str, ...], brief_text: str) -> tuple[str, ...]:
        modules = ["brief parser", "planner", "architect", "evaluator", "storyteller", "markdown renderer", "storage layer"]
        if "ai" in themes:
            modules.insert(0, "agent orchestrator")
        tokens = tokenize(brief_text)
        if "api" in tokens or "web" in tokens:
            modules.append("http api")
        return tuple(dict.fromkeys(modules))

    def _data_flow(self, themes: tuple[str, ...]) -> tuple[str, ...]:
        flow = (
            "Brief -> normalized input -> planner -> architect -> evaluator -> storyteller -> blueprint export",
            "Generated blueprint -> filesystem persistence -> API response",
        )
        if "ai" in themes:
            flow = flow + ("Agent outputs stay deterministic and inspectable at every stage.",)
        return flow

    def _api_surface(self, themes: tuple[str, ...]) -> tuple[str, ...]:
        api = (
            "POST /api/dossiers",
            "POST /api/dossiers/preview",
            "GET /api/dossiers",
            "GET /api/dossiers/compare",
            "GET /api/dossiers/{slug}",
            "GET /health",
        )
        return api

    def _persistence_plan(self, themes: tuple[str, ...]) -> tuple[str, ...]:
        plan = (
            "Create one output folder per generated blueprint",
            "Store markdown and JSON side by side",
            "Keep a summary text file for quick CLI inspection",
        )
        if "ai" in themes:
            plan = plan + ("Preserve stage-level metadata for explainability",)
        return plan

    def _implementation_notes(self, themes: tuple[str, ...], scope: tuple[str, ...]) -> tuple[str, ...]:
        notes = (
            "Use only the Python standard library so the project is easy to run anywhere.",
            "Keep the pipeline deterministic so validation and planning do not depend on external services.",
        )
        if len(scope) >= 4:
            notes = notes + ("The scope is intentionally broad enough to reflect product judgment.",)
        if "ai" in themes:
            notes = notes + ("Stage names mirror a multi-agent system to make the architecture legible.",)
        return notes

    def _architecture_summary(self, title: str, objective: str, themes: tuple[str, ...]) -> str:
        theme_phrase = ", ".join(themes)
        return (
            f"{title} routes one brief through planning, architecture, evaluation, and delivery notes. "
            f"The deterministic {theme_phrase} pipeline makes the recommendation repeatable and easy to challenge in review."
        )

    def _strengths(self, planner: PlannerResult, architect: ArchitectResult, brief: ProjectBrief) -> tuple[str, ...]:
        strengths = [
            "The output separates product framing, architecture, scoring, and delivery notes.",
            "The markdown export gives reviewers one artifact to inspect or hand off.",
            "The deterministic path makes repeated runs comparable.",
        ]
        if "ai" in planner.themes:
            strengths.append("The AI-facing labels are backed by visible deterministic stages.")
        if len(architect.modules) >= 6:
            strengths.append("The module breakdown suggests a maintainable implementation plan.")
        if brief.preset == "product":
            strengths.append("The product preset emphasizes user value and delivery clarity.")
        if brief.preset == "ml":
            strengths.append("The ML preset pushes the output toward evaluation and model judgment.")
        if brief.preset == "full-stack":
            strengths.append("The full-stack preset rewards balanced API, UI, and persistence coverage.")
        if brief.preset == "founder":
            strengths.append("The founder preset strengthens outcome framing and differentiation.")
        return tuple(strengths)

    def _risks(self, planner: PlannerResult, brief: ProjectBrief) -> tuple[str, ...]:
        risks = [
            "The brief may be too broad to implement fully in one iteration.",
            "The project could drift into generic planning output if the implementation path is not concrete.",
        ]
        if len(tokenize(brief.brief)) < 6:
            risks.append("The input brief is very short, so the generated output may need extra assumptions.")
        if "ai" not in planner.themes:
            risks.append("Without an explicit automation or AI angle, the project may sound less differentiated.")
        if brief.preset == "ml":
            risks.append("The ML preset raises expectations for evaluation rigor and dataset realism.")
        if brief.preset == "full-stack":
            risks.append("The full-stack preset raises expectations for end-to-end polish across backend and UI.")
        if brief.preset == "founder":
            risks.append("The founder preset raises expectations for market clarity and differentiation.")
        return tuple(risks)

    def _mitigations(self, risks: tuple[str, ...], planner: PlannerResult, brief: ProjectBrief) -> tuple[str, ...]:
        mitigations: list[str] = []
        for risk in risks:
            if "broad" in risk:
                mitigations.append("Cap the MVP to the blueprint generator, export path, and one clean first-run flow.")
            elif "generic" in risk:
                mitigations.append("Use a specific brief and review the stage output instead of relying on broad product claims.")
            elif "short" in risk:
                mitigations.append("Use the assumptions section to state the missing context explicitly.")
            else:
                mitigations.append("Anchor the walkthrough in the planner, architect, evaluator, and storyteller stages.")
        if "ai" in planner.themes:
            mitigations.append("Make the stage boundaries explicit so the AI workflow stays credible and inspectable.")
        if brief.preset == "ml":
            mitigations.append("Document evaluation assumptions and keep model claims intentionally conservative.")
        if brief.preset == "full-stack":
            mitigations.append("Walk through the CLI, API, and UI in one pass so the system feels integrated.")
        if brief.preset == "founder":
            mitigations.append("Lead with user pain, wedge, and why the first release is strategically narrow.")
        return tuple(dict.fromkeys(mitigations))

    def _recommendation(self, score: int, preset: str) -> str:
        if score >= 90:
            return f"ship with {preset} framing"
        if score >= 78:
            return "ship"
        return "tighten scope before pitching"

    def _hook(self, planner: PlannerResult, evaluator: EvaluatorResult) -> str:
        if evaluator.overall_score >= 85:
            return f"{planner.title} has enough detail to produce a reviewable first implementation plan."
        if "ai" in planner.themes:
            return f"The useful hook is the visible staged workflow: {planner.title} turns a brief into a scoring-backed build plan."
        return f"The hook is the clean product story: {planner.title} turns ambiguity into a concrete, reviewable build blueprint."
