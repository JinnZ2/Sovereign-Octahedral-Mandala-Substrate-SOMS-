# SOMS — Sovereign Octahedral Mandala Substrate

Physics simulation: octahedral-geometry computing via thermodynamic relaxation.
8 octahedral states (3-bit) + FRET 1/r^6 coupling + Fibonacci mandala geometry → ground-state solving.
Dual-pathway engine: angular (continuous sin²) + tensor (discrete eigenvalue L2), α-mixed by problem type.

## Quick Start

```bash
pip install numpy scipy   # dependencies
python -m pytest tests/   # 98 tests
python src/demo.py        # full walkthrough
```

## File Map

```
src/                         # Core library — import via `from src import *`
  octahedral_physics.py      # SOMSEngine: dual-pathway FRET engine, anneal(), relax_step()
  mandala_structure.py       # MandalaMap: Fibonacci φ-scaled 8-petal ring geometry
  phi_calculator.py          # PhiCalculator: integrated information Φ, sovereignty check (Φ>3.0)
  constraint_agent.py        # ConstraintAgent: seed-growth lifecycle (COMPRESSED→EXPANDING→EXPLORING→CONTRACTING)
  octahedral_lookup.py       # GRAY_CODES, OCTAHEDRAL_EIGENVALUES, ALLOWED_TRANSITIONS, phi_stability_score()
  geometric_encoder.py       # GeometricEncoder: GEIS token ↔ binary. Format: [vertex_bits]|[operator][symbol]
  resource_budget.py         # ResourceBudget dataclass
  geometric_map.py           # GeometricMap dataclass
  atlas_loader.py            # load_seed_catalog(), load_synergies(), DUAL_PAIRS, BRIDGE_PAIRS, SYNERGY_ALIASES
  lattice_handshake.py       # OctahedralLattice (CVP handshake), PulseChip (mat-vec hardware), feltscore()
tests/                       # pytest suite (82 tests)
data/GDSII_Coordinates.txt   # 100-cell nanometer fabrication layout
atlas/remote/                # Fieldlink-mounted data from 6 sibling repos (see .fieldlink.json)
  rosetta/                   # Rosetta-Shape-Core: octahedron.json, bridges.json, seed_catalog.json, math_constants.json
  mandala/                   # Mandala-Computing: shapes.json, glyphs.json, connect.json, sensors.json
  living-intelligence/       # Living-Intelligence-DB: synergies.json, expander_rules.json, resonance_sensor.json
  g2b/                       # Geometric-to-Binary: octahedral_state_encoding.json, sensor_suite.json, geobin_bridges.json
  regen/                     # Regenerative-Intelligence-Core: stub JSONs (seed_library, elder_archive, evolution_history)
  resilience/                # Resilience: seed_protocol.py, field_system.py, coupling_matrix.py, geobin_bridge.py, nfs_pipeline.py
```

## Architecture

```
MandalaMap(u,depth) → positions → distance_matrix → SOMSEngine(num_cells, problem_type)
                                                      ├─ angular_energy() (sin² coupling, weight α)
                                                      ├─ tensor_energy()  (eigenvalue L2, weight 1-α)
                                                      ├─ anneal(J, steps, T0) → ground state
                                                      └─ pathway_report(J) → {angular_E, tensor_E, alpha, dominant}

PhiCalculator(orientations) → evaluate_integration() → (phi, is_sovereign)  # sovereign if Φ>3.0

ConstraintAgent: COMPRESSED →bloom→ EXPANDING →explore→ EXPLORING →compress→ CONTRACTING → COMPRESSED
```

## 8-State Encoding

| St | Bin | Gray | Label  | Glyph | Eigenvalues (λ₁,λ₂,λ₃) |
|----|-----|------|--------|-------|--------------------------|
| 0  | 000 | 000  | +x     | ⊕     | 0.33, 0.33, 0.33        |
| 1  | 001 | 001  | -x     | ⊖     | 0.50, 0.50, 0.00        |
| 2  | 010 | 011  | +y     | ⊗     | 0.50, 0.00, 0.50        |
| 3  | 011 | 010  | -y     | ⊘     | 0.00, 0.50, 0.50        |
| 4  | 100 | 110  | +z     | ⊙     | 1.00, 0.00, 0.00        |
| 5  | 101 | 111  | -z     | ⊚     | 0.00, 1.00, 0.00        |
| 6  | 110 | 101  | diag-a | ⊛     | 0.00, 0.00, 1.00        |
| 7  | 111 | 100  | diag-b | ⊜     | 0.50, 0.25, 0.25        |

## Problem Type → α (angular weight)

OPTIMIZATION=0.8, SAT=0.7, TSP=0.6, PROTEIN_FOLDING=0.5, GRAPH_COLORING=0.3, FACTORIZATION=0.2

## Constants

PHI=1.618033988749895, FRET_EXP=6, FRET_CUTOFF=4.854Å, SOVEREIGNTY_THRESHOLD=3.0, TETRAHEDRAL_ANGLE=109.47°

## Fieldlink Ecosystem

7 repos connected via `.fieldlink.json` v3.0 (bidirectional, CC0/MIT):
rosetta-shape-core, mandala-computing, living-intelligence, regenerative-intelligence-core, geometric-to-binary, resilience

Entity namespace: `SHAPE.OCTA`, `CONST.PHI`, `PROTO.MANDALA_COMPUTE`, `PROTO.SEED_GROWTH`
Mount pattern: `atlas/remote/<source-name>/`

## Conventions

- Classes: PascalCase (`SOMSEngine`, `MandalaMap`, `GeometricEncoder`)
- Modules: snake_case (`octahedral_physics.py`)
- Spelling: `octahedral` (never `octohedral`)
- New files go in `src/`, `data/`, `docs/`, or `atlas/`
- Do not break `.fieldlink.json` schema
