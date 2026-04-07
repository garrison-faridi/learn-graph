#!/usr/bin/env bash
set -euo pipefail

# learn-graph install.sh
# Symlinks skills into ~/.claude/skills/ so Claude Code can find them.
# Usage:
#   bash install.sh          (default: symlink — changes to repo propagate automatically)
#   bash install.sh --copy   (hard copy — standalone, no repo dependency)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"
SKILLS_DST="$HOME/.claude/skills"
MODE="symlink"

if [[ "${1:-}" == "--copy" ]]; then
  MODE="copy"
fi

# ── OS detection for poppler hint ─────────────────────────────────────────────
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
  OS="macos"
elif [[ -f /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  case "${ID:-}" in
    ubuntu|debian) OS="debian" ;;
    fedora|rhel|centos|rocky|almalinux) OS="fedora" ;;
    arch) OS="arch" ;;
    *) OS="linux-other" ;;
  esac
fi

# ── Poppler check ─────────────────────────────────────────────────────────────
echo ""
echo "Checking for poppler (pdftotext)..."
if command -v pdftotext &>/dev/null; then
  echo "  pdftotext found: $(which pdftotext)"
else
  echo "  WARNING: pdftotext not found. PDF ingestion will not work without it."
  case "$OS" in
    macos)       echo "  Install with: brew install poppler" ;;
    debian)      echo "  Install with: sudo apt-get install poppler-utils" ;;
    fedora)      echo "  Install with: sudo dnf install poppler-utils" ;;
    arch)        echo "  Install with: sudo pacman -S poppler" ;;
    linux-other) echo "  Install poppler-utils using your distro's package manager." ;;
    *)           echo "  Could not detect OS. Install poppler manually." ;;
  esac
fi

# ── Create skills destination if needed ──────────────────────────────────────
if [[ ! -d "$SKILLS_DST" ]]; then
  echo ""
  echo "Creating $SKILLS_DST ..."
  mkdir -p "$SKILLS_DST"
fi

# ── Install each skill ────────────────────────────────────────────────────────
SKILLS=("tutor" "tutor-setup")

echo ""
echo "Installing skills ($MODE mode) → $SKILLS_DST"

for skill in "${SKILLS[@]}"; do
  src="$SKILLS_SRC/$skill"
  dst="$SKILLS_DST/$skill"

  if [[ ! -d "$src" ]]; then
    echo "  SKIP: $src not found"
    continue
  fi

  if [[ -e "$dst" || -L "$dst" ]]; then
    echo "  EXISTS: $dst — removing old installation"
    rm -rf "$dst"
  fi

  if [[ "$MODE" == "symlink" ]]; then
    ln -s "$src" "$dst"
    echo "  LINKED: /$skill → $src"
  else
    cp -r "$src" "$dst"
    echo "  COPIED: $src → $dst"
  fi
done

# ── Verify ────────────────────────────────────────────────────────────────────
echo ""
echo "Verification:"
ALL_OK=true
for skill in "${SKILLS[@]}"; do
  skill_md="$SKILLS_DST/$skill/SKILL.md"
  if [[ -f "$skill_md" ]]; then
    echo "  OK   /$skill"
  else
    echo "  FAIL /$skill — SKILL.md not found at $skill_md"
    ALL_OK=false
  fi
done

echo ""
if [[ "$ALL_OK" == "true" ]]; then
  echo "Done. Restart Claude Code and type /tutor to begin."
else
  echo "Installation incomplete. Check the FAIL lines above."
  exit 1
fi
