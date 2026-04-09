---
name: tutor
description: >
  Adaptive learning engine for any knowledge source. Builds and drills from
  Obsidian-compatible StudyVaults using MCQ quizzes, free-response with
  multi-evaluator grading, micro-assessments, guided reading, and spaced
  repetition via node-weight graphs. Supports multi-source vaults with
  scoped grading.
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
      - "User says 'teach me', 'walk me through', or 'explain this material'"
    avoid-when:
      - "User wants a simple summary or extraction from a PDF (no assessment)"
      - "User is asking for general knowledge, not drilling from a specific source"
      - "User wants to build a vault but not start studying (use tutor-setup instead)"
    includes:
      - "tutor-setup"
---

# Tutor — Unified Adaptive Learning Skill

Router for three learning modes: MCQ, Free Response, and Guided Reading.
Phases 0–2 are shared setup. Phase 3+ is delegated entirely to a mode-specific reference doc.

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

If the user selects "all", disable source filtering — the full vault is active.
If the vault has only one source, skip this phase entirely.

---

## Phase 2: Mode Dispatch

Ask the user which learning mode they want:

1. **Multiple Choice** — "4-option MCQ quiz. Fast rounds, tracks accuracy by concept."
2. **Free Response** — "Write-your-own-answer with multi-agent evaluation and depth scoring."
3. **Guided Reading** — "Conversational teaching. I'll walk you through the material — tell me when you're ready to be tested."

Then load the mode-specific reference and follow it completely:

| Mode | Reference Doc | Key Phases |
|------|--------------|------------|
| Multiple Choice | `skills/tutor/references/quiz-rules.md` | MCQ-3 → MCQ-6 |
| Free Response | `skills/tutor/references/free-response-rules.md` | FR-3 → FR-8 |
| Guided Reading | `skills/tutor/references/guided-reading-rules.md` | GR-3 → GR-7 |

**MANDATORY**: Read the reference doc for the selected mode BEFORE proceeding. The reference
doc contains the complete session workflow — do not proceed from memory alone.

---

## Shared Rules (All Modes)

- Communicate in user's detected language for all output
- StudyVault data stays on disk, separate from the assistant's operational memory graph
- After every session: ALWAYS update tracking files
- **Weight calculations**: ALWAYS use `skills/tutor/scripts/weight_calc.py` — never compute
  weights manually. Commands: `update`, `update --micro`, `discussed`, `recalc`, `next`, `show`.
- **Epistemic discipline**: In ALL modes, distinguish attested `[A]` claims (primary source),
  scholarship `[S]` (secondary/commentary), and inference `[I]` (agent synthesis). Never
  present inference as if it were attested.
- **False friends**: Check `00-Dashboard/false-friends-{source_id}.md` (or `false-friends.md`
  for single-source vaults) before teaching or quizzing any node. Flag domain terms that
  look like ordinary words but carry specialized meaning.
