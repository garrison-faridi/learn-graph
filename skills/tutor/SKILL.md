---
name: tutor
description: >
  Adaptive learning engine for any knowledge source. Builds and drills from
  Obsidian-compatible StudyVaults using MCQ quizzes, free-response with
  multi-evaluator grading, micro-assessments, and spaced repetition via
  node-weight graphs. Supports multi-source vaults with scoped grading.
  Use when: studying, quizzing, reviewing, learning from a PDF, testing
  knowledge, checking mastery, practicing recall, or building a study vault.
argument-hint: "[optional: pdf-path or source-path]"
metadata:
  vellum:
    activation-hints:
      - "User wants to study, learn, or review material from a document or vault"
      - "User says 'quiz me', 'test me', 'let's study', or 'check my knowledge'"
      - "User mentions a StudyVault, study session, or mastery progress"
      - "User provides a PDF and wants to learn from it, not just summarize it"
    avoid-when:
      - "User wants a simple summary or extraction from a PDF (no assessment)"
      - "User is asking for general knowledge, not drilling from a specific source"
      - "User wants to build a vault but not start studying (use tutor-setup instead)"
    includes:
      - "tutor-setup"
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

Ask the user which learning mode they want:

1. **Multiple Choice** — "4-option MCQ quiz. Fast rounds, tracks accuracy by concept."
2. **Free Response** — "Write-your-own-answer with multi-agent evaluation and depth scoring."
3. **Guided Reading** — "Conversational teaching. I'll walk you through the material — tell me when you're ready to be tested."

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
2. **If found**: verify accuracy by running:
   ```bash
   python3 skills/tutor/scripts/weight_calc.py recalc <vault>/fr-graph/node-weights.md
   ```
3. **If not found**: seed the initial file:
   - Count `[[NodeName]]` wiki-link occurrences per node → in-degree
   - Normalize: `C(n) = in_degree(n) / max_in_degree`
   - Set defaults: `M(n) = 0.50`, `P(n) = 0.00`, `R(n) = 0.00`
   - Write the markdown table to `fr-graph/node-weights.md` (see existing vaults for format)
   - Run `weight_calc.py recalc` to compute all W(n) values deterministically
4. Run `python3 skills/tutor/scripts/weight_calc.py next <weights_file>` to get top priority nodes.

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

**Synthesis**: Combine scores per `evaluator-prompts.md` formula → overall grade.
Grades: 🌟 ≥0.85 · 🟢 0.70–0.84 · 🟡 0.50–0.69 · 🔴 <0.50

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
4. Update weights via script with `--micro` flag:
   ```bash
   python3 skills/tutor/scripts/weight_calc.py update <weights_file> <node> \
     --coverage <cov> --depth <dep> --misconception <mis> --micro
   ```
5. If score < 0.50 → re-teach with different framing, offer re-quiz (max 2 attempts)
6. If score >= 0.50 → proceed to next gap segment

Micro-quizzes use the same graded pipeline (not binary pass/fail) because a 0.90 score
reflects stronger comprehension than 0.55 — the `--micro` flag applies a 0.3× multiplier
to the weight update automatically.

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

#### FR-8c — Update Node Weights

Run the weight calculator script with the evaluator scores from FR-6c:

```bash
python3 skills/tutor/scripts/weight_calc.py update <weights_file> <node> \
  --coverage <cov> --depth <dep> --misconception <mis> --decay
```

The `--decay` flag also adjusts recency for all other nodes. **Do not compute
weights manually** — the script handles EMA mastery updates, recency decay,
and atomic file writes to prevent data loss during session handoffs.

---

## Guided Reading Workflow (when {mode} = Guided Reading)

**MANDATORY**: Read `skills/tutor/references/guided-reading-rules.md` before starting any
Guided Reading session.

### GR-3: Orientation

1. Check for `00-Dashboard/reading-guide-{source_id}.md` in the vault.
   (In single-source vaults, use `reading-guide.md` without suffix.)
2. If found, present the orientation (domain structure, reference systems, recommended approach).
3. If not found, auto-generate from graph topology scoped to `{active_source}`
   (see guided-reading-rules.md) and save.
