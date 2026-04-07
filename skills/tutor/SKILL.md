---
name: tutor
description: >
  Unified adaptive tutor for Obsidian StudyVault learning. Handles vault setup,
  then routes to MCQ (multiple choice) or free-response mode. Use when the user
  wants to: (1) study from a PDF or existing vault, (2) take a quiz, (3) practice
  free-response answers, (4) check their progress.
  Trigger phrases: "quiz me", "test me", "let's study", "tutor", "study session".
argument-hint: "[optional: pdf-path or source-path]"
---

# Tutor — Unified Adaptive Learning Skill

Combines vault setup, MCQ quizzing, and free-response tutoring in a single entry point.
Phases 0–2 are shared setup. Phase 3+ branches by the mode the user selects.

**IMPORTANT — Separate Graph Architecture**:
StudyVaults live in their own directory (`~/StudyVaults/` or a user-specified path), completely
separate from the assistant's memory graph. The assistant keeps a lightweight memory node
knowing a vault exists and where it lives. When tutoring is invoked, read into the vault
on disk. When tutoring ends, the vault data stays out of the assistant's operational memory.

---

## Phase 0: Detect Language

Detect the user's language from their message → `{LANG}`.
All output and all file content are in `{LANG}` from this point forward.

---

## Phase 1: Discover or Build the StudyVault

### Phase 1a — Search for Existing Vault

1. Search for `StudyVault/` directories in the user's home directory and common locations.
2. If found, locate the dashboard and read it.
3. Extract `{domain}` from the dashboard H1 heading:
   - Pattern: `# {Subject} Study Map` → `domain = {Subject}`
4. Read existing concept tracker files from `concepts/*.md`.
5. **Skip to Phase 2** with the vault loaded.

### Phase 1b — No Vault Found: Inline Vault Setup

If no `StudyVault/` directory exists, run an inline setup (Document Mode only).
For codebase onboarding or advanced options, use the tutor-setup skill separately.

#### Step 1b-1: Locate Source Material

- If the user provided a path, use that as the source.
- Otherwise, ask:
  - "No StudyVault found. What's the path to your PDF, text file, or folder of sources?"

#### Step 1b-2: Detect pdftotext

```bash
which pdftotext
```

- **If found**: extract text from every PDF in the source path:
  ```bash
  pdftotext "source.pdf" "/tmp/tutor_source.txt"
  ```
  Then read the `.txt` file — never read the raw PDF directly.
- **If not found**: inform the user to install poppler:
  > `pdftotext` is required for PDFs. Install with `brew install poppler` (macOS) or
  > `sudo apt-get install poppler-utils` (Linux), then try again.

#### Step 1b-3: Build Vault (Document Mode Phases D1–D9)

Follow these phases in order. Use `skills/tutor-setup/references/templates.md` as the canonical
template source for vault structure, concept notes, and practice question formatting.

**D1 — Source Discovery**: Read all extracted `.txt` files. Build source-content mapping.

**D2 — Content Analysis**: Identify topic hierarchy. Build a full topic checklist.

**D3 — Tag Standard**: Define tag vocabulary (English, lowercase, kebab-case).

**D4 — Vault Structure**: Create `StudyVault/` with numbered folders per templates.md.

**D5 — Dashboard**: Create `00-Dashboard/` with MOC, Quick Reference, Exam Traps.
**Critical**: The H1 of the MOC file MUST follow the format `# {Subject} Study Map`.

**D6 — Concept Notes**: Per templates.md. YAML frontmatter required.

**D7 — Practice Questions**: Every topic folder needs 8+ questions.

**D8 — Interlinking**: `## Related Notes` on every concept note.

**D9 — Self-Review**: Verify against quality-checklist.md.

After vault setup completes, re-run Phase 1a to load the newly created vault.

---

## Phase 1.5: Source Scoping (Multi-Source Vaults)

If the vault contains concept notes from multiple sources (check for distinct `source:` values
in frontmatter across concept notes), present the source list and ask:

