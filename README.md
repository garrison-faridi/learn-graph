# learn-graph

An adaptive learning skill for AI agents. Feed it **any PDF** — a textbook, a technical spec, a research paper, company documentation, a certification guide — and it builds a structured knowledge vault, then tests your understanding with adaptive quizzing and AI-evaluated free-response sessions.

```
/tutor my-document.pdf
  → extracts and structures the content into a StudyVault
  → asks: Multiple Choice, Free Response, or Guided Reading?
  → teaches, quizzes, grades — tracks every concept, gap, and false friend across sessions
```

---

## Use Cases

This isn't just for school. Any dense material you need to actually *learn* — not just read — is a candidate:

- **Textbooks & coursework** — Biology, CS, economics, whatever. Build a vault, quiz yourself, track mastery across chapters.
- **Technical documentation** — AWS docs, API references, framework guides. Turn passive reading into active recall.
- **Research papers** — Break down a dense paper into concept nodes. Test yourself on methodology, findings, and implications.
- **Professional certifications** — PMP, AWS Solutions Architect, CFA. Structured study with adaptive difficulty.
- **Company knowledge bases** — Onboarding docs, product specs, internal wikis. Learn the material, not just skim it.
- **Codebases** — Point it at a repo and it builds a vault from the source code architecture (see Codebase Mode below).
- **Any PDF you want to deeply understand** — If it has concepts worth retaining, this tool will help you retain them.

---

## Framework Compatibility

This skill is framework-agnostic. The core is just markdown files (StudyVault) and prompting patterns (SKILL.md + reference docs). Any AI agent that can read files and follow skill instructions can run it.

**Tested with:**
- **Vellum** — Native workspace skill. Drop the `skills/` directory into your workspace.
- **Claude Code** — Symlink into `~/.claude/skills/` using the install script.

**Should work with any framework that supports:**
- Reading/writing markdown files on disk
- Following structured skill instructions (SKILL.md)
- Multi-turn conversation with the user

The `/tutor` and `/tutor-setup` command syntax is a convention — adapt the entry point to however your framework invokes skills.

---

## What It Does

Three learning modes from a single command:

**Multiple Choice (MCQ)** — 4-question rounds with adaptive difficulty. Tracks correct/wrong per concept. Automatically drills your weakest areas. Proficiency dashboard updates after every round.

**Free Response (FR)** — Open-ended questions evaluated by three parallel AI agents: one for content coverage, one for mechanistic depth, and one for misconceptions. A graph-based node weighting system decides what to ask next based on concept centrality and your current mastery level.

**Guided Reading** — Conversational teaching for when you don't know the material yet. The agent walks you through concepts in a structured reading path, flags false friends, follows epistemic rules, and transitions to assessment when you're ready. No quizzing until you say so.

All three modes share the same StudyVault format and dashboard. MCQ accuracy, FR depth scores, and Guided Reading coverage all feed into the same W(n) priority graph.

### Scope Contract System (FR Mode)

Every free-response question includes a **scope contract** — a hidden set of 3–6 specific claims being tested. This solves the problem of broad questions being graded against unreasonably specific expectations:

- **Scope claims** = what the question explicitly tests. Grading happens ONLY against these.
- **Vault gaps** = everything else in the concept note. Tracked across sessions, not graded.
- **Specificity alignment** — broad question → lenient grading on breadth. Specific question → strict grading on depth. The question text itself signals which mode you're in.
- **Progressive depth** — Score well (🟢/🌟) and the system suggests diving into untested vault gaps. Score poorly (🔴/🟡) and it focuses on reinforcing what was asked, saving gaps for later.
- **Persistence** — Vault gaps are tracked in `fr-graph/vault-gaps.md` per node, so the system remembers what has and hasn't been tested across sessions.

This means you're always graded fairly against what was actually asked, while the system quietly tracks what it hasn't tested you on yet and surfaces it when you're ready.

### Micro-Assessment Loop (FR Mode)

After scoring a free-response answer, the tutor walks you through your gaps — but instead of a one-way lecture, each teaching segment ends with a comprehension checkpoint:

- **Quiz me** — 1-2 targeted micro-questions on what was just taught, graded with the same 3-agent evaluator pipeline as full FR (not binary pass/fail)
- **Keep going** — move to the next segment
- **Re-explain** — try a different angle

Micro-quizzes use the same scope contract system (fewer claims — typically 1-2) and the same weighted scoring formula. The difference: they produce a **fractional** weight update via a configurable `MICRO_WEIGHT_MULTIPLIER` (default 0.3×). A student who scores 0.90 on a micro-quiz gets proportionally more credit than one who scores 0.55 — the pipeline preserves grading granularity at every scale.

