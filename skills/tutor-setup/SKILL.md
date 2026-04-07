---
name: tutor-setup
description: >
  Build a StudyVault from any knowledge source — PDFs, docs, web pages,
  or codebases. Extracts concepts, generates practice questions, and seeds
  the node-weight graph for adaptive learning. Supports incremental ingestion
  into existing vaults with source attribution and contradiction flagging.
  Use when: setting up a new study vault, ingesting a PDF, adding a source,
  building from a codebase, or creating study materials from documents.
argument-hint: "[source-path-or-url]"
metadata:
  vellum:
    activation-hints:
      - "User wants to create a new StudyVault or study notes from a source"
      - "User provides a PDF, document, or codebase to build learning materials from"
      - "User wants to add a new source to an existing vault"
    avoid-when:
      - "User already has a vault and wants to study or quiz (use tutor instead)"
      - "User wants to summarize a document without building structured study materials"
---

# Tutor Setup — Knowledge to Obsidian StudyVault

## PDF Tooling: poppler / pdftotext

> **PDF extraction requires `pdftotext` (part of poppler).** Detect at runtime:
> ```bash
> which pdftotext
> ```
> If found, use for ALL PDF files. Never read raw PDFs directly.
> If not found, install: `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux).

### Large Textbook Strategy (300+ pages)
1. Run `pdftotext` on the full PDF first
2. Read TOC + first/last pages to build the topic map
3. Process section by section
4. Use `-f` / `-l` page flags for specific chapters if needed

---

## Incremental Ingestion (Adding Sources to Existing Vaults)

When a StudyVault already exists and the user provides a new source, run **incremental mode**
instead of building from scratch.

### Detection

If the user provides a source path AND a `StudyVault/` already exists at the expected location:
1. Ask: "Add this to your existing vault, or build a new one?"
2. If adding → Incremental Mode (below)
3. If new → Standard Document/Codebase Mode

### Incremental Mode Phases

**I1 — Source Extraction**: Extract text from the new source (same as D1).
Tag the source with a unique `source_id` (e.g., `crispr-2024-paper`).

**I2 — Content Mapping**: Identify topics in the new source. Compare against existing
vault concept notes:
- **Overlapping topics** — new source covers something already in the vault
- **New topics** — new source introduces concepts not yet in the vault
- **Cross-references** — new source references concepts already in the vault

**I3 — Update Existing Notes** (for overlapping topics):
1. Read the existing concept note
2. Integrate new information — add depth, examples, or alternative perspectives
3. Add `[[wiki-links]]` to any new notes being created
4. **Flag contradictions** explicitly in the note:
   ```markdown
   > [!contradiction] Source conflict
   > {source_id_1} states X. {source_id_2} states Y.
   > Possible explanation: {agent's assessment}
   ```
5. Update the `sources:` frontmatter field (see below)

**I4 — Create New Notes** (for new topics):
Follow D6 template. Set `source:` frontmatter to the new source_id.
Add `[[wiki-links]]` to relevant existing notes.

**I5 — Update Dashboard**: Add new topics to the MOC. Update the source registry.

**I6 — Seed Weights**: Add new nodes to `fr-graph/node-weights.md` at default W=0.325.
Existing node weights are NOT modified — learner state is preserved.

**I7 — Self-Review**: Verify new/updated notes against quality-checklist.md.

### Source Attribution

Every concept note MUST track which sources contributed to it via frontmatter:

```yaml
---
title: Cellular Respiration
unit: 02-The-Cell
source: biology-2e
sources:
  - id: biology-2e
    type: textbook
    added: 2026-04-06
  - id: metabolism-review-2024
    type: paper
    added: 2026-04-08
tracker: concepts/Ch07-Cellular-Respiration-fr.md
---
```

- `source:` = the PRIMARY source (used for study session scoping)
- `sources:` = ALL sources that contributed to this note (for attribution)

When updating an existing note with new source material, append to `sources:` and
preserve the original `source:` value.

### Source Registry

Maintain a `00-Dashboard/sources.md` file listing all ingested sources:

```markdown
# Source Registry

| ID | Type | Title | Added | Notes |
|----|------|-------|-------|-------|
| biology-2e | textbook | OpenStax Biology 2e | 2026-04-06 | 47 chapters, 8 units |
| metabolism-review-2024 | paper | Metabolic Pathways Review | 2026-04-08 | 3 new notes, 5 updated |
```

---

## Mode Detection

1. **Check for project markers**: `package.json`, `pom.xml`, `build.gradle`, `Cargo.toml`, `go.mod`, `Makefile`, `*.sln`, `pyproject.toml`, `setup.py`, `Gemfile`
2. **If any marker found** → **Codebase Mode**
3. **If no marker found** → **Document Mode**
4. **Tie-break**: `.git/` alone with no source files → Document Mode
5. Announce detected mode and confirm with user.

---

## Document Mode

> Templates: [templates.md](references/templates.md)

### Phase D1: Source Discovery & Extraction

1. Scan for `*.pdf`, `*.txt`, `*.md`, `*.html`, `*.epub`.
2. Extract PDFs with `pdftotext`.
3. Build verified mapping: `{ source_file → actual_topics → page_ranges }`.

### Phase D2: Content Analysis

1. Identify topic hierarchy.
2. Separate concept content vs practice questions.
3. Map dependencies between topics.
4. **Full topic checklist** — every topic/subtopic listed.

### Phase D3: Tag Standard

English, lowercase, kebab-case. Registry only.

### Phase D4: Vault Structure

Create `StudyVault/` with numbered folders per templates.md.

### Phase D5: Dashboard Creation

Create `00-Dashboard/` with MOC, Quick Reference, Exam Traps.
**Critical**: H1 MUST be `# {Subject} Study Map`.

### Phase D6: Concept Notes

Per templates.md. YAML frontmatter: `source_pdf`, `part`, `keywords`.

### Phase D7: Practice Questions

8+ questions per topic. Answers in fold callouts.

### Phase D8: Interlinking

`## Related Notes` on everything. Cross-link concept ↔ practice.

### Phase D9: Self-Review

Verify against quality-checklist.md. Fix until all checks pass.

---

## Codebase Mode

> Full workflow: [codebase-workflow.md](references/codebase-workflow.md)
> Templates: [codebase-templates.md](references/codebase-templates.md)

| Phase | Name | Key Action |
|-------|------|------------|
| C1 | Project Exploration | Scan files, detect stack, read entry points |
| C2 | Architecture Analysis | Patterns, request flow, module boundaries |
| C3 | Tag Standard | `#arch-*`, `#module-*`, `#pattern-*`, `#api-*` |
| C4 | Vault Structure | Dashboard, Architecture, per-module, DevOps, Exercises |
| C5 | Dashboard | MOC + Quick Reference + Getting Started |
| C6 | Module Notes | Purpose, Key Files, Interface, Flow, Dependencies |
| C7 | Onboarding Exercises | Code reading, config, debugging, extension (5+/module) |
| C8 | Interlinking | Cross-link everything |
| C9 | Self-Review | Quality checklist verification |

---

## Language

Match source material language. Tags/keywords always English.
