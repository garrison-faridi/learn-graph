#!/usr/bin/env python3
"""
learn-graph weight calculator
Deterministic W(n) computation for StudyVault node prioritization.

Replaces LLM-driven arithmetic with a script the agent calls after evaluation.
The LLM runs the evaluator pipeline → gets scores → passes to this script → 
script handles all math and file I/O.

Usage:
  python weight_calc.py update <weights_file> <node> --coverage 0.7 --depth 0.6 --misconception 0.1
  python weight_calc.py update <weights_file> <node> --coverage 0.8 --depth 0.7 --micro
  python weight_calc.py score --coverage 0.7 --depth 0.6 --misconception 0.1
  python weight_calc.py recalc <weights_file>
  python weight_calc.py next <weights_file>
  python weight_calc.py show <weights_file> --top 10
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# === Constants ===
MASTERY_ALPHA = 0.3           # EMA learning rate for mastery updates
MICRO_WEIGHT_MULTIPLIER = 0.3 # Fractional update for micro-assessments
RECENCY_DECAY = 0.15          # Per-session R(n) increase for untested nodes

# W(n) formula coefficients
W_C = 0.25  # Centrality weight
W_M = 0.35  # Mastery gap weight (applied as 1-M)
W_P = 0.20  # Performance weight
W_R = 0.20  # Recency weight


# === Core Math ===

def compute_w(c, m, p, r):
    """W(n) = 0.25·C + 0.35·(1−M) + 0.20·P + 0.20·R"""
    return round(W_C * c + W_M * (1 - m) + W_P * p + W_R * r, 3)


def compute_fr_score(coverage, depth, misconception=0.0):
    """Composite FR score from the three evaluator dimensions.
    Score = 0.45·coverage + 0.40·depth + 0.15·(1 - misconception)"""
    return round(0.45 * coverage + 0.40 * depth + 0.15 * (1 - misconception), 3)


def priority_stars(centrality):
    """Priority stars based on centrality (fixed property, doesn't change)."""
    if centrality >= 0.80:
        return "★★★"
    elif centrality >= 0.50:
        return "★★"
    else:
        return "★"


# === File I/O ===

def parse_weights(path):
    """Parse node-weights.md markdown table into list of node dicts."""
    content = Path(path).read_text()
    nodes = []
    for line in content.split('\n'):
        line = line.strip()
        if not line.startswith('|') or 'Node' in line or '---' in line:
            continue
        parts = [p.strip() for p in line.split('|')[1:-1]]
        if len(parts) >= 6:
            try:
                nodes.append({
                    'name': parts[0],
                    'C': float(parts[1]),
                    'M': float(parts[2]),
                    'P': float(parts[3]),
                    'R': float(parts[4]),
                    'W': float(parts[5]),
                })
            except ValueError:
                continue
    return nodes


def write_weights(path, nodes):
    """Write nodes back to node-weights.md, sorted by W(n) descending."""
    nodes.sort(key=lambda n: (-n['W'], n['name']))
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        '# Node Weight Table\n',
        f'_Last updated: {now}_',
        f'_Formula: W(n) = {W_C}·C(n) + {W_M}·(1−M(n)) + {W_P}·P(n) + {W_R}·R(n)_\n',
        '| Node | C(n) | M(n) | P(n) | R(n) | W(n) | Priority |',
        '|---|---|---|---|---|---|---|',
    ]
    
    for n in nodes:
        stars = priority_stars(n['C'])
        lines.append(
            f"| {n['name']} | {n['C']:.2f} | {n['M']:.2f} | "
            f"{n['P']:.2f} | {n['R']:.2f} | {n['W']:.3f} | {stars} |"
        )
    
    Path(path).write_text('\n'.join(lines) + '\n')


# === Commands ===

def cmd_update(args):
    """Update a node after FR or micro-assessment evaluation."""
    nodes = parse_weights(args.weights_file)
    node = next((n for n in nodes if n['name'] == args.node), None)
    
    if not node:
        print(f"Error: Node '{args.node}' not found in {args.weights_file}", file=sys.stderr)
        sys.exit(1)
    
    # Compute composite score
    score = compute_fr_score(args.coverage, args.depth, args.misconception)
    
    # Determine learning rate (fractional for micro)
    alpha = MASTERY_ALPHA
    label = "Full FR"
    if args.micro:
        alpha *= MICRO_WEIGHT_MULTIPLIER
        label = "Micro-assessment"
    
    # Store old values for reporting
    old = {k: node[k] for k in ('M', 'P', 'R', 'W')}
    
    # Update mastery via EMA
    node['M'] = round(alpha * score + (1 - alpha) * node['M'], 3)
    
    # Update performance (latest score)
    node['P'] = round(score, 3)
    
    # Update recency (just tested = 1.0)
    node['R'] = 1.0
    
    # Recompute W(n)
    node['W'] = compute_w(node['C'], node['M'], node['P'], node['R'])
    
    # Decay recency for all OTHER nodes
    if args.decay:
        for n in nodes:
            if n['name'] != args.node and n['R'] > 0:
                n['R'] = round(max(0, n['R'] - RECENCY_DECAY), 3)
                n['W'] = compute_w(n['C'], n['M'], n['P'], n['R'])
    
    # Write
    write_weights(args.weights_file, nodes)
    
    # Report
    print(f"[{label}] {args.node}")
    print(f"  Evaluator: cov={args.coverage:.2f} dep={args.depth:.2f} mis={args.misconception:.2f}")
    print(f"  Score:     {score:.3f}")
    print(f"  Alpha:     {alpha:.3f}")
    print(f"  M(n):      {old['M']:.3f} → {node['M']:.3f}")
    print(f"  P(n):      {old['P']:.3f} → {node['P']:.3f}")
    print(f"  R(n):      {old['R']:.3f} → {node['R']:.3f}")
    print(f"  W(n):      {old['W']:.3f} → {node['W']:.3f}")
    print(f"  Written:   {args.weights_file}")