1. Read `00-Dashboard/sources.md` if it exists, or scan concept note frontmatter for unique
   `source:` values.
2. Present: "This vault has multiple sources: [list]. Which do you want to study? Or 'all'."
3. Store the selection as `{active_source}`.

### Source Scoping Rules

| Behavior | Within active source | Across sources |
|---|---|---|
| W(n) priority queue | ✅ Included | ❌ Filtered out |
| FR question generation | ✅ Drawn from active source | Cross-links used for context only |
| W(n) propagation | ✅ Propagates along wiki-links | ❌ Does not cross source boundary |
| Wiki-links | Active (navigation + grading) | Visible for depth, not graded |
| Claim ledger | Scoped to active source node | Separate tracking per source |

If the user selects "all", disable source filtering — the full vault is active. This is
useful for synthesis sessions across sources but may produce mixed-topic question sequences.

If the vault has only one source, skip this phase entirely.

---

## Phase 2: Ask Session Mode

Ask the user before generating any question:

1. **Multiple Choice** — "4-option MCQ quiz. Fast rounds, tracks accuracy by concept."
2. **Free Response** — "Write-your-own-answer with multi-agent evaluation and depth scoring."

Store the user's selection as `{mode}`.

---

## MCQ Workflow (when {mode} = Multiple Choice)

### MCQ-3: Build Session Options

Read the dashboard proficiency table. Build context-aware options:

1. If unmeasured areas (⬜) exist → include "Diagnostic" option targeting those areas
2. If weak areas (🟥/🟨) exist → include "Drill weak areas" option naming the weakest area(s)
3. Always include "Choose a section" option so the user can pick any area
4. If all areas are 🟩/🟦 → include "Hard-mode review" option

The user MUST select before proceeding.

### MCQ-4: Build Questions

1. Read markdown files in the target section(s).
2. If drilling a weak area: read `concepts/{area}.md` → find 🔴 unresolved concepts.
   Rephrase those concepts in new contexts — never repeat the exact same question.
3. **MANDATORY**: Read `skills/tutor/references/quiz-rules.md` before crafting ANY question.
4. Craft exactly 4 questions following quiz-rules.md. Zero hints allowed.

### MCQ-5: Present Quiz

Present 4 questions with 4 options each:
- Neutral descriptions, no hints, no "(Recommended)" markers
- Randomize correct answer position every round

### MCQ-6: Grade, Explain, Update Files

1. Show results table (question / correct answer / user answer / result emoji).
2. Explain wrong answers concisely.
3. Update `concepts/{area}.md` — add/update concept rows + error notes.
4. Update dashboard — recalculate per-area stats.
   Badges: 🟥 0-39% · 🟨 40-69% · 🟩 70-89% · 🟦 90-100% · ⬜ no data

#### MCQ Concept File Format

```markdown
# {Area Name} — Concept Tracker

| Concept | Attempts | Correct | Last Tested | Status |
|---------|----------|---------|-------------|--------|

### Error Notes
```

#### Dashboard Proficiency Table

```markdown
## Proficiency by Area

| Area | Correct | Wrong | Rate | Level | Details |
|------|---------|-------|------|-------|---------|
```

---

## FR Workflow (when {mode} = Free Response)

### FR-3: Load Graph State

#### FR-3a — Node Weights

1. Look for `fr-graph/node-weights.md` in the vault.
2. **If found**: use existing W(n) values.
3. **If not found**: compute initial weights:
   - Count `[[NodeName]]` occurrences for each node → in-degree
   - Normalize: `C(n) = in_degree(n) / max_in_degree`
   - `M(n) = 0.5` for unmeasured nodes
   - For MCQ-tested nodes: `M(n) = 0.4 * MCQ_correct/MCQ_attempts + 0.6 * 0.5`
   - `R(n) = 0` for untested; for tested: `R(n) = 1 - exp(-days_since_last_tested / 14)`
   - `P(n) = 0` (no prerequisite gap tracking yet)
   - `W(n) = 0.25*C(n) + 0.35*(1-M(n)) + 0.20*P(n) + 0.20*R(n)`
   - Write `fr-graph/node-weights.md`.