4. Ask: "Want the full orientation, or ready to dive in?"

### GR-4: Load Reading Path

1. Check for `00-Dashboard/reading-path-{source_id}.md` in the vault.
   (In single-source vaults, use `reading-path.md` without suffix.)
2. **If found**: use the manually curated path (may define phases, interleaving, pacing notes).
3. **If not found**: auto-generate from wiki-link topology scoped to `{active_source}` —
   topological sort of dependencies, interleave foundational with applied, group into phases.
   Save as `00-Dashboard/reading-path-{source_id}.md`.
4. Present the path overview. User can accept, modify, or skip ahead.

### GR-5: Teaching Loop

For each node in the reading path:

1. Read the concept note and its wiki-linked neighbors.
2. Check `00-Dashboard/false-friends-{source_id}.md` (or `false-friends.md` for single-source) —
   if the current node contains any false friends,
   alert BEFORE teaching:
   > ⚠️ **False Friend: "{term}"** — {why the everyday meaning is wrong} → {domain meaning}
3. Teach conversationally using vault content as ground truth. Follow **epistemic rules**:
   - **`[A]` Attested**: from the primary source (cite page/section)
   - **`[S]` Scholarship**: from commentary or secondary sources (with attribution)
   - **`[I]` Inference**: agent's own synthesis (label clearly)
4. Invite questions. Respond using vault content + wiki-linked context.
5. After covering the node, offer:
   - **"Next"** — continue to next node in the path
   - **"Quiz me on this"** — transition to FR for this node only (FR-5 through FR-8), then return
   - **"Go deeper"** — explore wiki-linked neighbors beyond the reading path
   - **"Jump to [topic]"** — skip ahead in the path

### GR-6: Readiness Transition

When the learner signals readiness (explicit: "quiz me" / "test me"; implicit: making claims
unprompted; or 60%+ of path nodes discussed), suggest transitioning to FR or MC mode.
If they transition, switch `{mode}` and begin the corresponding workflow with the full vault.

### GR-7: Session Persistence

1. Mark discussed nodes in `fr-graph/node-weights.md` — update R(n) only, no mastery change:
   ```bash
   python3 skills/tutor/scripts/weight_calc.py discussed <weights_file> <node> --decay
   ```
2. Append to `fr-graph/reading-log.md`: nodes covered, questions asked, false friends flagged,
   where the learner paused or asked for re-explanation, and pickup point for next session.

---

## Important Reminders

- ALWAYS read reference rules before creating questions (quiz-rules.md or free-response-rules.md)
- ALWAYS read guided-reading-rules.md before any Guided Reading session
- NEVER include hints in MCQ options
- NEVER give away the answer in FR feedback — Socratic probing only
- NEVER skip the multi-perspective evaluation in FR mode
- Randomize correct MCQ answer position every round
- After every session: ALWAYS update tracking files
- Communicate in user's detected language for all output
- StudyVault data stays on disk, separate from the assistant's operational memory graph
- **Epistemic discipline**: In ALL modes, distinguish attested `[A]` claims (primary source),
  scholarship `[S]` (secondary/commentary), and inference `[I]` (agent synthesis). Never
  present inference as if it were attested.
- **False friends**: Check `00-Dashboard/false-friends-{source_id}.md` (or `false-friends.md`
  for single-source vaults) before teaching or quizzing any node. Flag domain terms that
  look like ordinary words but carry specialized meaning.

### Scope Contract System (FR Mode)

Every FR question MUST include a **scope contract** — see `free-response-rules.md` for full spec.

- **Scope claims** (3–6) = what the question tests. Grading is ONLY against these.
- **Vault gaps** = everything else in the vault note. Tracked, not graded.
- Question specificity MUST match grading specificity: broad question → lenient grading on breadth; specific question → strict grading on depth.
- The question text itself must signal which mode: "describe" = broad, "explain step by step" / "in detail" = specific.
- After grading, vault gaps are persisted in `fr-graph/vault-gaps.md` per node.
- If score is 🟢/🌟, suggest untested vault gaps as depth dives.
- If score is 🔴/🟡, focus on reinforcing scoped claims. Save gaps for later.