def cmd_score(args):
    """Compute FR score without writing anything."""
    score = compute_fr_score(args.coverage, args.depth, args.misconception)
    print(f"{score:.3f}")


def cmd_recalc(args):
    """Recalculate W(n) for all nodes from current component values."""
    nodes = parse_weights(args.weights_file)
    fixes = 0
    for n in nodes:
        correct_w = compute_w(n['C'], n['M'], n['P'], n['R'])
        if abs(n['W'] - correct_w) > 0.001:
            print(f"  Fix: {n['name']}  {n['W']:.3f} → {correct_w:.3f}")
            n['W'] = correct_w
            fixes += 1
    
    write_weights(args.weights_file, nodes)
    print(f"\nRecalculated {len(nodes)} nodes, {fixes} corrections → {args.weights_file}")


def cmd_next(args):
    """Show the highest-priority node(s) to study next."""
    nodes = parse_weights(args.weights_file)
    # Recalculate to ensure accuracy
    for n in nodes:
        n['W'] = compute_w(n['C'], n['M'], n['P'], n['R'])
    nodes.sort(key=lambda n: (-n['W'], n['name']))
    
    top = args.top if hasattr(args, 'top') else 5
    print(f"Top {top} priority nodes:\n")
    print(f"  {'Node':<45} {'W(n)':>6}  {'M(n)':>5}  {'Stars'}")
    print(f"  {'-'*70}")
    for n in nodes[:top]:
        stars = priority_stars(n['C'])
        print(f"  {n['name']:<45} {n['W']:>6.3f}  {n['M']:>5.2f}  {stars}")


def cmd_show(args):
    """Display current weight table."""
    nodes = parse_weights(args.weights_file)
    nodes.sort(key=lambda n: (-n['W'], n['name']))
    
    print(f"\n  {'Node':<45} {'C':>5} {'M':>5} {'P':>5} {'R':>5} {'W':>6}  Pri")
    print(f"  {'-'*80}")
    
    limit = args.top if hasattr(args, 'top') else len(nodes)
    for n in nodes[:limit]:
        stars = priority_stars(n['C'])
        print(f"  {n['name']:<45} {n['C']:>5.2f} {n['M']:>5.2f} {n['P']:>5.2f} {n['R']:>5.2f} {n['W']:>6.3f}  {stars}")
    
    if len(nodes) > limit:
        print(f"\n  ... and {len(nodes) - limit} more nodes")
    
    # Summary stats
    tested = [n for n in nodes if n['P'] > 0]
    avg_m = sum(n['M'] for n in nodes) / len(nodes) if nodes else 0
    print(f"\n  Total: {len(nodes)} nodes | Tested: {len(tested)} | Avg mastery: {avg_m:.2f}")


# === CLI ===

def main():
    parser = argparse.ArgumentParser(
        description='learn-graph weight calculator — deterministic W(n) computation'
    )
    sub = parser.add_subparsers(dest='command', required=True)
    
    # update
    up = sub.add_parser('update', help='Update node after evaluation')
    up.add_argument('weights_file', help='Path to node-weights.md')
    up.add_argument('node', help='Node name (exact match)')
    up.add_argument('--coverage', type=float, required=True, help='Coverage score 0-1')
    up.add_argument('--depth', type=float, required=True, help='Depth score 0-1')
    up.add_argument('--misconception', type=float, default=0.0, help='Misconception penalty 0-1')
    up.add_argument('--micro', action='store_true', help='Micro-assessment (0.3x update)')
    up.add_argument('--decay', action='store_true', help='Decay recency for untested nodes')
    
    # score
    sc = sub.add_parser('score', help='Compute FR score (no file write)')
    sc.add_argument('--coverage', type=float, required=True)
    sc.add_argument('--depth', type=float, required=True)
    sc.add_argument('--misconception', type=float, default=0.0)
    
    # recalc
    rc = sub.add_parser('recalc', help='Recalculate all W(n) from components')
    rc.add_argument('weights_file', help='Path to node-weights.md')
    
    # next
    nx = sub.add_parser('next', help='Show top priority nodes')
    nx.add_argument('weights_file', help='Path to node-weights.md')
    nx.add_argument('--top', type=int, default=5)
    
    # show
    sh = sub.add_parser('show', help='Display weight table')
    sh.add_argument('weights_file', help='Path to node-weights.md')
    sh.add_argument('--top', type=int, default=10)
    
    args = parser.parse_args()
    
    commands = {
        'update': cmd_update,
        'score': cmd_score,
        'recalc': cmd_recalc,
        'next': cmd_next,
        'show': cmd_show,
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()
