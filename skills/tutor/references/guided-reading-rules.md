# GR Mode — Session Flow + Teaching Rules

This file contains the complete Guided Reading session workflow (GR-3 through GR-7) and all
teaching, epistemic, and false friend rules. Read entirely before any GR session.

---

## GR-3: Orientation

1. Check for `00-Dashboard/reading-guide-{source_id}.md` in the vault.
   (In single-source vaults, use `reading-guide.md` without suffix.)
2. If found, present the orientation (domain structure, reference systems, recommended approach).
3. If not found, auto-generate from graph topology scoped to `{active_source}`
   (see Orientation section below) and save.
4. Ask: "Want the full orientation, or ready to dive in?"

## GR-4: Load Reading Path

1. Check for `00-Dashboard/reading-path-{source_id}.md` in the vault.
   (In single-source vaults, use `reading-path.md` without suffix.)
2. **If found**: use the manually curated path.
3. **If not found**: auto-generate from wiki-link topology scoped to `{active_source}` —
   topological sort, interleave foundational with applied, group into phases.
   Save as `00-Dashboard/reading-path-{source_id}.md`.
4. Present the path overview. User can accept, modify, or skip ahead.

## GR-5: Teaching Loop

For each node in the reading path:

1. Read the concept note and its wiki-linked neighbors.
2. Check false friends file — if the current node contains any, alert BEFORE teaching:
   > ⚠️ **False Friend: "{term}"** — {why the everyday meaning is wrong} → {domain meaning}
3. Teach conversationally using vault content as ground truth. Follow epistemic rules below.
4. Invite questions. Respond using vault content + wiki-linked context.
5. After covering the node, offer:
   - **"Next"** — continue to next node in the path
   - **"Quiz me"** — return to SKILL.md Phase 2 Mode Dispatch (MCQ or FR). Scope: all discussed nodes.
   - **"Quiz me on this"** — return to SKILL.md Phase 2 Mode Dispatch, scoped to current node only. After assessment, return to GR path.
   - **"Go deeper"** — explore wiki-linked neighbors beyond the reading path
   - **"Jump to [topic]"** — skip ahead in the path

## GR-6: Readiness Transition

**MANDATORY**: ALL assessment transitions route through SKILL.md Phase 2 Mode Dispatch.
Load the selected mode's reference doc and run its full pipeline (scoring, claim ledger, W(n)).
Do NOT improvise questions within GR mode — GR teaches, it does not assess.

When the learner signals readiness (explicit or implicit — see Readiness Detection below),
return to Phase 2 Mode Dispatch: present MCQ and FR options, let the user choose, then load
the corresponding reference doc and begin that mode's workflow with the full vault.

## GR-7: Session Persistence

1. Mark discussed nodes — update R(n) only, no mastery change:
   ```bash
   python3 skills/tutor/scripts/weight_calc.py discussed <weights_file> <node> --decay
   ```
2. Append to `fr-graph/reading-log.md` (see Session Logging below).

---

## Teaching Rules

These rules govern every Guided Reading session.

---

## Reading Path Generation

### Option A — Manual Path (preferred when available)

A manually curated `00-Dashboard/reading-path.md` defines the teaching sequence. Format:

```markdown
# Reading Path: {Subject}

## Phase 1: {Phase Name}
**Goal**: {what the learner should understand after this phase}
**Pacing**: {slow / normal / fast — affects depth of teaching}

- [[Node-A]] — {why this comes first}
- [[Node-B]] alongside [[Node-C]] — {why these interleave}

## Phase 2: {Phase Name}
**Prerequisite**: Phase 1
**Goal**: {goal}

- [[Node-D]]
- [[Node-E]] — {pacing note: slow down here, dense material}

## Phase 3: ...
```

Key features of a good manual path:
- **Non-linear order**: the best reading order is rarely the source's chapter order
- **Interleaving**: pair foundational concepts with their applications early
- **Pacing notes**: flag where to slow down (dense/counterintuitive material)
- **Phase prerequisites**: which phases depend on which

