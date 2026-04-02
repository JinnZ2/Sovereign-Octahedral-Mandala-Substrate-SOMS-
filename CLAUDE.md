# CLAUDE.md — Sovereign Octahedral Mandala Substrate (SOMS)

## Project Overview

SOMS is a **physics simulation framework** for octahedral-geometry computing. It models how problems encoded as geometric energy landscapes can be solved through thermodynamic relaxation on a mandala-structured substrate.

Core thesis: Silicon's 109.47° tetrahedral bond symmetry enables 8-state octahedral tensor logic. FRET (Förster Resonance Energy Transfer) coupling provides O(1) complexity on NP-hard problems through geometric relaxation to ground state.

This repo is a **fieldlink peer** of [Rosetta-Shape-Core](https://github.com/JinnZ2/Rosetta-Shape-Core), connected via `.fieldlink.json`. The octahedron (`SHAPE.OCTA`) is the shared geometric anchor — 8 faces = 8 computational states = 8 sacred petals.

## Tech Stack

- **Language:** Python 3.9+
- **Dependencies:** NumPy
- **Data format:** JSON (fieldlink, atlas)
- **License:** CC0-1.0 (public domain)

## Directory Structure

```
src/
  __init__.py              — Package init, exports all public classes
  octahedral_physics.py    — FRET coupling + energy landscape (SOMSEngine)
  mandala_structure.py     — Fibonacci-scaled 8-petal geometry (MandalaMap)
  phi_calculator.py        — Integrated Information metric Φ (PhiCalculator)
  constraint_agent.py      — Seed-based geometric agent lifecycle (ConstraintAgent)
data/
  GDSII_Coordinates.txt    — 100-cell nanometer layout for fabrication
docs/
  Notes.md                 — Extensive technical documentation and design notes
  MANIFESTO.md             — Philosophical foundation
  CITATIONS.md             — Academic references
  Low-cost-fun.md          — DIY macro-scale experiment instructions
atlas/
  remote/rosetta/          — Mounted data from Rosetta-Shape-Core (via fieldlink)
    octahedron.json        — SHAPE.OCTA definition (8 faces, 12 edges, 6 vertices)
    bridges.json           — Cross-repo bridge map (shapes ↔ sensors ↔ defenses)
    seed_catalog.json      — Canonical seed definitions (5 Platonic solids)
    sacred_geometry.json   — Sacred geometry constants and forms
    math_constants.json    — PHI, PI, E, harmonic ratios
    interaction_ontology.json — DRILL/FUSE/AMPLIFY operations
    id_registry.json       — Namespace → authoritative source mapping
    expand.jsonl           — Transformation rules (EXPAND, STRUCTURE, ALIGN)
  remote/mandala/          — Mounted data from Mandala-Computing (via fieldlink)
    shapes.json            — Geometric primitives, energy model, fractal ring schema
    glyphs.json            — State-to-glyph mappings (⊕⊖⊗⊘⊙⊚⊛⊜)
    connect.json           — Fieldlink handshake protocol v1.0
    sensors.json           — Multi-layer sensor definitions (energy, convergence, quantum)
  remote/living-intelligence/ — Mounted data from Living-Intelligence-Database (via fieldlink)
    octahedral_state.json  — OCTA_STATE entity (8-vertex 3-bit encoding)
    mandala_bloom.json     — MANDALA bloom architecture (φ-radial expansion)
    rosetta_shape_core.json — Cross-domain geometric decoder entity
    synergies.json         — 80+ entity synergy graph (weighted edges)
    expander_rules.json    — 43 inference rules (BLOOM_RESONANCE, GEOMETRIC_COMPUTATION, etc.)
    resonance_sensor.json  — 22-channel parallel-field compositor
  remote/regen/            — Mounted data from Regenerative-Intelligence-Core (via fieldlink)
```

## Common Commands

```bash
# Run simulation (from repo root)
python -c "
from src import SOMSEngine, MandalaMap, PhiCalculator
m = MandalaMap(u=20, depth=3)
e = SOMSEngine(num_cells=len(m.pos))
from scipy.spatial import distance_matrix
d = distance_matrix(m.pos, m.pos)
j = e.fret_coupling(d)
print('Energy:', e.energy_landscape(j))
phi, sov = PhiCalculator(e.orientations).evaluate_integration()
print(f'Phi: {phi}, Sovereign: {sov}')
"
```

## Key Constants

| Constant | Value | Usage |
|----------|-------|-------|
| PHI (φ) | 1.618033988749895 | Fibonacci eigenvalue scaling |
| Octahedral states | 8 (0°–315°, 45° steps) | Computational state space |
| FRET exponent | 6 (1/r^6) | Dipole-dipole coupling decay |
| Sovereignty threshold | Φ > 3.0 | Integrated Information cutoff |
| Tetrahedral angle | 109.47° | Silicon bond symmetry |

## Rosetta-Shape-Core Fieldlink

This repo connects to Rosetta-Shape-Core via `.fieldlink.json`:

| SOMS Concept | Rosetta Entity | Connection |
|---|---|---|
| 8 octahedral states | `SHAPE.OCTA` (8 faces) | Direct 1:1 state mapping |
| Golden Ratio (φ) | `CONST.PHI` | Fibonacci eigenvalue scaling |
| Mandala petals | `PROTO.MANDALA_COMPUTE` | Mandala compute protocol v1.0 |
| Relaxation engine | `PROTO.SEED_GROWTH` | Seed-growth protocol v1.0 |
| FRET coupling | Coupling edge | 1/r^6 weighted edges |

## Key Conventions

- **Class names:** PascalCase — `SOMSEngine`, `MandalaMap`, `PhiCalculator`, `ConstraintAgent`
- **Module names:** snake_case — `octahedral_physics.py`, `mandala_structure.py`
- **Rosetta entity IDs:** dot-namespaced — `SHAPE.OCTA`, `CONST.PHI`, `PROTO.MANDALA_COMPUTE`
- **Fieldlink mounts:** under `atlas/remote/<source-name>/`

## Pipeline (Intended Flow)

```
MandalaMap (geometry) → distance matrix → SOMSEngine (physics)
   ↓                                          ↓
GDSII layout                          energy landscape
                                              ↓
                                    relaxation → ground state
                                              ↓
                                    PhiCalculator → sovereignty check (Φ > 3.0)

ConstraintAgent lifecycle (seed-growth protocol):
  COMPRESSED → bloom(depth) → EXPANDING → explore() → EXPLORING
       ↑                                                    ↓
       └──────────── compress() ← CONTRACTING ←────────────┘
```

## Do Not

- Use `octohedral` (typo) — always `octahedral`
- Use snake_case for class names — always PascalCase
- Break `.fieldlink.json` schema compatibility
- Add files without placing them in the correct directory (`src/`, `data/`, `docs/`)
