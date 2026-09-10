# Experiments

Simulations that test the hypotheses underlying SOMS. Each script states
its hypothesis, runs a simulation, and reports whether the results support
or contradict the claim.

**Nothing here proves SOMS "solves" NP-hard problems.** These experiments
validate specific physical mechanisms that the architecture is built on.

## Scripts

| Script | Tests | Status |
|--------|-------|--------|
| `validate_annealer.py` | Core SOMS claims: stochasticity, 1/r^6 coupling, no optimality guarantee, Phi threshold is arbitrary, **T/J scale (random-walk detector)** | Ready (numpy/scipy) |
| `benchmark_sat.py` | MAX-SAT: SOMS vs vanilla SA, with and without the clauses in the energy | Ready (numpy/scipy) |
| `run_symmetry_identifiability.py` | E07a: label-isometry groups, collision classes, L_R = L_sym + L_excess, cross-geometry recovery, negative controls, BranchSet out | Ready (numpy); writes `docs/experiment_07_*` |
| `firefly_swarm.py` | Stochastic resonance in coupled oscillators — does intermediate noise beat zero noise? | Ready (numpy/scipy/matplotlib) |
| `constraint_drift.py` | Semantic drift detection: tracks constraint loss when a term's meaning silently changes over decades | Ready (numpy) |
| `thermodynamic_audit.py` | Exergy-weighted impact scoring: detects when "profitable" activities are thermodynamically destructive | Ready (no deps) |
| `fret_quantum_sync.py` | Dipole-coupled qubits: does coherence survive room-temperature noise? | Requires QuTiP ≥ 5 + matplotlib |
| `thermal_bridge_quantum.py` | Phonon-assisted energy transfer: noise as co-processor (bridge ON vs OFF control) | Requires QuTiP ≥ 5 + matplotlib |

## Quick Start

```bash
# Core validation (no extra dependencies beyond numpy/scipy)
cd experiments
python validate_annealer.py

# Firefly stochastic resonance (single sigma, or sweep R vs sigma)
python firefly_swarm.py 1.2
python firefly_swarm.py --sweep

# MAX-SAT benchmark (three arms, ~30 s)
python benchmark_sat.py

# E07a symmetry / identifiability (from the repo root, ~5 s; regenerates docs/experiment_07_*)
python experiments/run_symmetry_identifiability.py

# Constraint drift detection
python constraint_drift.py

# Thermodynamic accountability audit
python thermodynamic_audit.py

# Quantum simulations (need QuTiP: pip install qutip matplotlib)
python fret_quantum_sync.py
python thermal_bridge_quantum.py
```

Scripts must be run from inside `experiments/` (they add `..` to `sys.path`).
Set `MPLBACKEND=Agg` on a headless machine; plots are saved as PNG next to
the script either way.

## What Each Experiment Validates

### validate_annealer.py
Runs 5 tests against the SOMS engine itself:
1. **Stochasticity** — annealing gives different results with different seeds
2. **Non-monotonic energy** — Metropolis correctly accepts uphill moves
3. **1/r^6 coupling** — FRET coupling follows the stated power law
4. **No optimality guarantee** — different runs find different local minima
5. **Phi threshold** — the "sovereignty" threshold 3.0 is a design choice, not physics

### firefly_swarm.py
Tests stochastic resonance (a real phenomenon in nonlinear dynamics).
`--sweep` runs σ ∈ {0, 0.3, 0.6, 1.2, 2.5} and reports the tail-mean
order parameter R. The hypothesis is supported only if some σ > 0 beats
σ = 0 by a clear margin. With the shipped parameters it is not (see
Results): R falls monotonically with noise.

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

## Results (2026-09, numpy 2.4 / scipy 1.17 / QuTiP 5.3)

Energy-flow view of the whole suite: where each experiment's signal
actually goes, and where it was leaking.

```
                       ┌──────────────────────────────────────────────────┐
  MandalaMap(u=20)  ── │  d = 20..440 units  →  J = 1/d^6 ≤ 1.6e-8         │
                       │  T = 5.0 → 0.01     →  exp(-dE/T) ≈ 1 for all dE  │  ← BOTTLENECK 1
                       │  ⇒ every proposal accepted ⇒ RANDOM WALK          │    (scale mismatch)
                       └──────────────────────────────────────────────────┘
                                          │  fix: d / d_nn  (J_nn = 1)
                                          ▼
  problem (SAT clauses) ──╳──▶ J ──▶ anneal ──▶ readout            ← BOTTLENECK 2
              clauses never enter the energy ⇒ readout is random       (no encoder)
                                          │  fix: + clause penalty in E_local
                                          ▼
                              soms_sat ≈ vanilla SA  (geometry is neutral on MAX-SAT)
```

