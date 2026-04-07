# Session Trace Visualization

An animated graph visualization that shows how the tutor agent traverses a StudyVault during an FR session. Built for screen recordings, demos, and YouTube content.

---

## What It Shows

A force-directed graph of every concept node in the vault. At rest, the full topology is visible as a dim constellation — unit-colored dots connected by faint lines. When a session trace plays, nodes and edges illuminate as the agent touches them:

- **Scanned nodes** light up when the agent reads the weight table
- **Target node** gets a breathing glow ring when selected
- **Neighbor nodes** illuminate when the agent follows wiki-links for context
- **Edges pulse** with flowing particles during traversal and ripple steps
- **Weight changes** display directly on the node after evaluation
- **Ripple effects** propagate through connected nodes when mastery changes

Everything is cumulative — nodes stay lit once touched, building a map of what the agent read vs. what remains untouched.

---

## Architecture

The visualization is a single self-contained HTML file with no dependencies (vanilla JS + Canvas API).

### Components

1. **Graph Data** — Node list with `id`, `unit`, `label`, `ch` fields. Edge list with `source`/`target` pairs. Extracted directly from the StudyVault's wiki-link structure.

2. **Event Timeline** — An ordered array of session events. Each event has:
   ```js
   {
     t: 0,                    // step index
     phase: "PHASE 1 · ...",  // status pill header
     text: "...",             // status pill description
     light: ["node-id", ...], // nodes to illuminate (cumulative)
     edges: [["src","tgt"]], // edges to activate with particles
     glow: ["node-id"],      // nodes to give active glow ring (current step only)
     color: "#hex",          // accent color for this step
     weight: { id, val }     // optional weight text to display on a node
   }
   ```

3. **Force Layout** — Nodes cluster by unit using gravitational pull toward unit center points arranged in a circle. Soft boundary repulsion (no hard clamping) keeps nodes from pressing against screen edges.

4. **Camera System** — Smooth lerp camera that auto-centers on the centroid of all active (glowing + lit) nodes. The highlighted cluster is always near screen center.

5. **Rendering** — Canvas-based with three visual tiers:
   - **Dormant**: unit-colored at 15% opacity, edges at 6% — dim constellation
   - **Lit (cumulative)**: unit-colored at 40-90% opacity, edges at 15-30%
   - **Glowing (active step)**: full color + animated glow ring + label + weight text

---

## How to Generate for Any Vault

### Step 1: Extract the graph

```python
import os, re, json

VAULT = "/path/to/your/StudyVault"
nodes = []
edges = []

for root, dirs, files in os.walk(VAULT):
    for f in files:
        if f.endswith('.md') and f.startswith('Ch'):
            filepath = os.path.join(root, f)
            name = f.replace('.md', '')
            folder = os.path.basename(root)
            with open(filepath) as fh:
                content = fh.read()
            links = re.findall(r'\[\[(Ch[^\]]+)\]\]', content)
            ch_num = int(re.search(r'Ch(\d+)', name).group(1))
            nodes.append({
                'id': name, 'unit': folder,
                'label': name.split('-', 1)[-1].replace('-', ' ').strip(),
                'ch': ch_num
            })
            for link in links:
                edges.append({'source': name, 'target': link})

# Deduplicate edges
seen = set()
unique = []
for e in edges:
    key = tuple(sorted([e['source'], e['target']]))
    if key not in seen:
        seen.add(key)
        unique.append(e)

json.dump({'nodes': nodes, 'edges': unique}, open('vault_graph.json', 'w'))
```

### Step 2: Build the event timeline

Map your actual FR session to a sequence of events. Standard phases:

| Step | Phase | What to light |
|------|-------|--------------|
| 0 | Load weights | Nothing (or all nodes briefly) |
| 1 | Scan candidates | All candidate nodes for this session |
| 2 | Select target | Target node gets `glow` |
| 3 | Read concept note | Target node in `light` + `glow` |
| 4 | Traverse neighbors | Neighbor nodes in `light`, edges between target and neighbors |
| 5 | Generate scope contract | Target glows, accent color shift |
| 6 | Present question | Target glows |
| 7 | Student answers | Target glows, color = green |
| 8-10 | Evaluators (coverage, depth, misconceptions) | Target glows, neighbors light for depth eval |
| 11 | Synthesis / grade | Target glows, color = grade color |
| 12 | Update weights | Target glows, `weight` field set |
| 13 | Ripple | All connected neighbors in `light` + `edges`, color = purple |
| 14 | Save gaps | Target glows |
| 15 | Complete | Target + key neighbors glow |

### Step 3: Drop data into the template

Replace `graphData` and `events` in the HTML template with your extracted data.

### Step 4: Customize unit colors

```js
const unitColors = {
  "01-Your-Unit-Name": "#hex",
  "02-Another-Unit":   "#hex",
  // ...
};
```

---

## Controls

| Input | Action |
|-------|--------|
| Space / K | Play / Pause |
| ← → | Step backward / forward |
| R | Reset |
| 1-4 keys | Set speed (0.5× to 4×) |
| Click dot | Jump to step |
| Hover node | Tooltip with chapter, unit, state |

---

## Tuning Guide

### Layout

| Parameter | Location | Effect |
|-----------|----------|--------|
| Cluster radius | `Math.min(W,H) * 0.22` | How spread out unit clusters are. Increase for more separation. |
| Soft boundary padding | `pad = 120` | How far from edges nodes are repelled. Increase to push nodes inward. |
| Center gravity | `0.001` multiplier | How strongly nodes pull toward screen center. |
| Unit clustering | `0.008` multiplier | How tightly nodes within a unit stick together. |
| Node repulsion | `500 / d2` | How strongly nodes push apart. Increase for more spacing. |
| Edge spring length | `d - 65` | Rest length of edges. Increase for looser connections. |

### Visuals

| Parameter | Location | Effect |
|-----------|----------|--------|
| Dormant node opacity | `ctx.globalAlpha = 0.15` | Constellation brightness at rest |
| Dormant edge opacity | `rgba(255,255,255,0.06)` | Constellation line brightness |
| Glow ring size | `24 + 7 * Math.sin(t * 3)` | Active node pulse radius |
| Camera lerp speed | `0.04` | How fast camera pans to center on active cluster (0-1, lower = smoother) |
| Step duration | `2200` ms default | Time per step during playback |

### For Video Recording

- Use speed 1× for narrated walkthroughs
- Use speed 0.5× for dramatic effect on key steps (evaluation, ripple)
- Step manually (← →) if you want to pause and explain specific phases
- The ripple step (phase 7) is the most visually dramatic — pause here for emphasis
- Dark background is screen-recording friendly — no chroma key needed

---

## Template

A ready-to-use template is included at `examples/session-trace-template.html`. Replace the `graphData` and `events` objects with your vault data and session trace.
