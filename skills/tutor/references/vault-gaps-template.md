# Vault Gaps — {Subject}

_Tracks untested depth per node across FR sessions. Updated after every FR evaluation._
_Gaps persist here so the system remembers what has and hasn't been tested._

## Format

| Node | Gap Topic | Sessions Since Logged | Last Offered | Status |
|------|-----------|----------------------|--------------|--------|

### Status Key
- **UNTESTED** — Never asked about, logged from scope contract vault_gaps
- **OFFERED** — Suggested to student as depth dive, not yet taken
- **TESTED** — Student was asked about this in a subsequent scoped question
- **ABSORBED** — Student addressed voluntarily (bonus coverage) without being asked

### Auto-Suggestion Rules

1. When a student scores 🟢 or 🌟, check this file for UNTESTED gaps on the same node
2. Suggest the top 2 gaps by relevance (prefer gaps with high node centrality)
3. If student accepts, create a new scoped question targeting those gaps specifically
4. When a gap is tested via a new question, update status to TESTED
5. When a student voluntarily covers a gap (bonus_vault_gaps_addressed), mark ABSORBED