If you fail a micro-quiz (< 0.50), the tutor re-teaches with a different framing and offers a re-quiz. Multiple micro-quiz results compound: score poorly on the initial FR but nail all the checkpoints, and your weight adjusts upward to reflect actual in-session learning.

### Claim Ledger — Persistent Learner State (FR Mode)

Every FR and micro-quiz result is written to a **paired tracker file** — a structured markdown ledger that lives alongside each concept note:

- Concept note: `{unit}/Ch07-Cellular-Respiration.md` — **ground truth** (content only, never modified by session data)
- Tracker file: `concepts/Ch07-Cellular-Respiration-fr.md` — **learner state** (claim tables, persistent gaps, misconception history)

The concept note's YAML frontmatter includes a `tracker:` field pointing to the paired file. At session start, the agent reads both — using claim history and persistent gaps to target questions at your weakest specific claims, not just your weakest topics.

**Why separate files?** Appending learner history (including wrong answers) to the concept note risks context contamination — weaker models could mistake student misconceptions for facts, especially when error history grows long. Clean separation: content is ground truth, tracker is learner state.

This makes the vault fully self-contained and agent-agnostic. Any agent that can read markdown can reconstruct your exact learner state — no vector database, no memory system, no framework dependency. Just files.

### Guided Reading Mode

For material you don't already know, Guided Reading teaches before testing:

1. **Orientation** — Auto-generated reading guide: domain scope, structure, reference system, genre conventions, and a recommended non-linear approach. Saved per-source as `reading-guide-{source_id}.md` so multi-source vaults each get their own.

2. **Reading Path** — A phased teaching sequence derived from the vault's wiki-link graph. Topological sort of dependencies, interleaved with applied neighbors so you see *why* each foundation matters. Auto-generated from graph topology by default; manually curated `reading-path-{source_id}.md` overrides are supported for deep-reading use cases.

3. **Teaching Loop** — The agent walks through each node conversationally: explains with epistemic precision, flags false friends before you can misinterpret them, invites questions, and offers four options at each step: *Next*, *Quiz me on this*, *Go deeper*, or *Jump to [topic]*.

4. **Readiness Transition** — When you signal readiness (or 60%+ of the reading path is covered), the system suggests switching to FR or MCQ mode. Discussed-but-untested nodes get priority in the assessment queue.

Guided Reading sessions update recency (`R(n)`) without touching mastery (`M(n)`) — no assessment means no mastery claim. Session progress is logged to `fr-graph/reading-log.md`.

### Epistemic Rules

Every claim in a vault note can carry a provenance tag:

- **`[A]` Attested** — directly from the primary source, with citation. Graded strictly in FR.
- **`[S]` Scholarship** — from commentary or secondary sources, with attribution. Any credible interpretation accepted.
- **`[I]` Inference** — the agent's own synthesis. Clearly labeled. NOT graded in FR — the student isn't responsible for the agent's interpretations.

This matters most for philosophical, historical, and interpretive texts where the line between source and commentary is critical. For technical/scientific sources, most claims default to `[A]`.

### False Friends

A **false friends file** (`00-Dashboard/false-friends-{source_id}.md`) lists domain terms that look like ordinary English but carry specialized meaning. During Guided Reading, the agent alerts *before* teaching a node with false friends. During FR evaluation, misuse of a false friend term gets flagged by the Misconception Detector (Evaluator 3). During MCQ, false friend distractors use the everyday meaning as wrong answers.

Format: lookup table with columns for term, everyday meaning, domain meaning, why it matters, and linked nodes.

### Multi-Source Vaults — Incremental Ingestion

A vault isn't limited to a single PDF. Add new sources over time — textbooks, papers, documentation, codebases — and the system integrates them into your existing knowledge graph:

- **Incremental ingestion** — New sources get mapped against existing concept notes. Overlapping topics are enriched (not rebuilt). New topics get their own notes with wiki-links to existing ones.
- **Contradiction flagging** — When a new source conflicts with existing notes, the system flags it explicitly rather than silently overwriting.
- **Source attribution** — Every concept note tracks which sources contributed to it via frontmatter (`source:` for primary, `sources:` for all contributors). A source registry in the dashboard lists everything that's been ingested.
- **Scoped grading** — Study sessions are scoped to a specific source (or "all"). The W(n) priority queue, question generation, and weight propagation only operate within the active source scope. Cross-source wiki-links are visible for context but don't bleed into grading. This means you can have Biology 2e + a CRISPR paper + AWS docs in one vault without the grading systems interfering.

This follows the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — the vault is a persistent, compounding artifact that gets richer with every source. The difference: learn-graph adds adaptive assessment on top, with grading isolation between sources.

---