### Option B — Auto-Generated Path

When no manual path exists, generate from the vault's wiki-link graph:

1. **Compute in-degree** for every node (count incoming `[[wiki-links]]`)
2. **Topological sort** — nodes with zero or low in-degree come first (they depend on nothing)
3. **Interleave** — don't just go linearly. After a foundational node, immediately teach
   one applied neighbor so the learner sees *why* the foundation matters
4. **Group into phases** — 3-5 nodes per phase. Each phase has a coherent theme
5. **Save** as `00-Dashboard/reading-path.md` with the manual format (so the user can edit it)

Interleaving algorithm:
```
for each foundational_node (top 30% by centrality):
  teach foundational_node
  pick highest-connected neighbor NOT yet in path
  teach that neighbor immediately after
  continue with next foundational node
remaining nodes: append in topological order
```

---

## Orientation (Reading Guide)

The reading guide (`00-Dashboard/reading-guide.md`) orients the learner before any teaching.

### What it contains:

1. **Domain scope** — what this subject covers and what it doesn't
2. **Structure overview** — how the knowledge is organized (linear? hierarchical? networked?)
3. **Reference system** — how the source material is cited (page numbers, sections, verse
   numbering, Stephanus pages, etc.)
4. **Genre conventions** — how to read this type of source (dialogue, textbook, treatise,
   code, specification). What's literal vs. figurative? What's the author's rhetorical style?
5. **Recommended approach** — the non-obvious "read this way" advice. E.g., "read the
   conclusion before the methodology" or "the middle section is the hardest — don't start there"

### Auto-generation:

When generating from vault structure:
- Domain scope → from dashboard MOC headings
- Structure → from folder hierarchy and wiki-link density
- Reference system → detect from concept note citations
- Genre conventions → infer from source type (textbook, paper, philosophical text, code)
- Recommended approach → from reading path phase order + centrality analysis

---

## Epistemic Rules

Every claim made during teaching MUST carry provenance. Three levels:

### `[A]` Attested
- Directly from the primary source material
- MUST include citation (page, section, verse, timestamp)
- This is ground truth — grade strictly in assessments
- Example: `[A] The demiurge fashions the cosmos by looking to eternal forms [Tim. 28a-29a]`

### `[S]` Scholarship
- From commentary, secondary sources, or established academic interpretation
- MUST include attribution (author, work, or tradition)
- Grade with awareness that interpretations vary
- Example: `[S] Cornford argues the receptacle is best understood as space, not matter (Plato's Cosmology, 1937)`

### `[I]` Inference
- The teaching agent's own synthesis, connection, or interpretation
- MUST be clearly labeled ("connecting this to...", "my read on this is...", "this suggests...")
- Do NOT grade the student on the agent's inferences — they are not source truth
- Example: `[I] This parallels the modern concept of substrate-independence in philosophy of mind`

