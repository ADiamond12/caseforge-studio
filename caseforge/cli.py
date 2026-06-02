from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import ProjectBrief
from .server import run_server
from .service import DossierService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="caseforge",
        description="Generate implementation-ready project blueprints from rough ideas.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="generate a project blueprint from a brief")
    create_parser.add_argument("brief", nargs="?", help="raw project brief text")
    create_parser.add_argument("--brief-file", help="path to a markdown or text brief")
    create_parser.add_argument("--title")
    create_parser.add_argument("--audience", default="Technical stakeholders")
    create_parser.add_argument("--mode", default="AI assistant")
    create_parser.add_argument("--goal", default="Drive implementation clarity")
    create_parser.add_argument(
        "--preset",
        default="general",
        choices=["general", "product", "ml", "full-stack", "founder"],
        help="evaluation preset for the generated blueprint",
    )
    create_parser.add_argument(
        "--provider",
        default="deterministic",
        choices=["deterministic", "openai"],
        help="generation provider; deterministic is the default safe local path",
    )
    create_parser.add_argument("--provider-model", help="optional live provider model override")
    create_parser.add_argument("--preview", action="store_true", help="generate a blueprint without saving it")
    create_parser.add_argument("--json", action="store_true", help="print the public JSON payload")

    serve_parser = subparsers.add_parser("serve", help="run the local web app")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8127)

    show_parser = subparsers.add_parser("show", help="open a persisted blueprint record by slug")
    show_parser.add_argument("slug")

    list_parser = subparsers.add_parser("list", help="list recent blueprints")
    list_parser.add_argument("--limit", type=int, default=10)

    compare_parser = subparsers.add_parser("compare", help="compare two persisted blueprint records")
    compare_parser.add_argument("slugs", nargs=2)
    compare_parser.add_argument("--json", action="store_true", help="print comparison as JSON")
    compare_parser.add_argument("--markdown", action="store_true", help="print comparison as Markdown")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = DossierService()

    if args.command == "create":
        brief_text = _resolve_brief_text(args.brief, args.brief_file, parser)
        brief = ProjectBrief(
            brief=brief_text,
            title=args.title,
            audience=args.audience,
            mode=args.mode,
            goal=args.goal,
            preset=args.preset,
            provider=args.provider,
            provider_model=args.provider_model,
        )
        result = service.preview(brief) if args.preview else service.generate(brief)
        if args.json:
            payload = service.preview_public_payload(result) if args.preview else service.to_public_payload(result)
            print(json.dumps(payload, indent=2))
            return 0

        print(f"Title: {result.planner.title}")
        print(f"Slug: {result.slug}")
        print(f"Score: {result.evaluator.overall_score}/100")
        print(f"Provider: {result.brief.provider} ({result.provider_status})")
        print(f"Provider message: {result.provider_message}")
        if args.preview:
            print("Preview: not persisted")
        else:
            print(f"Markdown: {result.markdown_path}")
            print(f"JSON: {result.json_path}")
            print(f"Summary: {result.summary_path}")
        print("")
        print(result.markdown)
        return 0

    if args.command == "serve":
        return run_server(host=args.host, port=args.port)

    if args.command == "show":
        print(json.dumps(service.load_record(args.slug), indent=2))
        return 0

    if args.command == "list":
        records = service.list_records(limit=args.limit)
        if not records:
            print("No blueprints found.")
            return 0
        for record in records:
            print(f"{record['slug']}\t{record['title']}\t{record['score']}")
        return 0

    if args.command == "compare":
        comparison = service.compare_records(list(args.slugs))
        if args.json:
            print(json.dumps(comparison, indent=2))
            return 0
        if args.markdown:
            print(service.comparison_markdown(comparison))
            return 0
        print(comparison["summary"])
        print(f"Decision note: {comparison['decision_note']}")
        for item in comparison["items"]:
            print(
                f"- {item['slug']}: {item['score']} | {item['preset']} | "
                f"{item['provider_status']} | risk: {item['top_risk']}"
            )
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def _resolve_brief_text(
    inline_brief: str | None,
    brief_file: str | None,
    parser: argparse.ArgumentParser,
) -> str:
    if inline_brief:
        return inline_brief.strip()
    if brief_file:
        return Path(brief_file).read_text(encoding="utf-8").strip()
    parser.error("provide either a brief argument or --brief-file")
    return ""
