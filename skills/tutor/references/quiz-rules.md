# MCQ Mode — Session Flow + Quiz Design Rules

This file contains the complete MCQ session workflow (MCQ-3 through MCQ-6) and all quiz
design rules. Read entirely before any MCQ session.

---

## MCQ-3: Build Session Options

Read the dashboard proficiency table. Build context-aware options:

1. If unmeasured areas (⬜) exist → include "Diagnostic" option targeting those areas
2. If weak areas (🟥/🟨) exist → include "Drill weak areas" option naming the weakest area(s)
3. Always include "Choose a section" option so the user can pick any area
4. If all areas are 🟩/🟦 → include "Hard-mode review" option

The user MUST select before proceeding.

## MCQ-4: Build Questions

1. Read markdown files in the target section(s).
2. If drilling a weak area: read `concepts/{area}.md` → find 🔴 unresolved concepts.
   Rephrase those concepts in new contexts — never repeat the exact same question.
3. Craft exactly 4 questions following the design rules below. Zero hints allowed.

## MCQ-5: Present Quiz

Present 4 questions with 4 options each:
- Neutral descriptions, no hints, no "(Recommended)" markers
- Randomize correct answer position every round

## MCQ-6: Grade, Explain, Update Files

1. Show results table (question / correct answer / user answer / result emoji).
2. Explain wrong answers concisely.
3. Update `concepts/{area}.md` — add/update concept rows + error notes.
4. Update dashboard — recalculate per-area stats.
   Badges: 🟥 0-39% · 🟨 40-69% · 🟩 70-89% · 🟦 90-100% · ⬜ no data

### MCQ Concept File Format

```markdown
# {Area Name} — Concept Tracker

| Concept | Attempts | Correct | Last Tested | Status |
|---------|----------|---------|-------------|--------|

### Error Notes
```

### Dashboard Proficiency Table

```markdown
## Proficiency by Area

| Area | Correct | Wrong | Rate | Level | Details |
|------|---------|-------|------|-------|---------|
```

---

## Quiz Design Rules

## Zero-Hint Policy (CRITICAL)

Every question must be answerable ONLY by someone who actually knows the material.

1. **Option descriptions**: NEVER reveal correctness
   - BAD: `label: "stderr"`, `description: "Error output stream used by Cloud Run for error classification"`
   - GOOD: `label: "stderr"`, `description: "Standard error stream"`

2. **No "(Recommended)" tag** on any option

3. **Randomize** correct answer position — never always first or last

4. **Question phrasing**: Ask about behavior/purpose/output, don't hint at the answer
   - BAD: "Which error stream does error() use?"
   - GOOD: "Where does error() method output go?"

5. **Plausible distractors**: Wrong options must be real concepts from the domain, representing common misconceptions

## Question Types

1. **Factual recall**: "What HTTP status code is returned when...?"
2. **Conceptual understanding**: "Why does the system use X pattern?"
3. **Behavioral prediction**: "What happens when X fails?"
4. **Comparison/distinction**: "What is the difference between X and Y?"
5. **Debugging scenario**: "Given this error, what is the most likely cause?"

## Difficulty Balancing

- Diagnostic: easy 40%, medium 40%, hard 20%
- Weak-area drill: medium 30%, hard 70%
- Review: all levels evenly

## Drilling Unresolved Concepts

When targeting 🔴 concepts from concept files:
- Do NOT repeat the exact same question — rephrase in a new context
- Test the same underlying knowledge from a different angle
- E.g., if user confused "400 vs 422", ask a scenario question where they must choose the correct status code for a new situation

## AskUserQuestion Format

- 4 questions per round, 4 options each, single-select
- Header: max 12 chars, "Q1. Topic"

## File Update Protocol

After grading:
1. Update `concepts/{area}.md` — add/update concept rows + error notes
2. Update dashboard — recalculate area stats from concept files
3. Badges: 🟥 0-39% · 🟨 40-69% · 🟩 70-89% · 🟦 90-100% · ⬜ no data

## Language Rule

All file content and output in the user's detected language. Badge emojis are universal.