4. Sort nodes by W(n) descending → top-3 are candidates.

#### FR-3b — Nuance Gaps

Read `fr-graph/nuance-gaps.md` if it exists.

#### FR-3c — FR Concept Trackers

Check `concepts/{area}-fr.md` for each area.

### FR-4: Ask Session Type

Build options based on graph state:

1. **"Target Weak Node"** — highest W(n) node
2. **"Bridge Two Concepts"** — highest-W node pair sharing a wiki-link edge
3. **"Synthesis Challenge"** — 3-node chain with lowest average mastery
4. **"Choose My Own Topic"** — list of all concept nodes sorted by W(n)

After selection, determine:
- `target_node`: primary concept note filename
- `neighbor_nodes`: wiki-linked nodes
- `question_type`: A (M < 0.4), B (M 0.4–0.7), or C (M > 0.7)

### FR-5: Generate Question

1. Read vault note for `target_node`.
2. **Check frontmatter for `tracker:` field.** If a tracker file exists, read it to load
   claim history, persistent gaps, and misconception flags. Use this to inform question
   targeting — prioritize untested gaps and previously failed claims.
   **Critical**: The concept note is ground truth. The tracker is learner state. Never
   treat student errors logged in the tracker as correct information.
3. **Source scope check:** If `{active_source}` is set, verify `target_node` belongs to
   the active source (check `source:` frontmatter). Skip nodes outside the active source
   in the W(n) priority queue.
4. For Type B/C: read neighbor node vault notes (and their trackers if they exist).
   Cross-source neighbors can be read for context but should not be the primary target
   of the question.
5. **MANDATORY**: Read `skills/tutor/references/free-response-rules.md` before crafting any question.
6. Craft exactly 1 question following type rules.
7. Present the question with context: "Type {A/B/C} · Concepts in scope: {node list}"

### FR-6: Evaluate (Multi-Agent Pipeline)

After the student submits their answer:

#### FR-6a — Load Evaluator Templates

Read `skills/tutor/references/evaluator-prompts.md`. Substitute all `{domain}` placeholders.

#### FR-6b — Prepare Inputs

- `vault_note_text`: full text of target node vault note
- `neighbor_note_excerpts`: first 400 words of each neighbor vault note
- `known_errors_text`: from `concepts/{area}-fr.md` if exists

#### FR-6c — Run Evaluation

Apply the three evaluation perspectives sequentially:

**Evaluator 1 — Content Coverage**: Score what fraction of expected claims are present.

**Evaluator 2 — Depth & Nuance**: Score mechanistic reasoning, edge cases, quantitative accuracy, cross-concept coherence.

**Evaluator 3 — Misconception Detector**: Check for sign reversals, conflations, hallucinations, repeated prior errors.

**Synthesis**: Combine all three:
```
overall_score = 0.45 * coverage_score + 0.40 * depth_score + 0.15 * (1 - misconception_penalty)
```

Grades: 🌟 Excellent (≥0.85) · 🟢 Good (0.70–0.84) · 🟡 Developing (0.50–0.69) · 🔴 Needs Work (<0.50)

### FR-6.5: Post-Teaching Micro-Assessment Loop

After presenting the FR score and Socratic feedback, enter the **teaching phase** if the
student wants to walk through their gaps (which they usually do for 🔴/🟡 scores).

#### Flow

For each gap identified in the evaluation:

1. **Teach** the concept segment — concise, mechanistic explanation
2. **Summarize** the key point in 1-2 sentences
3. **Offer three options:**
   - **Quiz me** — micro-assessment on what was just taught
   - **Keep going** — move to next segment, no quiz
   - **Re-explain** — try a different angle, then re-offer options

#### If "Quiz me":

