from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from caseforge.models import ProjectBrief
from caseforge.pipeline import DossierPipeline
from caseforge.service import DossierService


class FakeHTTPResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class CaseForgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_root = Path(self.temp_dir.name)
        self.service = DossierService(output_root=self.output_root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_pipeline_produces_ai_themes_and_markdown(self) -> None:
        result = DossierPipeline().run(
            ProjectBrief(
                brief="Build an AI operations copilot that scores incidents and drafts follow-up plans.",
                audience="Technical stakeholders",
                mode="AI assistant",
                goal="Emphasize AI decisioning",
            )
        )
        self.assertIn("ai", result.planner.themes)
        self.assertIn("#", result.markdown)
        self.assertEqual(result.markdown_path, "")

    def test_pipeline_architecture_targets_submitted_product_not_caseforge_internals(self) -> None:
        result = DossierPipeline().run(
            ProjectBrief(
                brief="Build an AI operations copilot that turns incident notes, service metrics, and follow-up tasks into a release-ready action plan.",
                audience="Engineering lead",
                mode="Workflow product",
                goal="Drive implementation clarity",
                preset="full-stack",
            )
        )
        modules = set(result.architect.modules)
        forbidden_modules = {"brief parser", "planner", "architect", "evaluator", "storyteller", "markdown renderer"}
        self.assertEqual(result.planner.title, "AI Operations Copilot")
        self.assertTrue({"workflow engine", "review dashboard", "provider boundary"}.issubset(modules))
        self.assertFalse(modules.intersection(forbidden_modules))
        self.assertIn("intake", result.architect.api_surface[0])
        self.assertIn("review", " ".join(result.storyteller.talking_points).lower())

    def test_pipeline_infers_human_readable_product_title(self) -> None:
        result = DossierPipeline().run(
            ProjectBrief(
                brief="Build a release readiness planner that turns incident notes, service metrics, and owner comments into an action plan with risks, owners, checks, and next steps.",
                preset="full-stack",
            )
        )
        self.assertEqual(result.planner.title, "Release Readiness Planner")
        self.assertIn("release, readiness, planner", result.planner.objective)

    def test_service_persists_markdown_json_and_summary(self) -> None:
        result = self.service.generate(
            ProjectBrief(
                brief="Design an operations copilot that summarizes incidents and suggests follow-up work.",
                audience="Engineering lead",
                mode="Workflow product",
                goal="Drive implementation clarity",
                preset="full-stack",
            )
        )
        self.assertTrue(Path(result.markdown_path).exists())
        self.assertTrue(Path(result.json_path).exists())
        self.assertTrue(Path(result.summary_path).exists())

        payload = self.service.to_public_payload(result)
        self.assertEqual(payload["title"], result.planner.title)
        self.assertEqual(payload["markdownPath"], f"outputs/{result.slug}/dossier.md")
        self.assertEqual(payload["jsonPath"], f"outputs/{result.slug}/dossier.json")
        self.assertEqual(payload["summaryPath"], f"outputs/{result.slug}/summary.txt")
        self.assertEqual(len(payload["sections"]), 6)
        self.assertEqual(payload["preset"], "full-stack")

    def test_service_loads_record(self) -> None:
        result = self.service.generate(
            ProjectBrief(
                brief="Create a study planner that turns notes into revision plans and quizzes.",
                audience="Internal team",
                mode="Study companion",
                goal="Strengthen product framing",
            )
        )
        record = self.service.load_record(result.slug)
        self.assertEqual(record["slug"], result.slug)
        self.assertEqual(record["planner"]["title"], result.planner.title)
        self.assertEqual(record["markdown_path"], f"outputs/{result.slug}/dossier.md")

    def test_service_rejects_unsafe_record_slug(self) -> None:
        with self.assertRaises(ValueError):
            self.service.load_record("../README")

    def test_service_lists_recent_records_with_comparison_metadata(self) -> None:
        result = self.service.generate(
            ProjectBrief(
                brief="Build an AI operations copilot that compares multiple blueprint runs for a release review.",
                audience="Technical stakeholders",
                mode="AI assistant",
                goal="Emphasize AI decisioning",
                preset="ml",
            )
        )
        items = self.service.list_records(limit=5)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["slug"], result.slug)
        self.assertEqual(items[0]["preset"], "ml")
        self.assertEqual(items[0]["provider"], "deterministic")
        self.assertIn("/100", items[0]["score"])
        self.assertTrue(items[0]["summary"])
        self.assertIn("Recommendation:", items[0]["summary"])
        self.assertIn("Preset:", items[0]["summary"])

    def test_service_lists_records_by_created_at_not_slug_order(self) -> None:
        pipeline = DossierPipeline()
        older = self.service.storage.persist(
            pipeline.run(
                ProjectBrief(
                    brief="Build Zeta ops planner.",
                    audience="Technical stakeholders",
                    mode="Workflow product",
                    goal="Drive implementation clarity",
                ),
                created_at=datetime(2026, 4, 24, 9, 0, tzinfo=timezone.utc),
            )
        )
        newer = self.service.storage.persist(
            pipeline.run(
                ProjectBrief(
                    brief="Build Alpha ops planner.",
                    audience="Technical stakeholders",
                    mode="Workflow product",
                    goal="Drive implementation clarity",
                ),
                created_at=datetime(2026, 4, 25, 9, 0, tzinfo=timezone.utc),
            )
        )

        items = self.service.list_records(limit=5)
        self.assertEqual([items[0]["slug"], items[1]["slug"]], [newer.slug, older.slug])

    def test_service_compares_two_records(self) -> None:
        first = self.service.generate(
            ProjectBrief(
                brief="Build an AI operations copilot that scores incidents and follow-up plans.",
                audience="Technical stakeholders",
                mode="AI assistant",
                goal="Emphasize AI decisioning",
                preset="ml",
            )
        )
        second = self.service.generate(
            ProjectBrief(
                brief="Design an operations copilot that summarizes incidents and next steps.",
                audience="Engineering lead",
                mode="Workflow product",
                goal="Drive implementation clarity",
                preset="full-stack",
            )
        )

        comparison = self.service.compare_records([first.slug, second.slug])
        self.assertEqual(len(comparison["items"]), 2)
        self.assertEqual(comparison["items"][0]["slug"], first.slug)
        self.assertEqual(comparison["items"][1]["slug"], second.slug)
        self.assertIn("summary", comparison)
        self.assertIn("decision_note", comparison)
        self.assertIsInstance(comparison["decision_note"], str)
        self.assertGreater(len(comparison["decision_note"]), 40)
        self.assertIsInstance(comparison["score_delta"], int)
        self.assertIn(comparison["winner_slug"], {first.slug, second.slug, None})

    def test_service_compare_requires_two_unique_slugs(self) -> None:
        with self.assertRaises(ValueError):
            self.service.compare_records(["only-one"])

    def test_preview_does_not_persist_files(self) -> None:
        result = self.service.preview(
            ProjectBrief(
                brief="Preview an AI product brief before saving it.",
                audience="Technical stakeholders",
                mode="AI assistant",
                goal="Emphasize AI decisioning",
                preset="ml",
            )
        )
        self.assertEqual(result.markdown_path, "")
        self.assertEqual(self.service.list_records(), [])

        payload = self.service.preview_public_payload(result)
        self.assertTrue(payload["preview"])
        self.assertFalse(payload["persisted"])
        self.assertEqual(payload["preset"], "ml")

    def test_service_loads_public_payload_for_saved_record(self) -> None:
        result = self.service.generate(
            ProjectBrief(
                brief="Build a full-stack blueprint product with CLI, API, and UI.",
                audience="Engineering lead",
                mode="Developer tool",
                goal="Drive implementation clarity",
                preset="full-stack",
            )
        )
        payload = self.service.load_public_payload(result.slug)
        self.assertEqual(payload["title"], result.planner.title)
        self.assertEqual(payload["preset"], "full-stack")
        self.assertTrue(payload["persisted"])
        self.assertEqual(len(payload["sections"]), 6)
        self.assertEqual(payload["summary"], self.service.to_public_payload(result)["summary"])

    def test_openai_provider_falls_back_without_api_key(self) -> None:
        result = self.service.preview(
            ProjectBrief(
                brief="Use OpenAI to refine a blueprint.",
                audience="Technical stakeholders",
                mode="AI assistant",
                goal="Emphasize AI decisioning",
                preset="ml",
                provider="openai",
            )
        )
        self.assertEqual(result.provider_status, "fallback")
        self.assertIn("OPENAI_API_KEY", result.provider_message)
        self.assertIsNone(result.provider_overlay)

    def test_openai_provider_applies_mocked_overlay(self) -> None:
        fake_payload = {
            "output": [
                {
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(
                                {
                                    "summary": "A live OpenAI overlay tightened the public-facing story for this blueprint.",
                                    "insights": [
                                        "Lead with the wedge before the feature list.",
                                        "Keep the evaluation logic explicit.",
                                        "Anchor the review around one saved artifact.",
                                    ],
                                    "sections": [
                                        {"label": "Problem", "title": "Problem framing", "body": "The user needs a clearer path from idea to implementation artifact."},
                                        {"label": "Audience", "title": "Review target", "body": "The output is aimed at technical stakeholders."},
                                        {"label": "Approach", "title": "How it works", "body": "A deterministic blueprint is generated first, then refined for public presentation."},
                                        {"label": "Architecture", "title": "System shape", "body": "The provider overlay sits beside the deterministic pipeline and degrades safely."},
                                        {"label": "Tradeoffs", "title": "What changes", "body": "Live provider output is optional and never blocks the deterministic path."},
                                        {"label": "Delivery story", "title": "How to move it forward", "body": "Review deterministic output first, then explain the optional live refinement layer."},
                                    ],
                                }
                            ),
                        }
                    ]
                }
            ]
        }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-5-mini"}, clear=False):
            with patch("caseforge.providers.urlopen", return_value=FakeHTTPResponse(fake_payload)):
                result = self.service.preview(
                    ProjectBrief(
                        brief="Use OpenAI to refine a blueprint.",
                        audience="Technical stakeholders",
                        mode="AI assistant",
                        goal="Emphasize AI decisioning",
                        preset="ml",
                        provider="openai",
                    )
                )

        self.assertEqual(result.provider_status, "live")
        self.assertIsNotNone(result.provider_overlay)
        self.assertEqual(result.provider_overlay.model, "gpt-5-mini")
        self.assertIn("OpenAI overlay", result.summary_text())
        self.assertEqual(len(result.sections()), 6)

    def test_cli_create_emits_json_payload(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "caseforge",
                "create",
                "Build an AI operations copilot for release planning.",
                "--audience",
                "Technical stakeholders",
                "--mode",
                "AI assistant",
                "--goal",
                "Emphasize AI decisioning",
                "--preset",
                "ml",
                "--json",
            ],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertIn("title", payload)
        self.assertIn("summary", payload)
        self.assertIn("markdownPath", payload)
        self.assertEqual(payload["preset"], "ml")

    def test_cli_preview_emits_non_persisted_payload(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "caseforge",
                "create",
                "Preview an ML-oriented blueprint without saving it.",
                "--preset",
                "ml",
                "--preview",
                "--json",
            ],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["preview"])
        self.assertFalse(payload["persisted"])

    def test_service_load_public_payload_normalizes_legacy_interviewer_hook(self) -> None:
        legacy_slug = "legacy-blueprint"
        legacy_dir = self.output_root / legacy_slug
        legacy_dir.mkdir(parents=True, exist_ok=True)
        (legacy_dir / "dossier.json").write_text(
            json.dumps(
                {
                    "slug": legacy_slug,
                    "brief": {
                        "audience": "Technical stakeholders",
                        "goal": "Drive implementation clarity",
                        "mode": "AI assistant",
                        "preset": "general",
                        "provider": "deterministic",
                    },
                    "planner": {
                        "title": "Legacy Blueprint",
                        "objective": "Legacy objective",
                    },
                    "architect": {
                        "architecture_summary": "Legacy architecture summary",
                    },
                    "evaluator": {
                        "overall_score": 81,
                        "recommendation": "ship",
                        "risks": ["Legacy risk"],
                        "mitigations": ["Legacy mitigation"],
                    },
                    "storyteller": {
                        "elevator_pitch": "Legacy pitch",
                        "interviewer_hook": "Legacy delivery hook",
                    },
                    "markdown_path": f"outputs/{legacy_slug}/dossier.md",
                    "json_path": f"outputs/{legacy_slug}/dossier.json",
                    "summary_path": f"outputs/{legacy_slug}/summary.txt",
                    "provider_status": "deterministic",
                    "provider_message": "Deterministic pipeline used.",
                }
            ),
            encoding="utf-8",
        )

        record = self.service.load_record(legacy_slug)
        payload = self.service.load_public_payload(legacy_slug)
        self.assertEqual(record["storyteller"]["delivery_hook"], "Legacy delivery hook")
        self.assertEqual(payload["sections"][-1]["body"], "Legacy delivery hook")

    def test_cli_list_reports_empty_output_directory(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "caseforge", "list"],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertTrue(result.stdout.strip() in {"No blueprints found.", ""} or "\t" in result.stdout)

    def test_web_ui_exposes_reviewer_workspace_contract(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        index_html = (project_root / "caseforge" / "web" / "index.html").read_text(encoding="utf-8")
        app_js = (project_root / "caseforge" / "web" / "app.js").read_text(encoding="utf-8")
        readme = (project_root / "README.md").read_text(encoding="utf-8")

        self.assertIn('id="alert-panel"', index_html)
        self.assertIn('id="export-json-path"', index_html)
        self.assertIn('id="open-markdown-link"', index_html)
        self.assertIn('class="workflow-strip"', index_html)
        self.assertIn("function setAlert", app_js)
        self.assertIn("exportJsonPath.textContent", app_js)
        self.assertIn("caseforge:formState", app_js)
        self.assertIn("release-planner", app_js)
        self.assertIn("compare-decision", app_js)
        self.assertIn("decision_note", app_js)
        self.assertIn("Local Product Walkthrough", readme)
        self.assertNotIn("## Feature Set", readme)


if __name__ == "__main__":
    unittest.main()
