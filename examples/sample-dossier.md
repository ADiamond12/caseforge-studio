# AI Interview Coach

## Snapshot
- Created: 2026-04-10T02:12:54.913850+03:00
- Audience: Hiring manager
- Mode: AI assistant
- Goal: Show AI judgment
- Preset: general
- Provider: deterministic
- Provider status: deterministic
- Score: 96/100

## Provider Notes
Deterministic pipeline used.

## Brief
# AI Interview Coach

Build an AI interview coach that turns a job description, resume, and selected portfolio projects into a rehearsal plan with mock questions, STAR prompts, confidence scoring, and a two-minute project walkthrough.

## Planner
- Objective: Build AI Interview Coach for hiring manager review, focused on ai outcomes and anchored in ai, coach, interview.
- Themes: ai, learning

### Assumptions
- The target audience is Hiring manager reviewers or stakeholders.
- The project should be easy to demo without external infrastructure.
- The project should explain its AI layer clearly instead of hiding it.

### Success Metrics
- A clear end-to-end story from input brief to exported dossier.
- A deterministic output that repeats for the same brief.
- A polished interview narrative with concrete talking points.
- A visible multi-agent breakdown that is simple to explain in an interview.

### Scope
- Brief intake and normalization
- Four-stage deterministic pipeline
- Markdown dossier export
- Local file persistence
- JSON API for external integration

### Delivery Plan
- Define the brief and expected audience
- Run the planner stage
- Shape the architecture and execution plan
- Score the project for interview readiness
- Package the dossier and persist the output
- Present the agent breakdown as an explainable AI workflow
- Use the success metrics as the final demo checklist

## Architecture
AI Interview Coach uses a deterministic ai, learning pipeline to produce a dossier that explains both what to build and why it is interview-worthy. Build AI Interview Coach for hiring manager review, focused on ai outcomes and anchored in ai, coach, interview.

### Modules
- agent orchestrator
- brief parser
- planner
- architect
- evaluator
- storyteller
- markdown renderer
- storage layer

### Data Flow
- Brief -> normalized input -> planner -> architect -> evaluator -> storyteller -> dossier export
- Generated dossier -> filesystem persistence -> API response
- Agent outputs stay deterministic and inspectable at every stage.

### API Surface
- POST /api/dossiers
- POST /api/dossiers/preview
- GET /api/dossiers
- GET /api/dossiers/{slug}
- GET /health

### Persistence
- Create one output folder per generated dossier
- Store markdown and JSON side by side
- Keep a summary text file for quick CLI inspection
- Preserve stage-level metadata for explainability

### Implementation Notes
- Use only the Python standard library so the project is easy to run anywhere.
- Keep the pipeline deterministic so interview demos do not depend on external services.
- The scope is intentionally broad enough to demonstrate product judgment.
- Stage names mirror a multi-agent system to make the architecture legible.

## Evaluation
Recommendation: ship with general framing

### Strengths
- Clear product framing for an interviewer.
- Strong separation between planning, architecture, scoring, and storytelling.
- Markdown output is immediately shareable.
- The agent labels make the workflow feel AI-native without hiding the logic.
- The module breakdown suggests a maintainable implementation plan.

### Risks
- The brief may be too broad to implement fully in one iteration.
- The project could drift into generic portfolio territory if the demo is not concrete.

### Mitigations
- Cap the MVP to the dossier generator, export path, and one clean demo flow.
- Lead with the deterministic multi-agent workflow and the polished narrative output.
- Show the stage boundaries to make the AI story feel credible and inspectable.

## Interview Pitch
AI Interview Coach turns a rough brief into a structured build plan, architecture outline, and interview narrative for hiring manager review.

Hook: This brief already has enough structure for a strong interview demo: AI Interview Coach can ship as a polished, explainable AI workflow.

### Demo Script
- Paste a brief into the CLI or API.
- Show the generated dossier sections and the scored recommendations.
- Export the markdown bundle and point to the persistence path.
- Explain how the deterministic pipeline keeps outputs explainable and reproducible.

### Talking Points
- Deterministic AI-style orchestration without external model calls.
- Small, testable stages with clean boundaries.
- Markdown-first output that is easy to review in an interview.
- HTTP API and CLI share the same core service layer.