### Rules:
1. Never present `[I]` as if it were `[A]`. If you're synthesizing, say so.
2. When sources disagree, present both as `[S]` with attributions — don't pick a winner.
3. If the primary source is ambiguous, say so. Ambiguity is a feature of the text, not a gap.
4. In FR evaluation, `[A]` claims are graded strictly. `[S]` claims accept the student citing
   any credible interpretation. `[I]` claims are not graded (they're the agent's, not the source's).

### In Scope Contracts:

Epistemic tags carry into the scope contract format:

```
SCOPE_CONTRACT:
  scope_claims:
    - "[A] The demiurge uses eternal forms as a model [Tim. 28a]"
    - "[A] The created cosmos is an image of the eternal [Tim. 29b]"
    - "[S] The 'likely story' caveat limits cosmological claims to probability (Burnyeat 2005)"
  vault_gaps:
    - "[A] The world soul is constructed from Same, Different, and Being [Tim. 35a-36b]"
    - "[S] Debate on whether the receptacle is space or matter (Cornford vs. Zeyl)"
```

---

## False Friends

False friends are domain terms that look like ordinary English (or the user's language) but
carry specialized, often counterintuitive meaning in the subject domain.

### File format (`00-Dashboard/false-friends.md`):

```markdown
# False Friends: {Subject}

| Term | Everyday Meaning | Domain Meaning | Why It Matters | Nodes |
|------|-----------------|----------------|----------------|-------|
| psychē | soul (Cartesian, immaterial) | principle of life and self-motion | Plato's psychē is NOT the Christian/Cartesian soul | [[World-Soul]], [[Individual-Soul]] |
| necessity (anankē) | logical necessity | brute physical constraint, the "wandering cause" | Opposite of rational design — it's what resists the demiurge | [[Receptacle]], [[Pre-Cosmic-Chaos]] |
| form (eidos) | an idea in someone's head | eternal, mind-independent pattern | Not subjective — forms exist independently of any thinker | [[Theory-of-Forms]], [[Demiurge]] |
```

### When to alert:

- **Guided Reading**: Alert BEFORE teaching a node that contains a false friend
- **FR mode**: If a student's answer misuses a false friend term, Evaluator 3 (Misconception
  Detector) should flag it specifically and reference the false-friends entry
- **MCQ mode**: Include false friend distractors — wrong answers that use the everyday meaning

### Auto-generation:

During vault build, identify false friends by:
1. Scanning concept notes for terms that appear in both general English and the domain glossary
2. Flagging any term where the source explicitly redefines or qualifies its meaning
3. Checking for terms with known false-friend patterns in the domain (e.g., "fitness" in
   biology, "work" in physics, "argument" in logic, "form" in philosophy)

---

## Teaching Conversation Flow

### Tone
- Conversational, not lecturing. Think "knowledgeable friend explaining over coffee"
- Use the Socratic method: ask questions that lead the learner to discover connections
- Match depth to engagement — if the learner asks surface questions, stay accessible;
  if they probe deeply, go deep

### Structure per node
1. **Hook** — why this concept matters, or a surprising fact that creates curiosity
2. **Core explanation** — the main idea, mechanistically explained with epistemic tags
3. **False friend check** — flag any before the learner can misinterpret
4. **Connection** — link to what was just covered (reading path continuity)
5. **Check-in** — "Make sense? Questions before we move on?"

### Handling student questions
- If the question is about a node NOT yet in the reading path: answer briefly, note that
  it'll be covered in full later, and return to the current node
- If the question reveals a misconception: correct immediately with epistemic precision
  (cite the source, not just "that's wrong")
- If the question goes beyond the vault content: acknowledge the limit honestly. Mark any
  response as `[I]` inference

---

## Readiness Detection

### Explicit signals (transition immediately if requested):
- "Quiz me", "Test me", "I think I get it", "Let's try some questions"

### Implicit signals (suggest transition, don't force):
- Student starts making claims or connections unprompted
- Student corrects a deliberate simplification
- Student asks "what if" or "but doesn't that contradict" questions

### Coverage threshold:
- At 60%+ of reading path nodes discussed, proactively suggest:
  > "We've covered a lot of ground. Want to switch to assessment mode to see what stuck?"
- At 100%, strongly suggest but don't force

### Transition behavior:
- When transitioning to FR: the W(n) graph will show discussed-but-untested nodes with
  updated R(n) but M(n) = 0.50 (default). The priority queue will naturally target
  recently-discussed nodes first.
- When transitioning to MC: build questions from discussed nodes preferentially.

---

## Session Logging

After every Guided Reading session, append to `fr-graph/reading-log.md`:

```markdown
## Session: {date} {time}

**Path progress**: Phase {n}, nodes {covered}/{total}
**Nodes covered**: [[Node-A]], [[Node-B]], [[Node-C]]
**False friends flagged**: {term} at [[Node-X]]
**Student questions**: {brief summary of questions asked}
**Re-explanations**: [[Node-B]] — {what was unclear, what angle worked}
**Pickup point**: Phase {n}, starting at [[Node-D]]
**Notes for next session**: {anything to review or revisit}
```