| Script | Ran before? | Verdict now | What changed |
|--------|-------------|-------------|--------------|
| `validate_annealer.py` | yes, 5/5 "pass" | 6/6, but TEST 6 flags the default setup as a **random walk** | Added acceptance-ratio + E_final/E_random detector. Tests 1, 2, 4 pass for a random walk too (stochastic, non-monotone, spread > 0), so they never caught it. |
| `benchmark_sat.py` | yes | `soms_sat` ≈ `vanilla` (±0.2%); `soms_geo` 94-96% = best-of-100 random | The shipped SOMS arm never saw the clauses. Added a clause-penalty arm (same encoding as `MandalaComputer.encode_sat`) and normalized distances. |
| `firefly_swarm.py` | crashed (matplotlib) | **Hypothesis NOT supported**: R = 0.71 → 0.48 as σ goes 0 → 2.5, no interior peak | Flash impulse was multiplied by `dt` (kick ≤ 0.008 rad), so nothing synced at any σ (R ≈ 0.05). Fixed; added `--sweep`. |
| `fret_quantum_sync.py` | crashed (QuTiP 5 API) | **NOT supported**: coherence peaks at 0.33 (t≈3) then decays to ~1e-7 by t=100; entropy 0.37 | Excitation was prepared in the ground level and the script read the vacuum coherence ρ[0,1] (identically 0). Now uses `basis(2,0)` = excited and reads ρ[|EG⟩,|GE⟩]. |
| `thermal_bridge_quantum.py` | crashed (QuTiP 5 API) | **Supported**: peak qubit-2 population 0.143 (bridge ON) vs 0.080 (OFF) | Same convention bug: it measured the level that spontaneous decay pumps into, so "transfer" happened with the bridge off too. Added the bridge-OFF control. |
| `constraint_drift.py` | yes | Runs; framework demo, not a hypothesis test | Interpretation text hard-coded "0.80" while reporting 100%. Now prints the computed score. |
| `thermodynamic_audit.py` | yes | Runs; framework demo, not a hypothesis test | Unchanged. Weights are hand-picked; there is no falsifiable claim yet. |

### E07a and E09 (added after the run-through)

- `docs/experiment_07_symmetry_identifiability_report.md` — static arm of the
  symmetry/identifiability work order. Headline: the joint (G1,G2,G4,G6)
  relational representation on 4-cell words has 548 collision pairs not
  explained by any joint symmetry (reproducing the E06 count from an
  independent regeneration); every one of them is a label-isometry pair
  under G2 and under G4, and a genuine collision under G1 and G6. G2 and G4
  lose only what their symmetry removes (L_excess = 0); G1 and G6 do not.
  The E06 and E05 artifacts were not reachable; those two controls are
  recorded as blocked, not passed.
- `docs/experiment_09_representation_invariant_quantity.md` — the annealer
  scale finding written as a measured Q(Ax) ≠ Q(x) case: the energy ranking
  is invariant under the distance rescale, the Metropolis procedure at fixed
  T is not.

### What moves the project forward

1. **Fix the coupling/temperature scale in the engine, not just here.**
   The CLAUDE.md quick-start (`MandalaMap(u=20)` + `T_start=5.0`) is the
   random-walk configuration. `src/demo.py` happens to work because it uses
   `u=1`. Options: normalize `dist / d_nn` inside `fret_coupling`, add an
   `r0` reference distance (J = (r0/r)^6), or auto-scale `T_start` from
   the median |dE| of a few trial moves. Any of these turns every
   downstream `anneal()` from a random walk into a search.
2. **Add a problem-energy hook to `SOMSEngine`.** `anneal(j)` only knows
   the geometric J. `benchmark_sat.py` shows the pattern (subclass,
   `_local_energy += clause_penalty`); `MandalaComputer` in the mandala
   mount already has SAT/TSP/coloring/factorization encoders that could
   be lifted into `src/`. Until then the geometry cannot be evaluated on
   any real problem.
3. **Geometry is neutral on MAX-SAT with the naive readout** (state ≥ 4 →
   True). That is a clean negative result. The next test worth running:
   a problem whose structure matches the octahedral states (8-colouring,
   or 3-bit register arithmetic), where the α-mixed angular/tensor
   coupling could plausibly act as more than a regularizer.
4. **Stochastic resonance needs a frustrated zero-noise state.** The
   swarm syncs to R ≈ 0.7 at σ = 0, so there is nothing for noise to
   unlock. To test the hypothesis fairly: bimodal ω, weaker ε, longer λ,
   or a sub-threshold periodic drive, then re-run `--sweep`.
5. **The two QuTiP scripts are now real controlled tests.** The thermal
   bridge result is the only physics hypothesis in the suite that came
   back positive; the FRET coherence one is negative at these rates.
   Both are dimensionless-time toy models; calibrating to a material
   system is the next step if either is going to inform hardware.

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