## Prerequisites

- Any AI agent framework with skill/tool support (Claude Code, Vellum, or similar)
- **poppler** for PDF text extraction:
  - macOS: `brew install poppler`
  - Ubuntu/Debian: `sudo apt-get install poppler-utils`
  - Fedora/RHEL: `sudo dnf install poppler-utils`
  - Arch: `sudo pacman -S poppler`

---

## Installation

```bash
git clone https://github.com/garrison-faridi/learn-graph.git
cd learn-graph
bash install.sh
```

The install script checks for poppler and copies the skill files into your agent's skill directory. For Claude Code, it symlinks into `~/.claude/skills/`. For other frameworks, copy the `skills/` directory to wherever your agent reads skill definitions.

To install as standalone copies (works with any framework):
```bash
bash install.sh --copy
```

---

## Quick Start

### From any PDF

```
/tutor /path/to/your/document.pdf
```

Claude extracts the PDF, builds a StudyVault, then asks which mode you want. Works with textbooks, papers, documentation — anything with extractable text.

### From an existing StudyVault

Navigate to the directory containing your `StudyVault/` folder, then:

```
/tutor
```

### Set up a vault manually (advanced)

```
/tutor-setup
```

Supports both **Document Mode** (PDFs, text, web content) and **Codebase Mode** (source code projects). Use this when you want full control over vault construction before starting study sessions.

---

## Session Flow

```
/tutor [optional path]
        |
        v
  Phase 0: Detect language
        |
        v
  Phase 1: Find StudyVault?
    |              |
   YES             NO
    |              |
    |        Ask for PDF/source path
    |        Run pdftotext
    |        Build vault (D1-D9)
    |              |
    v              v
  Phase 2: Choose mode
          |           |           |
    Multiple        Free        Guided
     Choice        Response     Reading
              |           |
              v           v
       Build 4 MCQ    Load graph weights
        questions     (node-weights.md)
              |           |
              v           v
        AskUser quiz  Generate scope contract
            round     (scope_claims + vault_gaps)
              |           |
              v           v
         Grade &     Generate FR question
          explain    (aligned to scope)
              |            |
              v            v
         Update      3 eval agents grade
         concept     against scoped claims
         file +              |
        dashboard            v
                       Agent 4 synthesis
                             |
                             v
                       Grade + Socratic
                       feedback + depth
                        suggestions
                             |
                             v
                       Post-teaching loop:
                        Teach → Quiz me /
                        Keep going / Re-explain
                        (micro-quizzes use same
                         3-agent pipeline at 0.3×)
                             |
                             v
                       Update tracking
                       files + claim ledger
                       + vault gaps
                       + recompute weights
                       (via weight_calc.py)
```

---

## StudyVault Structure

```
StudyVault/
├── 00-Dashboard/
│   ├── MOC - {Subject} Study Map.md   ← proficiency table + area links
│   ├── Quick Reference.md             ← cheat sheet with key concept links
│   └── Exam Traps.md                  ← per-topic common mistake callouts
├── 01-{Topic}/
│   ├── {Concept A}.md                 ← concept note with wiki-links
│   ├── {Concept B}.md
│   └── {Topic} Practice.md            ← 8+ folded questions
├── 02-{Topic}/
│   └── ...
├── concepts/
│   ├── {area}.md                      ← MCQ concept tracker (per area)
│   └── {area}-fr.md                   ← FR tracker (per area)
└── fr-graph/
    ├── node-weights.md                ← W(n) scores for all concept nodes
    ├── nuance-gaps.md                 ← running log of identified FR gaps
    └── vault-gaps.md                  ← untested depth per node (scope contract)

scripts/
└── weight_calc.py                     ← deterministic W(n) calculator (Python CLI)
```

**Concept note ↔ tracker pairing:**
```
{unit}/Ch07-Cellular-Respiration.md       ← content (ground truth)
  frontmatter: tracker: concepts/Ch07-Cellular-Respiration-fr.md
concepts/Ch07-Cellular-Respiration-fr.md  ← learner state (claim ledger)
```

---

## How Tracking Works

### MCQ Tracking

Every concept you answer is recorded in `concepts/{area}.md`:

| Concept | Attempts | Correct | Last Tested | Status |
|---------|----------|---------|-------------|--------|
| Hardy-Weinberg | 3 | 2 | 2026-04-05 | 🟢 |

The dashboard aggregates these into per-area proficiency badges:

| Level | Badge | Range |
|-------|-------|-------|
| Weak | 🟥 | 0–39% |
| Fair | 🟨 | 40–69% |
| Good | 🟩 | 70–89% |
| Mastered | 🟦 | 90–100% |
| Unmeasured | ⬜ | no data |

