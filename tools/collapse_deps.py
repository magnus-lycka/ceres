import json
from pathlib import Path
import sys

from graphviz import Digraph

# run uvx pydeps src/ceres --show-deps > deps.json first,
# then uv run tools/collapse_deps.py 2 (or 3 for one level deeper).

depth = int(sys.argv[1]) if len(sys.argv) > 1 else 2


def trim(name, d):
    parts = name.split('.')
    return '.'.join(parts[:d])


with Path('deps.json').open() as f:
    deps = json.load(f)

edges = set()
for src, info in deps.items():
    if not isinstance(info, dict):
        continue
    s = trim(src, depth)
    if not s.startswith('ceres'):
        continue
    for t in info.get('imports', []):
        t2 = trim(t, depth)
        if t2.startswith('ceres') and s != t2:
            edges.add((s, t2))

g = Digraph()
for s, t in sorted(edges):
    g.edge(s, t)
g.render('pkg_deps', format='svg', view=True)
