# Free-Response Question Rules

These rules govern every question generated in FR mode. Read this file before crafting ANY question.

---

## Question Types

### Type A — Intra-node (Recall/Explain)
**Trigger**: Target node mastery M(n) < 0.4, or first FR session for this node
**Structure**: Single concept, tests definition + mechanism + one implication
**Format**: "Explain X. In your answer, address [mechanism] and [at least one consequence or application]."
**Depth expected**: Mechanistic, not just definitional. Student should state the underlying logic, not just name the thing.

### Type B — Bridge (Compare/Connect)
**Trigger**: M(n) 0.4–0.7, two linked nodes with an edge in the wiki-link graph
**Structure**: Two concepts connected by a causal or comparative relationship
**Format**: "Compare X and Y. Specifically, explain how [linking mechanism] connects them and when you would choose one over the other."
**Depth expected**: Student must articulate the relationship direction, not just describe both in isolation.

### Type C — Synthesis (Analyze/Apply)
**Trigger**: M(n) > 0.7, or explicit "Synthesis challenge" session choice
**Structure**: 3+ concept chain; design, interpret, or analyze a scenario
**Format**: "Given [scenario with data or context], explain what pattern you expect to observe and why, drawing on [concept A], [concept B], and [concept C]."
**Depth expected**: Cross-concept integration with explicit mechanistic reasoning. Quantitative or directional predictions are required where applicable.

---

## Scope Contract (MANDATORY)

Every FR question MUST be accompanied by a **scope contract** — a hidden list of the specific
claims being tested. This contract governs how the evaluator grades the answer.

### How it works:

1. **When crafting the question**, identify 3–6 **scope claims** — the specific factual/mechanistic
   points the question explicitly asks about. These are the ONLY claims the evaluator grades for
   coverage. The question's sub-parts directly map to scope claims.

2. **Also generate a full `vault_gaps` list** — ALL remaining claims from the vault note that are
   NOT in scope. These are tracked but NOT graded. They represent knowledge the student hasn't
   been tested on yet for this node.

3. **Pass both lists to the evaluator.** The evaluator grades against `scope_claims` only. It logs
   `vault_gaps` separately as "untested depth."

### Scope contract format (internal, not shown to student):

```
SCOPE_CONTRACT:
  scope_claims:
    - "[A] DNA is transcribed by RNA polymerase (not DNA polymerase) [p.247]"
    - "[A] Codons are triplets of nucleotides that specify amino acids [p.250]"
    - "[S] The genetic code is nearly universal with minor exceptions (Koonin 2017)"
  vault_gaps:
    - "[A] 5' cap and poly-A tail processing in eukaryotes [p.263]"
    - "[A] tRNA anticodon-codon base pairing at ribosome A/P/E sites [p.258]"
    - "[I] Degeneracy may buffer against point mutations (inference from wobble)"
```

### Epistemic provenance tags

Every scope claim and vault gap SHOULD carry an epistemic tag when the vault supports it:

- **`[A]` Attested** — directly from the primary source, with citation. Grade strictly.
- **`[S]` Scholarship** — from commentary or secondary sources, with attribution.
  Accept any credible interpretation from the student.
- **`[I]` Inference** — agent synthesis or cross-concept connection. Do NOT grade the
  student on inferences — they are the agent's interpretations, not source truth.

If the vault's concept notes don't have epistemic tags, default all claims to `[A]` (assume
primary source) and note this in the evaluation. Epistemic tagging is strongest for
philosophical, historical, and interpretive texts where source vs. commentary matters most.

### Specificity-grading alignment rule:

- **Broad question** (2–3 sub-parts) → 3–4 scope claims → grading is lenient on depth,
  expects breadth. A correct broad answer scores well.
- **Specific question** (targets one mechanism in detail) → 5–6 scope claims → grading
  expects mechanistic depth. Surface-level answers score poorly.
- The question itself MUST signal which mode it's in. If the student should go deep, the
  question says "describe the mechanism in detail" or "explain step by step." If broad,
  it says "describe" or "explain" without depth qualifiers.

### Vault gaps → depth suggestions:

After grading, review the `vault_gaps` list. If the student scored 🟢 or 🌟 on the scoped
question, suggest diving into untested gaps as a follow-up:

> "You nailed the core. Ready to go deeper? I haven't tested you on [gap topic 1]
> or [gap topic 2] yet — want me to drill into those?"

If the student scored 🔴 or 🟡, do NOT suggest new depth — focus on reinforcing the
scoped claims first. Save the gaps for a future session.

Vault gaps are persisted in `fr-graph/vault-gaps.md` per node so the system remembers
what has and hasn't been tested across sessions.

---

## Post-Teaching Micro-Assessment Loop

After the initial FR score and Socratic feedback, the tutor enters a **teaching phase** where
it walks the student through gaps. This phase includes comprehension checkpoints.

### Flow

