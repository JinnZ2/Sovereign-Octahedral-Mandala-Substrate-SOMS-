# SOMS Roadmap — For AI Contributors

## What SOMS Is

A heuristic annealer that uses octahedral geometry (8 states, 3-bit)
and FRET 1/r^6 coupling on a Fibonacci-scaled mandala to search for
low-energy configurations. It does NOT solve NP-hard problems in
polynomial time. It IS a novel geometry for structuring energy
landscapes that combinatorial heuristics explore.

## Repo Health (as of 2026-04-09)

- 291 tests passing (`python -m pytest tests/`)
- 6 runnable experiments in `experiments/`
- Physics claims audited and corrected across all docs
- CLAUDE.md provides full file map and architecture

## For AI Agents: Where to Start

### Understand the core in 3 files
```python
from src import MandalaMap, SOMSEngine, OhGroup
# 1. MandalaMap — Fibonacci-spaced cell positions
# 2. SOMSEngine — triple-pathway annealer (angular + tensor + Cayley)
# 3. OhGroup    — the 48-element octahedral symmetry group
```

### Run something immediately
```bash
pip install numpy scipy
python experiments/validate_annealer.py  # 5 empirical tests, <10s
python experiments/constraint_drift.py   # semantic drift demo
python experiments/thermodynamic_audit.py # exergy scoring demo
python -m pytest tests/ -q               # full test suite
```

## Open Work — Prioritized

### P0: Physics & Correctness

- [ ] **Calibrate Phi metric** — `src/phi_calculator.py` uses `exp(1/entropy) * 1.618`
  which is ad-hoc. Either derive a principled formula from IIT literature,
  or rename the metric to avoid confusion with Tononi's Phi.
- [ ] **FRET distance calibration** — the 1/r^6 coupling uses arbitrary distance
  units. Map to real FRET parameters (R0 ~ 5nm, fluorophore-dependent).
- [ ] **Benchmark against known heuristics** — compare SOMS anneal() results
  to simulated annealing on standard benchmark problems (MAX-SAT, TSP
  instances from TSPLIB). Document where octahedral geometry helps vs. hurts.

### P1: Missing Experiments

- [ ] **Firefly hysteresis** — ramp noise up then back down during a single
  simulation. Does the swarm "remember" synchronization? (Notes.md line 996)
- [ ] **Cuttlefish bandgap** — 2D oscillator grid with traveling wave.
  Measure if reflected light shows momentum bandgap. (Notes.md line 2017)
- [ ] **Bee waggle Floquet decoder** — periodically driven RNN that decodes
  direction. Does intermediate noise improve decoding? (Notes.md line 2073)
- [ ] **Constraint drift on real data** — apply `constraint_drift.py` to a real
  dataset (medical guidelines, agricultural policy, AI training data).

### P2: Code Quality

- [ ] **Pin dependencies** — create `requirements.txt` with numpy/scipy versions.
- [ ] **Type hints** — add type annotations to `src/octahedral_physics.py` and
  `src/holographic_engine.py` (the two most-used modules).
- [ ] **Docstrings** — `anneal()`, `renormalization_anneal()`, `cayley_energy()`
  need 2-3 line docstrings stating what they compute and what they guarantee.
- [ ] **Test coverage** — add tests for `experiments/` scripts (import + run
  main functions, assert expected output ranges).

### P3: Architecture

- [ ] **Move constraint_drift into src/** — if the framework proves useful,
  promote from experiments/ to src/ with proper tests.
- [ ] **Thermodynamic audit as a sensor** — wire `ThermodynamicHierarchy` into
  the GeometricBridge sensor suite as a new modality.
- [ ] **Holographic engine benchmarks** — compare `renormalization_anneal()` vs
  flat `anneal()` on same problem. Quantify when multi-scale helps.
- [ ] **Cayley pathway weight** — currently Cayley energy is computed but not
  mixed into the combined energy. Add a `gamma` parameter for 3-way mixing:
  `alpha * angular + beta * tensor + gamma * cayley`.

### P4: Ecosystem & Docs

- [ ] **Notes.md cleanup** — the 4900-line file contains extractable code
  (quantum sims, constraint stubs, case studies). Remaining extractable
  content listed in experiments/README.md "Hypotheses NOT Yet Tested."
- [ ] **CONTRIBUTING.md** — add "no unsubstantiated complexity claims" rule.
- [ ] **Case studies** — extract the hypertension and depression case studies
  from Notes.md (lines 2479-2890) into standalone scripts with real
  constraint vectors.

## Architecture Diagram (for AI orientation)

```
MandalaMap(u, depth)
  └─ positions (Fibonacci phi^d ring spacing)
       └─ distance_matrix
            └─ SOMSEngine.fret_coupling() → J matrix (1/r^6)
                 ├─ angular_energy(J)   ← sin²(θi - θj)     weight α
                 ├─ tensor_energy(J)    ← ||λi - λj||²      weight 1-α
                 ├─ cayley_energy(J)    ← O_h graph distance weight (separate)
                 └─ anneal(J) → Metropolis sweep → energy history

HolographicEngine(mandala)
  └─ build() → rings + entanglement links
       └─ renormalization_anneal(J) → coarse-to-fine solving

OhGroup.instance() → 48-element O_h
  └─ GeometricState.from_classical_state(group, 0..7)
       └─ cayley_distance_to(other) → true geometric distance

experiments/
  ├─ validate_annealer.py      → tests core SOMS claims empirically
  ├─ firefly_swarm.py          → stochastic resonance demo
  ├─ constraint_drift.py       → semantic drift detection framework
  ├─ thermodynamic_audit.py    → exergy-weighted impact scoring
  ├─ fret_quantum_sync.py      → dipole-coupled qubit coherence (QuTiP)
  └─ thermal_bridge_quantum.py → phonon-assisted transfer (QuTiP)
```

## Claims This Repo Makes (Honest Version)

| Claim | Status | Evidence |
|-------|--------|----------|
| 1/r^6 FRET coupling | Correct | `validate_annealer.py` test 3 |
| 8-state octahedral encoding | Correct | Lookup table + O_h group verified |
| Simulated annealing finds low-energy states | Correct (heuristic) | `validate_annealer.py` tests 1,2,4 |
| O(1) for NP-hard problems | **Removed** — was wrong | Fixed in README.md |
| Phi > 3.0 = sovereignty | Design parameter, not physics | `validate_annealer.py` test 5 |
| Stochastic resonance aids synchronization | Real phenomenon | `firefly_swarm.py` |
| Room-temp quantum coherence via FRET | Hypothesis, untested with real parameters | `fret_quantum_sync.py` (illustrative only) |
| Noise-assisted transport | Real phenomenon | `thermal_bridge_quantum.py` |
| Fibonacci spacing prevents local minima | **Corrected** — reduces but doesn't prevent | Fixed in docs/Notes.md |

## How to Contribute Without Breaking Physics

1. Run `python -m pytest tests/` before and after changes
2. Run `python experiments/validate_annealer.py` to check core claims
3. Never claim specific complexity classes without proof
4. Use "heuristic," "approximate," "empirically" — not "optimal," "guaranteed," "solves"
5. New experiments go in `experiments/` with a docstring stating the hypothesis
6. New source code goes in `src/` with tests in `tests/`
