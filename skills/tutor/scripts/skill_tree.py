#!/usr/bin/env python3
"""
learn-graph skill tree generator
Builds an interactive, gamified visualization of the knowledge graph.

Reads:  node-weights.md, weight-history.jsonl, learner-stats.json, vault wiki-links
Writes: skill-tree.html (self-contained, no server needed)

Usage:
  python3 skill_tree.py <vault_path>
  python3 skill_tree.py <vault_path> --output /custom/path.html
  python3 skill_tree.py <vault_path> --open
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# ── Tier thresholds ──────────────────────────────────────────────────────────

TIER_COLORS = {
    'locked':      {'bg': '#2d2d44', 'border': '#555577', 'text': '#888888'},
    'struggling':  {'bg': '#e74c3c', 'border': '#c0392b', 'text': '#ff6b6b'},
    'in_progress': {'bg': '#f39c12', 'border': '#e67e22', 'text': '#ffc048'},
    'proficient':  {'bg': '#2ecc71', 'border': '#27ae60', 'text': '#5dff9e'},
    'mastered':    {'bg': '#9b59b6', 'border': '#8e44ad', 'text': '#c39bd3'},
}

LEVELS = [(0, "Novice"), (100, "Student"), (500, "Scholar"),
          (2000, "Master"), (5000, "Grandmaster")]


# ── Parsers ──────────────────────────────────────────────────────────────────

def parse_weights(weights_path):
    nodes = []
    for line in Path(weights_path).read_text().split('\n'):
        line = line.strip()
        if not line.startswith('|') or 'Node' in line or '---' in line:
            continue
        parts = [p.strip() for p in line.split('|')[1:-1]]
        if len(parts) >= 6:
            try:
                nodes.append({
                    'name': parts[0],
                    'C': float(parts[1]), 'M': float(parts[2]),
                    'P': float(parts[3]), 'R': float(parts[4]),
                    'W': float(parts[5]),
                })
            except ValueError:
                continue
    return nodes


def parse_edges(vault_path):
    edges = []
    seen = set()
    for md in Path(vault_path).rglob('*.md'):
        if any(d in md.parts for d in ('fr-graph', '00-Dashboard', 'concepts', '.obsidian')):
            continue
        source = md.stem
        for target in re.findall(r'\[\[([^\]]+)\]\]', md.read_text()):
            key = tuple(sorted([source, target]))
            if key not in seen:
                seen.add(key)
                edges.append({'from': source, 'to': target})
    return edges


def detect_domains(vault_path):
    domains = {}
    vault = Path(vault_path)
    for md in vault.rglob('*.md'):
        if any(d in md.parts for d in ('fr-graph', '00-Dashboard', 'concepts', '.obsidian')):
            continue
        rel = md.relative_to(vault)
        domains[md.stem] = rel.parts[0] if len(rel.parts) > 1 else 'Root'
    return domains


def parse_history(path):
    events = []
    if not Path(path).exists():
        return events
    for line in Path(path).read_text().strip().split('\n'):
        if line.strip():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def parse_stats(path):
    if not Path(path).exists():
        return {"xp": 0, "streak_current": 0, "streak_best": 0,
                "last_session_date": None, "total_sessions": 0}
    return json.loads(Path(path).read_text())


# ── Computed properties ──────────────────────────────────────────────────────

def tier_of(n):
    if n['R'] == 0 and n['P'] == 0:
        return 'locked'
    if n['W'] >= 0.85:
        return 'mastered'
    if n['W'] >= 0.70:
        return 'proficient'
    if n['W'] >= 0.50:
        return 'in_progress'
    return 'struggling'


def get_level(xp):
    name = "Novice"
    for t, n in LEVELS:
        if xp >= t:
            name = n
    nxt = next((t for t, _ in LEVELS if xp < t), None)
    return name, nxt


def detect_bosses(nodes, edges):
    conn = defaultdict(int)
    for e in edges:
        conn[e['from']] += 1
        conn[e['to']] += 1
    return {n['name'] for n in nodes if n['C'] >= 0.80 and conn.get(n['name'], 0) >= 4}


def domain_stats(nodes, domains):
    buckets = defaultdict(list)
    nd = {n['name']: n for n in nodes}
    for name, dom in domains.items():
        if name in nd:
            buckets[dom].append(nd[name])
    out = {}
    for dom, ns in sorted(buckets.items()):
        total = len(ns)
        out[dom] = {
            'total': total,
            'tested': sum(1 for n in ns if n['P'] > 0 or n['R'] > 0),
            'proficient': sum(1 for n in ns if n['W'] >= 0.70),
            'mastered': sum(1 for n in ns if n['W'] >= 0.85),
            'avg_w': round(sum(n['W'] for n in ns) / total, 3) if total else 0,
        }
    return out


# ── HTML generator ───────────────────────────────────────────────────────────

def generate_html(nodes, edges, domains, history, stats, bosses, dstats):
    nd = {n['name']: n for n in nodes}

    # Domain color palette
    udoms = sorted(set(domains.values()))
    dpal = ['#1e3a5f','#5f1e3a','#1e5f3a','#5f3a1e','#3a1e5f','#3a5f1e',
            '#1e5f5f','#5f5f1e','#4a1e5f','#1e4a5f','#5f1e4a','#4a5f1e',
            '#1e5f4a','#5f4a1e','#2e2e5f','#5f2e2e']
    dcol = {d: dpal[i % len(dpal)] for i, d in enumerate(udoms)}

    # Level
    level_name, next_xp = get_level(stats.get('xp', 0))
    xp = stats.get('xp', 0)
    xp_pct = min(100, (xp / next_xp) * 100) if next_xp else 100
    level_emojis = {"Novice": "🌊", "Student": "📚", "Scholar": "🎓",
                    "Master": "⭐", "Grandmaster": "👑"}
    lemoji = level_emojis.get(level_name, "🌊")

    # Build vis.js data
    vis_nodes = []
    for n in nodes:
        t = tier_of(n)
        dom = domains.get(n['name'], 'Unknown')
        boss = n['name'] in bosses
        sz = 15 + n['C'] * 25
        opac = (0.4 + 0.6 * n['R']) if t != 'locked' else 0.35
        tc = TIER_COLORS[t]
        vis_nodes.append({
            'id': n['name'],
            'label': n['name'].replace('-', '\n'),
            'size': round(sz),
            'color': {'background': tc['bg'], 'border': tc['border'],
                      'highlight': {'background': tc['border'], 'border': '#ffffff'}},
            'font': {'color': '#e0e0e0' if t != 'locked' else '#777',
                     'size': 10, 'face': 'Inter, system-ui, sans-serif',
                     'multi': True},
            'borderWidth': 3 if boss else 2,
            'opacity': round(opac, 2),
            'group': dom,
            'shadow': {'enabled': True, 'color': tc['bg'], 'size': 15,
                       'x': 0, 'y': 0} if t == 'mastered' else False,
        })

    vis_edges = []
    for e in edges:
        if e['from'] in nd and e['to'] in nd:
            cross = domains.get(e['from']) != domains.get(e['to'])
            vis_edges.append({
                'from': e['from'], 'to': e['to'],
                'color': {'color': '#6a4a6a' if cross else '#3a3a5a', 'opacity': 0.35},
                'width': 1, 'dashes': cross,
                'smooth': {'type': 'continuous'},
            })

    # Node detail data
    details = {}
    for n in nodes:
        t = tier_of(n)
        dom = domains.get(n['name'], 'Unknown')
        boss = n['name'] in bosses
        nh = [h for h in history if h['node'] == n['name']]
        conns = []
        for e in edges:
            other = None
            if e['from'] == n['name'] and e['to'] in nd:
                other = nd[e['to']]
            elif e['to'] == n['name'] and e['from'] in nd:
                other = nd[e['from']]
            if other:
                conns.append({'name': other['name'], 'tier': tier_of(other)})
        details[n['name']] = {
            'label': n['name'].replace('-', ' '), 'domain': dom,
            'tier': t, 'boss': boss,
            'C': n['C'], 'M': n['M'], 'P': n['P'], 'R': n['R'], 'W': n['W'],
            'stars': '★★★' if n['C'] >= 0.80 else ('★★' if n['C'] >= 0.50 else '★'),
            'history': nh, 'connections': conns,
        }

    # Domain cards HTML
    dom_cards = ''
    for dom, ds in sorted(dstats.items()):
        pct = round((ds['tested'] / ds['total']) * 100) if ds['total'] else 0
        col = dcol.get(dom, '#1a1a3a')
        pretty = dom.replace('-', ' ')
        dom_cards += f'''<div class="domain-card" onclick="filterDomain('{dom}')">
  <div class="domain-name">{pretty}</div>
  <div class="domain-progress"><div class="domain-progress-fill" style="width:{pct}%;background:{col}"></div></div>
  <div class="domain-stats-text">{ds['tested']}/{ds['total']} explored · {ds['proficient']} proficient</div>
</div>\n'''

    tested = sum(1 for n in nodes if n['P'] > 0)
    proficient = sum(1 for n in nodes if n['W'] >= 0.70)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Skill Tree — Learn Graph</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a1a;color:#e0e0e0;font-family:'Inter',system-ui,sans-serif;overflow:hidden;height:100vh}}

#stats-bar{{position:fixed;top:0;left:0;right:0;height:56px;background:linear-gradient(180deg,#12122a,#0d0d20);border-bottom:1px solid #2a2a44;display:flex;align-items:center;padding:0 24px;gap:28px;z-index:100}}
.stat-group{{display:flex;align-items:center;gap:8px}}
.stat-label{{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.5px}}
.stat-value{{font-size:14px;font-weight:600}}
.level-badge{{display:flex;align-items:center;gap:6px;background:#1a1a3a;padding:4px 14px;border-radius:20px;border:1px solid #3a3a5a}}
.level-emoji{{font-size:18px}}
.level-name{{font-weight:600;color:#f0f0f0;font-size:14px}}
.xp-container{{display:flex;align-items:center;gap:8px}}
.xp-bar{{width:140px;height:8px;background:#1a1a3a;border-radius:4px;overflow:hidden}}
.xp-fill{{height:100%;background:linear-gradient(90deg,#9b59b6,#3498db);border-radius:4px;transition:width .5s}}
.xp-text{{font-size:12px;color:#aaa}}
.streak-fire{{font-size:18px}}
.vault-stats{{margin-left:auto;display:flex;gap:20px}}

#domains-panel{{position:fixed;top:56px;left:0;width:240px;bottom:0;background:#0f0f24;border-right:1px solid #2a2a44;padding:16px;overflow-y:auto;z-index:90}}
#domains-panel h3{{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#666;margin-bottom:12px}}
.domain-card{{background:#14142a;border-radius:8px;padding:10px 12px;margin-bottom:6px;border:1px solid #22223a;cursor:pointer;transition:border-color .2s}}
.domain-card:hover,.domain-card.active{{border-color:#5a5a7a}}
.domain-name{{font-size:12px;font-weight:600;color:#c0c0d0;margin-bottom:5px}}
.domain-progress{{height:5px;background:#1a1a30;border-radius:3px;overflow:hidden;margin-bottom:4px}}
.domain-progress-fill{{height:100%;border-radius:3px}}
.domain-stats-text{{font-size:10px;color:#666}}
.domain-show-all{{background:#14142a;border-radius:8px;padding:8px 12px;margin-bottom:6px;border:1px solid #22223a;cursor:pointer;text-align:center;font-size:12px;color:#888;transition:border-color .2s}}
.domain-show-all:hover{{border-color:#5a5a7a;color:#bbb}}

#graph-container{{position:fixed;top:56px;left:240px;right:0;bottom:0}}

#node-detail{{position:fixed;top:56px;right:-380px;width:380px;bottom:0;background:#0f0f24;border-left:1px solid #2a2a44;padding:24px;overflow-y:auto;z-index:95;transition:right .3s ease}}
#node-detail.open{{right:0}}
.detail-close{{position:absolute;top:12px;right:16px;background:none;border:none;color:#666;font-size:20px;cursor:pointer}}
.detail-close:hover{{color:#fff}}
.detail-header{{margin-bottom:16px}}
.detail-title{{font-size:18px;font-weight:700;margin-bottom:2px}}
.detail-domain{{font-size:11px;color:#888}}
.detail-stars{{color:#f39c12;margin-left:6px}}
.tier-badge{{display:inline-block;padding:3px 10px;border-radius:10px;font-size:11px;font-weight:600;margin-bottom:16px}}
.tier-locked{{background:#22223a;color:#888}}
.tier-struggling{{background:#3a1111;color:#e74c3c}}
.tier-in_progress{{background:#3a2a08;color:#f39c12}}
.tier-proficient{{background:#083a18;color:#2ecc71}}
.tier-mastered{{background:#28083a;color:#9b59b6}}
.boss-badge{{display:inline-block;padding:2px 8px;border-radius:6px;font-size:10px;background:#3a2a08;color:#f39c12;margin-left:6px;font-weight:600}}

.weight-section{{margin-bottom:20px}}
.weight-row{{display:flex;align-items:center;gap:8px;margin-bottom:5px}}
.weight-label{{font-size:10px;color:#888;width:55px;text-align:right;text-transform:uppercase}}
.weight-bar{{flex:1;height:7px;background:#1a1a30;border-radius:4px;overflow:hidden}}
.weight-bar-fill{{height:100%;border-radius:4px;transition:width .3s}}
.weight-val{{font-size:12px;font-weight:600;width:36px}}

.section-title{{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#666;margin:16px 0 10px;padding-bottom:4px;border-bottom:1px solid #1a1a30}}
.history-item{{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #14142a;font-size:11px}}
.history-date{{color:#555;width:55px;font-size:10px}}
.history-mode{{padding:1px 6px;border-radius:3px;font-size:9px;font-weight:600}}
.mode-FR{{background:#0e2a42;color:#3498db}}
.mode-micro{{background:#3a2808;color:#f39c12}}
.mode-discussed{{background:#083a18;color:#2ecc71}}
.history-score{{color:#aaa;font-size:10px}}
.history-delta{{margin-left:auto;font-weight:600;font-size:11px}}
.delta-up{{color:#2ecc71}}
.delta-down{{color:#e74c3c}}
.delta-same{{color:#888}}

.conn-item{{display:flex;align-items:center;gap:8px;padding:3px 0;font-size:11px;cursor:pointer}}
.conn-item:hover{{color:#fff}}
.conn-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}

#legend{{position:fixed;bottom:12px;left:256px;display:flex;gap:14px;background:rgba(15,15,36,.92);padding:6px 14px;border-radius:8px;border:1px solid #2a2a44;z-index:50}}
.legend-item{{display:flex;align-items:center;gap:5px;font-size:10px;color:#888}}
.legend-dot{{width:9px;height:9px;border-radius:50%}}

::-webkit-scrollbar{{width:5px}}
::-webkit-scrollbar-track{{background:#0a0a1a}}
::-webkit-scrollbar-thumb{{background:#3a3a5a;border-radius:3px}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 8px rgba(155,89,182,.4)}}50%{{box-shadow:0 0 20px rgba(155,89,182,.7)}}}}
</style>
</head>
<body>

<div id="stats-bar">
  <div class="level-badge">
    <span class="level-emoji">{lemoji}</span>
    <span class="level-name">{level_name}</span>
  </div>
  <div class="xp-container">
    <span class="stat-label">XP</span>
    <div class="xp-bar"><div class="xp-fill" style="width:{xp_pct:.0f}%"></div></div>
    <span class="xp-text">{xp}{'/' + str(next_xp) if next_xp else ''}</span>
  </div>
  <div class="stat-group">
    <span class="streak-fire">🔥</span>
    <span class="stat-value">{stats.get('streak_current', 0)}</span>
    <span class="stat-label">streak</span>
  </div>
  <div class="stat-group">
    <span class="stat-value">{stats.get('total_sessions', 0)}</span>
    <span class="stat-label">sessions</span>
  </div>
  <div class="vault-stats">
    <div class="stat-group">
      <span class="stat-value">{tested}/{len(nodes)}</span>
      <span class="stat-label">tested</span>
    </div>
    <div class="stat-group">
      <span class="stat-value">{proficient}/{len(nodes)}</span>
      <span class="stat-label">proficient</span>
    </div>
  </div>
</div>

<div id="domains-panel">
  <h3>Domains</h3>
  <div class="domain-show-all" onclick="filterDomain(null)">Show All</div>
  {dom_cards}
</div>

<div id="graph-container"></div>

<div id="node-detail">
  <button class="detail-close" onclick="closeDetail()">✕</button>
  <div id="detail-content"></div>
</div>

<div id="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#2d2d44"></div>Locked</div>
  <div class="legend-item"><div class="legend-dot" style="background:#e74c3c"></div>Struggling</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f39c12"></div>In Progress</div>
  <div class="legend-item"><div class="legend-dot" style="background:#2ecc71"></div>Proficient</div>
  <div class="legend-item"><div class="legend-dot" style="background:#9b59b6"></div>Mastered</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f39c12;border:2px solid #fff;width:7px;height:7px"></div>Boss</div>
</div>

<script>
const NODES_DATA = {json.dumps(vis_nodes)};
const EDGES_DATA = {json.dumps(vis_edges)};
const DETAILS = {json.dumps(details)};
const TIER_COLORS = {json.dumps(TIER_COLORS)};
const BOSSES = {json.dumps(list(bosses))};

const container = document.getElementById('graph-container');
const nodes = new vis.DataSet(NODES_DATA);
const edges = new vis.DataSet(EDGES_DATA);
let allNodes = NODES_DATA.map(n => n.id);

const network = new vis.Network(container, {{nodes, edges}}, {{
  physics: {{
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {{ gravitationalConstant: -40, centralGravity: 0.008, springLength: 120, springConstant: 0.04, damping: 0.4 }},
    stabilization: {{ iterations: 200, fit: true }},
  }},
  interaction: {{ hover: true, tooltipDelay: 200, zoomView: true, dragView: true }},
  groups: {json.dumps({d: {'color': {'background': c}} for d, c in dcol.items()})},
  layout: {{ improvedLayout: true }},
}});

// Click → detail panel
network.on('click', function(params) {{
  if (params.nodes.length > 0) {{
    showDetail(params.nodes[0]);
  }} else {{
    closeDetail();
  }}
}});

function showDetail(nodeId) {{
  const d = DETAILS[nodeId];
  if (!d) return;
  const tc = TIER_COLORS[d.tier];
  const panel = document.getElementById('node-detail');
  const content = document.getElementById('detail-content');

  let historyHtml = '';
  if (d.history.length > 0) {{
    d.history.slice().reverse().forEach(h => {{
      const date = h.ts ? h.ts.substring(5, 16).replace('T', ' ') : '—';
      const modeClass = 'mode-' + h.mode;
      const wOld = h.W[0], wNew = h.W[1];
      const delta = wNew - wOld;
      const deltaClass = delta > 0 ? 'delta-up' : (delta < 0 ? 'delta-down' : 'delta-same');
      const deltaStr = delta > 0 ? '+' + delta.toFixed(3) : delta.toFixed(3);
      const scoreStr = h.score !== null ? 'score: ' + h.score.toFixed(2) : '';
      historyHtml += `<div class="history-item">
        <span class="history-date">${{date}}</span>
        <span class="history-mode ${{modeClass}}">${{h.mode.toUpperCase()}}</span>
        <span class="history-score">${{scoreStr}}</span>
        <span class="history-delta ${{deltaClass}}">W ${{deltaStr}}</span>
      </div>`;
    }});
  }} else {{
    historyHtml = '<div style="color:#555;font-size:11px;padding:8px 0">No history yet</div>';
  }}

  let connHtml = '';
  d.connections.forEach(c => {{
    const ct = TIER_COLORS[c.tier];
    connHtml += `<div class="conn-item" onclick="network.selectNodes(['${{c.name}}']);showDetail('${{c.name}}')">
      <div class="conn-dot" style="background:${{ct.bg}}"></div>
      <span>${{c.name.replace(/-/g, ' ')}}</span>
    </div>`;
  }});

  content.innerHTML = `
    <div class="detail-header">
      <div class="detail-title">${{d.label}}<span class="detail-stars"> ${{d.stars}}</span></div>
      <div class="detail-domain">${{d.domain.replace(/-/g, ' ')}}${{d.boss ? '<span class=boss-badge>BOSS</span>' : ''}}</div>
    </div>
    <span class="tier-badge tier-${{d.tier}}">${{d.tier.replace('_', ' ').toUpperCase()}}</span>
    <div class="weight-section">
      <div class="weight-row">
        <span class="weight-label">W(n)</span>
        <div class="weight-bar"><div class="weight-bar-fill" style="width:${{d.W*100}}%;background:${{tc.bg}}"></div></div>
        <span class="weight-val" style="color:${{tc.text}}">${{d.W.toFixed(3)}}</span>
      </div>
      <div class="weight-row">
        <span class="weight-label">Mastery</span>
        <div class="weight-bar"><div class="weight-bar-fill" style="width:${{d.M*100}}%;background:#3498db"></div></div>
        <span class="weight-val">${{d.M.toFixed(2)}}</span>
      </div>
      <div class="weight-row">
        <span class="weight-label">Perf</span>
        <div class="weight-bar"><div class="weight-bar-fill" style="width:${{d.P*100}}%;background:#e67e22"></div></div>
        <span class="weight-val">${{d.P.toFixed(2)}}</span>
      </div>
      <div class="weight-row">
        <span class="weight-label">Recency</span>
        <div class="weight-bar"><div class="weight-bar-fill" style="width:${{d.R*100}}%;background:#1abc9c"></div></div>
        <span class="weight-val">${{d.R.toFixed(2)}}</span>
      </div>
      <div class="weight-row">
        <span class="weight-label">Central</span>
        <div class="weight-bar"><div class="weight-bar-fill" style="width:${{d.C*100}}%;background:#9b59b6"></div></div>
        <span class="weight-val">${{d.C.toFixed(2)}}</span>
      </div>
    </div>
    <div class="section-title">History</div>
    ${{historyHtml}}
    <div class="section-title">Connections (${{d.connections.length}})</div>
    ${{connHtml}}
  `;
  panel.classList.add('open');
}}

function closeDetail() {{
  document.getElementById('node-detail').classList.remove('open');
  network.unselectAll();
}}

function filterDomain(domain) {{
  document.querySelectorAll('.domain-card').forEach(c => c.classList.remove('active'));
  if (!domain) {{
    nodes.update(NODES_DATA.map(n => ({{id: n.id, hidden: false}})));
    edges.update(EDGES_DATA.map(e => ({{id: e.id || (e.from+'-'+e.to), hidden: false}})));
    return;
  }}
  event.target.closest('.domain-card')?.classList.add('active');
  const domainNodes = new Set();
  Object.entries(DETAILS).forEach(([name, d]) => {{
    if (d.domain === domain) domainNodes.add(name);
  }});
  nodes.update(NODES_DATA.map(n => ({{id: n.id, hidden: !domainNodes.has(n.id)}})));
}}

// Keyboard: Escape closes detail
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeDetail(); }});
</script>
</body>
</html>'''


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Generate skill tree visualization')
    parser.add_argument('vault_path', help='Path to StudyVault root')
    parser.add_argument('--output', help='Output HTML path (default: fr-graph/skill-tree.html)')
    parser.add_argument('--open', action='store_true', help='Open in browser after generating')
    args = parser.parse_args()

    vault = Path(args.vault_path)
    fg = vault / 'fr-graph'

    if not fg.exists():
        print(f"Error: {fg} not found", file=sys.stderr)
        sys.exit(1)

    nodes = parse_weights(fg / 'node-weights.md')
    edg = parse_edges(vault)
    domains = detect_domains(vault)
    hist = parse_history(fg / 'weight-history.jsonl')
    stats = parse_stats(fg / 'learner-stats.json')
    bosses = detect_bosses(nodes, edg)
    dstats = domain_stats(nodes, domains)

    html = generate_html(nodes, edg, domains, hist, stats, bosses, dstats)

    out = Path(args.output) if args.output else fg / 'skill-tree.html'
    out.write_text(html)

    # Summary
    tested = sum(1 for n in nodes if n['P'] > 0)
    prof = sum(1 for n in nodes if n['W'] >= 0.70)
    mast = sum(1 for n in nodes if n['W'] >= 0.85)
    level_name, _ = get_level(stats.get('xp', 0))
    print(f"⚔️  Skill Tree Generated")
    print(f"   Nodes: {len(nodes)} ({tested} tested, {prof} proficient, {mast} mastered)")
    print(f"   Domains: {len(dstats)} | Bosses: {len(bosses)}")
    print(f"   Level: {level_name} | XP: {stats.get('xp', 0)} | Streak: {stats.get('streak_current', 0)}")
    print(f"   Written: {out}")

    if args.open:
        import webbrowser
        webbrowser.open(f'file://{out.resolve()}')


if __name__ == '__main__':
    main()