```
For each gap/concept segment being taught:
  1. Explain the concept segment (concise, mechanistic)
  2. Summarize the key point in 1-2 sentences
  3. Offer: "Quiz me / Keep going / Re-explain"
  
  If QUIZ ME:
    → Generate 1-2 micro-questions scoped to ONLY what was just taught
    → Evaluate with the SAME evaluator pipeline (Coverage + Depth + Accuracy)
    → Score using same weighted formula
    → Apply score as a FRACTIONAL W(n) update (micro-weight multiplier)
    → If score < 0.50: re-teach with different framing, then offer re-quiz
    → If score >= 0.50: move to next segment
  
  If KEEP GOING:
    → Move to next segment (no W(n) adjustment)
  
  If RE-EXPLAIN:
    → Re-teach with different angle/analogy, then re-offer the same 3 options
```

### Micro-Quiz Scope Contracts

Micro-questions follow the same scope contract rules as full FR questions, but narrower:

- **1-2 scope claims** per micro-question (scoped to the segment just taught)
- **Vault gaps** = everything outside the micro-scope (not graded)
- Same evaluator pipeline: Coverage, Depth, Misconception → Synthesis
- Same weighted formula: `0.45 * coverage + 0.40 * depth + 0.15 * (1 - misconception_penalty)`

### Micro-Weight Multiplier

Micro-quiz scores produce a **fractional** W(n) update relative to a full FR:

```
micro_delta = full_FR_delta_formula(micro_score) * MICRO_WEIGHT_MULTIPLIER
```

- **Default MICRO_WEIGHT_MULTIPLIER = 0.3** (tunable per vault)
- This means a micro-quiz that would produce a +0.15 W shift as a full FR instead
  produces +0.045
- Multiple micro-quizzes in a session compound: a student who scores poorly on the
  initial FR but passes all checkpoints gets real, proportional credit

### Why Same Pipeline (Not Binary Pass/Fail)

A flat pass/fail with a fixed bonus discards signal. A student who scores 0.90 on a
micro-quiz demonstrated stronger comprehension than one who scores 0.55 — both should
NOT get the same weight adjustment. The evaluator pipeline preserves that granularity
at every scale.

### Session-End Adjusted Score

After all teaching segments complete:

```
adjusted_W(n) = initial_W(n) + full_FR_delta + sum(all_micro_deltas)
```

This adjusted weight is what gets written to `fr-graph/node-weights.md`.

### Claim Ledger Persistence

After scoring (both full FR and micro-quizzes), write results to the paired tracker file.

#### File convention:

- Concept note: `{unit}/Ch07-Cellular-Respiration.md` (ground truth, content only)
- Tracker file: `concepts/Ch07-Cellular-Respiration-fr.md` (learner state)

#### Frontmatter hook:

Every concept note MUST have a `tracker:` field in its YAML frontmatter pointing to the
paired tracker file:

```yaml
---
title: Cellular Respiration
unit: 02-The-Cell
tracker: concepts/Ch07-Cellular-Respiration-fr.md
---
```

If the `tracker:` field is missing, add it during the first FR session for that node.

#### Reading convention:

When loading a concept note for FR question generation or evaluation, ALWAYS check for
a `tracker:` frontmatter field. If present, read the tracker file BEFORE generating
questions. Use persistent gaps and misconception history to inform question targeting.

**Critical**: The concept note is ground truth. The tracker is learner state. Never treat
student errors logged in the tracker as correct information.

#### Writing convention:

After each FR or micro-quiz evaluation, append a session entry to the tracker file using
the format in `skills/tutor/references/claim-ledger-template.md`. Update the Persistent
Gaps checklist at the top of the file (check off resolved gaps, add new ones).

If no tracker file exists yet, create one from the template.

---

## Universal Rules

1. **Zero hints in the question.** Do not use words that imply the answer direction.
2. **One question per session.** Never stack multiple questions in one prompt.
3. **Name the target node** so the evaluation can assess against the vault note.
4. **No answer key in the question prompt.**
5. **Require mechanism, not just recall.** Every question must include "explain why" or "describe the mechanism" or "what does this imply for."
6. **Type C questions must name the graph nodes** being bridged but must not hint at how they connect.
7. **Quantitative anchoring**: For concepts with formulas, specify "use the relevant formula or statistic in your answer."
8. **Scope contract is mandatory.** Every question must have a scope contract generated before presenting to the student. No question without scoped claims.

---

## Question Quality Checklist

Before presenting a question, verify:
- [ ] No answer-direction hint present
- [ ] Mechanism or "why" is required
- [ ] Target node is recorded (for evaluators)
- [ ] Type classification is correct for current M(n)
- [ ] For Type B/C: neighbor node(s) named but not their relationship
- [ ] Scope contract generated with 3–6 scope claims
- [ ] Vault gaps list generated for untested depth
- [ ] Question specificity matches scope claim count (broad ↔ few, specific ↔ many)