### FR Node Weighting

Each concept node gets a weight `W(n)` computed from four factors:

```
W(n) = 0.25 * C(n)        ← centrality: how many notes link to this concept
     + 0.35 * (1 - M(n))  ← mastery: combined MCQ accuracy + FR depth score
     + 0.20 * P(n)         ← prerequisite gap: whether linked nodes are also weak
     + 0.20 * R(n)         ← recency: time since last tested (decays over 14 days)
```

Nodes with high centrality and low mastery surface first. After each FR session, the `weight_calc.py` script recomputes weights deterministically and writes them to `fr-graph/node-weights.md`. No LLM arithmetic — the agent passes evaluation scores to the script, which handles all math and file I/O.

### FR Evaluation Pipeline

Three parallel agents evaluate every free-response answer:

- **Agent 1 — Content Coverage** *(scope-aware)*: scores what fraction of **scoped claims** are present. Vault gaps are tracked separately as untested depth, not penalized.
- **Agent 2 — Depth & Nuance**: scores mechanistic reasoning, edge cases, quantitative accuracy, and cross-concept coherence
- **Agent 3 — Misconception Detector**: checks for sign reversals, conflations, hallucinations, and repeated prior errors

**Agent 4** synthesizes all three:
```
overall_score = 0.45 * coverage_score
              + 0.40 * depth_score
              + 0.15 * (1 - misconception_penalty)
```

Grades: 🌟 Excellent (≥0.85) · 🟢 Good (0.70–0.84) · 🟡 Developing (0.50–0.69) · 🔴 Needs Work (<0.50)

Feedback is Socratic — no answers given, only targeted questions pointing at your gaps. On strong scores, the system suggests untested vault gaps as optional depth dives.

### Vault Gap Tracking

Vault gaps persist across sessions with a lifecycle:

| Status | Meaning |
|--------|---------|
| **UNTESTED** | Logged from scope contract, never asked about |
| **OFFERED** | Suggested to student as a depth dive |
| **TESTED** | Asked about in a subsequent scoped question |
| **ABSORBED** | Student addressed voluntarily without being asked |

This creates a progressive depth system — the tool knows what you've been tested on, what you haven't, and when you're ready to go deeper.

---

## Troubleshooting

**`pdftotext: command not found`**
Install poppler first (see Prerequisites above), then re-run `/tutor`.

**No StudyVault found**
Pass a PDF path directly: `/tutor /path/to/file.pdf`
Or run setup first in your sources directory: `/tutor-setup`

**Skills not available after install**
Confirm the skill files exist in your agent's skill directory. Re-run `bash install.sh` if not.
Restart your agent after any install.

**FR agents evaluate for the wrong subject**
The domain name is extracted from your dashboard's H1: `# {Subject} Study Map`.
If the heading was changed, restore it to that format and re-run `/tutor`.

**Dashboard badges out of sync with concept files**
Re-run `/tutor` — Phase 1 re-reads all existing files, and MCQ-6 recalculates stats
directly from `concepts/{area}.md` files.

---

## Attribution

Built on top of [**RoundTable02/tutor-skills**](https://github.com/RoundTable02/tutor-skills) (MIT licensed). The original included MCQ quizzing and vault setup skills.

**Changes and additions in this fork:**

- **Free-response mode** with graph-based node weighting (`W(n)`), three parallel evaluator agents, and Socratic synthesis feedback
- **Scope contract system** — questions define scoped claims for fair grading + vault gaps for progressive depth tracking
- **Unified entry point** — single `/tutor` command handles vault setup, mode selection, MCQ, and FR
- **Micro-assessment loop** — post-teaching comprehension checkpoints with the same graded evaluator pipeline (not binary pass/fail), fractional weight updates via configurable multiplier
- **Claim ledger persistence** — per-node tracker files with claim-level pass/fail history, persistent gap checklists, and misconception logs. Fully agent-agnostic (pure markdown, no DB dependency)
- **Multi-source incremental ingestion** — add new sources to existing vaults without rebuilding. Contradiction flagging, source attribution, and scoped grading keep assessment isolated per source while knowledge compounds across them
- **Deterministic weight calculator** — Python script (`scripts/weight_calc.py`) replaces LLM arithmetic for all W(n) updates. Commands: `update`, `score`, `recalc`, `next`, `show`. Supports full FR and micro-assessment updates with atomic file writes (prevents data loss during session handoffs)
- **Inline vault setup** — pass a PDF path directly, no separate `/tutor-setup` step needed
- Domain-agnostic evaluator prompts (extracted from vault at runtime)
- Fixed hardcoded `pdftotext` path to use runtime detection
- `install.sh` with OS-aware poppler detection and symlink/copy install modes
