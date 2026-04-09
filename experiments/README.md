# Experiments

Simulations that test the hypotheses underlying SOMS. Each script states
its hypothesis, runs a simulation, and reports whether the results support
or contradict the claim.

**Nothing here proves SOMS "solves" NP-hard problems.** These experiments
validate specific physical mechanisms that the architecture is built on.

## Scripts

| Script | Tests | Status |
|--------|-------|--------|
| `validate_annealer.py` | Core SOMS claims: stochasticity, 1/r^6 coupling, no optimality guarantee, Phi threshold is arbitrary | Ready (numpy/scipy) |
| `firefly_swarm.py` | Stochastic resonance in coupled oscillators — noise helps synchronization at intermediate levels | Ready (numpy/scipy) |
| `constraint_drift.py` | Semantic drift detection: tracks constraint loss when a term's meaning silently changes over decades | Ready (numpy) |
| `thermodynamic_audit.py` | Exergy-weighted impact scoring: detects when "profitable" activities are thermodynamically destructive | Ready (no deps) |
| `fret_quantum_sync.py` | Dipole-coupled qubits: does coherence survive room-temperature noise? | Requires QuTiP |
| `thermal_bridge_quantum.py` | Phonon-assisted energy transfer: noise as co-processor | Requires QuTiP |

## Quick Start

```bash
# Core validation (no extra dependencies beyond numpy/scipy)
cd experiments
python validate_annealer.py

# Firefly stochastic resonance (try different sigma values)
python firefly_swarm.py

# Constraint drift detection
python constraint_drift.py

# Thermodynamic accountability audit
python thermodynamic_audit.py

# Quantum simulations (need QuTiP: pip install qutip)
python fret_quantum_sync.py
python thermal_bridge_quantum.py
```

## What Each Experiment Validates

### validate_annealer.py
Runs 5 tests against the SOMS engine itself:
1. **Stochasticity** — annealing gives different results with different seeds
2. **Non-monotonic energy** — Metropolis correctly accepts uphill moves
3. **1/r^6 coupling** — FRET coupling follows the stated power law
4. **No optimality guarantee** — different runs find different local minima
5. **Phi threshold** — the "sovereignty" threshold 3.0 is a design choice, not physics

### firefly_swarm.py
Tests stochastic resonance (a real phenomenon in nonlinear dynamics):
- `sigma=0.0` — frustrated, partial synchronization
- `sigma=1.2` — stochastic resonance, global sync emerges
- `sigma=2.5` — noise destroys order

The analogy to "time crystals" in Notes.md is poetic but not rigorous.
True time crystals break continuous time-translation symmetry; firefly
phase-locking is driven dissipative synchronization.

### fret_quantum_sync.py
Simulates 3 qubits with XY coupling and Lindblad noise. Tests whether
dipole coupling sustains coherence. **Caveat**: uses dimensionless time
and tuned parameters — does not prove room-temperature quantum computing.

### thermal_bridge_quantum.py
Tests phonon-mediated energy transfer between mismatched qubits.
Noise-assisted transport is a real effect (seen in photosynthetic
complexes), but the parameters here are illustrative, not calibrated
to any specific material system.

## Hypotheses NOT Yet Tested

These ideas from Notes.md need future experiments:

- **Hysteresis in firefly sync** — does the swarm "remember" synchronization
  when noise is ramped back down? (Notes.md line 996)
- **Cuttlefish chromatophore bandgap** — do traveling wave patterns in a 2D
  oscillator grid create momentum bandgaps? (Notes.md line 2017)
- **Bee waggle dance as Floquet decoder** — does a periodically driven RNN
  decode direction better at intermediate noise? (Notes.md line 2073)

## Ground Rules for New Experiments

1. State the hypothesis clearly in the docstring
2. State what a positive AND negative result would mean
3. Do not claim to "solve" NP-hard problems or "prove" quantum advantage
4. Use "heuristic," "approximate," or "empirically" instead of "optimal" or "guaranteed"
5. Cite the Notes.md line range the experiment was extracted from

### constraint_drift.py
Semantic drift detection framework. Tracks how a term's constraints
decay over time (e.g., "sustainable farming" 1985 vs 2024). Includes:
- **VectorTerm** — terms as points in [energy, physical, resonance] space
- **drift detection** — measures what percentage of constraints were dropped
- **bridge test** — can a modern term claim continuity with its historical meaning?
- **risk cascade** — if one constraint fails, what else collapses?

Demo output: "sustainable farming" 2024 has lost 100% of its 1985 constraints.

### thermodynamic_audit.py
Exergy-weighted impact scoring. Replaces money-as-proxy with physics:
- **ThermodynamicHierarchy** — weights by irreplaceability (Magnetic Core=1.0, Money=0.01)
- **DeepAncestryAuditor** — traces impacts down to physical foundation layers
- **InvariantAuditor** — checks if an action accounts for hidden prerequisites

Demo output: a $100M development scores -24.25 when weighted by physics.
