from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
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
                brief="Build an AI interview coach that scores responses and drafts rehearsal plans.",
                audience="Hiring manager",
                mode="AI assistant",
                goal="Show AI judgment",
            )
        )
        self.assertIn("ai", result.planner.themes)
        self.assertIn("#", result.markdown)
        self.assertEqual(result.markdown_path, "")

    def test_service_persists_markdown_json_and_summary(self) -> None:
        result = self.service.generate(
            ProjectBrief(
                brief="Design an operations copilot that summarizes incidents and suggests follow-up work.",
                audience="Engineering lead",
                mode="Workflow product",
                goal="Show systems thinking",
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
                goal="Show product taste",
            )
        )
        record = self.service.load_record(result.slug)
        self.assertEqual(record["slug"], result.slug)
        self.assertEqual(record["planner"]["title"], result.planner.title)
        self.assertEqual(record["markdown_path"], f"outputs/{result.slug}/dossier.md")

    def test_service_lists_recent_records_with_comparison_metadata(self) -> None:
        result = self.service.generate(
            ProjectBrief(
                brief="Build an AI interview coach that compares multiple dossier runs for a hiring loop.",
                audience="Hiring manager",
                mode="AI assistant",
                goal="Show AI judgment",
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

    def test_service_compares_two_records(self) -> None:
        first = self.service.generate(
            ProjectBrief(
                brief="Build an AI interview coach that scores responses and rehearsal plans.",
                audience="Hiring manager",
                mode="AI assistant",
                goal="Show AI judgment",
                preset="ml",
            )
        )
        second = self.service.generate(
            ProjectBrief(
                brief="Design an operations copilot that summarizes incidents and next steps.",
                audience="Engineering lead",
                mode="Workflow product",
                goal="Show systems thinking",
                preset="full-stack",
            )
        )

        comparison = self.service.compare_records([first.slug, second.slug])
        self.assertEqual(len(comparison["items"]), 2)
        self.assertEqual(comparison["items"][0]["slug"], first.slug)
        self.assertEqual(comparison["items"][1]["slug"], second.slug)
        self.assertIn("summary", comparison)
        self.assertIsInstance(comparison["score_delta"], int)
        self.assertIn(comparison["winner_slug"], {first.slug, second.slug, None})

    def test_service_compare_requires_two_unique_slugs(self) -> None:
        with self.assertRaises(ValueError):
            self.service.compare_records(["only-one"])

    def test_preview_does_not_persist_files(self) -> None:
        result = self.service.preview(
            ProjectBrief(
                brief="Preview an AI product brief before saving it.",
                audience="Hiring manager",
                mode="AI assistant",
                goal="Show AI judgment",
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
                brief="Build a full-stack dossier product with CLI, API, and UI.",
                audience="Engineering lead",
                mode="Developer tool",
                goal="Show systems thinking",
                preset="full-stack",
            )
        )
        payload = self.service.load_public_payload(result.slug)
        self.assertEqual(payload["title"], result.planner.title)
        self.assertEqual(payload["preset"], "full-stack")
        self.assertTrue(payload["persisted"])
        self.assertEqual(len(payload["sections"]), 6)

    def test_openai_provider_falls_back_without_api_key(self) -> None:
        result = self.service.preview(
            ProjectBrief(
                brief="Use OpenAI to refine a dossier.",
                audience="Hiring manager",
                mode="AI assistant",
                goal="Show AI judgment",
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
                                    "summary": "A live OpenAI overlay tightened the public-facing story for this dossier.",
                                    "insights": [
                                        "Lead with the wedge before the feature list.",
                                        "Keep the evaluation story explicit.",
                                        "Anchor the demo around one saved artifact.",
                                    ],
                                    "sections": [
                                        {"label": "Problem", "title": "Problem framing", "body": "The user needs a clearer path from idea to interview artifact."},
                                        {"label": "Audience", "title": "Review target", "body": "The output is aimed at a hiring manager or technical interviewer."},
                                        {"label": "Approach", "title": "How it works", "body": "A deterministic dossier is generated first, then refined for public presentation."},
                                        {"label": "Architecture", "title": "System shape", "body": "The provider overlay sits beside the deterministic pipeline and degrades safely."},
                                        {"label": "Tradeoffs", "title": "What changes", "body": "Live provider output is optional and never blocks the demo path."},
                                        {"label": "Interview story", "title": "How to present it", "body": "Show deterministic output first, then explain the optional live refinement layer."},
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
                        brief="Use OpenAI to refine a dossier.",
                        audience="Hiring manager",
                        mode="AI assistant",
                        goal="Show AI judgment",
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
                "Build an AI coach for interviews and portfolio prep.",
                "--audience",
                "Hiring manager",
                "--mode",
                "AI assistant",
                "--goal",
                "Show AI judgment",
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
                "Preview an ML-oriented dossier without saving it.",
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

    def test_cli_list_reports_empty_output_directory(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "caseforge", "list"],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertTrue(result.stdout.strip() in {"No dossiers found.", ""} or "\t" in result.stdout)


if __name__ == "__main__":
    unittest.main()