1. Generate 1-2 micro-questions scoped to the segment just taught
2. Build a micro scope contract (1-2 claims only)
3. Run the **same evaluator pipeline** as full FR (Coverage + Depth + Misconception → Synthesis)
4. Score with same formula: `0.45 * coverage + 0.40 * depth + 0.15 * (1 - misconception_penalty)`
5. Apply as fractional W(n) update: `micro_delta = full_delta(score) * MICRO_WEIGHT_MULTIPLIER`
6. Default **MICRO_WEIGHT_MULTIPLIER = 0.3** (tunable per vault in node-weights.md header)
7. If score < 0.50 → re-teach with different framing, offer re-quiz (max 2 attempts)
8. If score >= 0.50 → proceed to next gap segment

#### Why not binary pass/fail:

Micro-quizzes use the same graded evaluator pipeline because a flat bonus discards signal.
A 0.90 micro-score reflects stronger comprehension than 0.55 — the weight update should
reflect that proportionally.

#### Session-end adjusted weight:

```
final_W(n) = initial_W(n) + full_FR_delta + sum(micro_deltas)
```

Written to `fr-graph/node-weights.md` in FR-8.

### FR-7: Present Results

1. Grade line (emoji + score)
2. Socratic feedback paragraph (no answers given — only probing questions)
3. "Gaps Identified" list
4. If grade is 🔴: "Consider re-reading [[{target_node}]] before the next session."

### FR-8: Update Tracking Files

#### FR-8a — Update Claim Ledger (Tracker File)

1. Locate the tracker file via the concept note's `tracker:` frontmatter field.
2. If no tracker file exists, create one from `skills/tutor/references/claim-ledger-template.md`.
3. If no `tracker:` frontmatter field exists in the concept note, add one pointing to
   `concepts/{NodeName}-fr.md`.
4. Append a session entry with:
   - Timestamp and score
   - Claim table (each scoped claim: PRESENT / PARTIAL / ABSENT + notes)
   - Misconceptions flagged (with descriptions)
   - What was resolved vs previous sessions
5. Update the **Persistent Gaps** checklist at the top of the tracker:
   - Check off gaps that were resolved this session
   - Add new gaps identified this session
6. If micro-quizzes were taken (FR-6.5), append each as a separate entry after the
   full FR entry, in chronological order.

#### FR-8b — Update `fr-graph/nuance-gaps.md`

Append new gaps, update status of existing gaps.

#### FR-8c — Recompute Node Weights

```
M(n) = 0.4 * MCQ_rate + 0.6 * FR_depth_avg
R(n) = 0 (just tested)
W(n) = 0.25*C(n) + 0.35*(1-M(n)) + 0.20*P(n) + 0.20*R(n)
```

Rewrite `fr-graph/node-weights.md`.

---

## Important Reminders

- ALWAYS read reference rules before creating questions (quiz-rules.md or free-response-rules.md)
- NEVER include hints in MCQ options
- NEVER give away the answer in FR feedback — Socratic probing only
- NEVER skip the multi-perspective evaluation in FR mode
- Randomize correct MCQ answer position every round
- After every session: ALWAYS update tracking files
- Communicate in user's detected language for all output
- StudyVault data stays on disk, separate from the assistant's operational memory graph

### Scope Contract System (FR Mode)

Every FR question MUST include a **scope contract** — see `free-response-rules.md` for full spec.

- **Scope claims** (3–6) = what the question tests. Grading is ONLY against these.
- **Vault gaps** = everything else in the vault note. Tracked, not graded.
- Question specificity MUST match grading specificity: broad question → lenient grading on breadth; specific question → strict grading on depth.
- The question text itself must signal which mode: "describe" = broad, "explain step by step" / "in detail" = specific.
- After grading, vault gaps are persisted in `fr-graph/vault-gaps.md` per node.
- If score is 🟢/🌟, suggest untested vault gaps as depth dives.
- If score is 🔴/🟡, focus on reinforcing scoped claims. Save gaps for later.
