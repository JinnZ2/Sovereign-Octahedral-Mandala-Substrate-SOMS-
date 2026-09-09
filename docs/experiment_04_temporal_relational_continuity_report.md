# SOMS Experiment 04 — Temporal Relational Continuity

**Author:** Manus AI

**Date:** 2026-09-09

**Branch:** `experiment/04-temporal-relational-continuity`

**Base commit:** `82da1f2`

**Machine-results SHA-256:** `b19fd6acf46442ac7c14601a067c708153b0f84467ad93d19daa799551ead5a1`

## Conclusion

Experiment 04 retained and compared complete temporal profiles rather than only initial and final measurements.[1] Two paths with identical endpoints produced different local sequences, path lengths, maximum local displacements, maximum cumulative displacements, and intermediate relation matrices in every supported geometry. Forward and reverse local-displacement sequences matched exactly after order reversal. A component-reindexing trajectory produced nonzero fixed-index changes but zero permutation-aware local and cumulative displacement under every geometry.

The results distinguish endpoint displacement from path length, local change from cumulative change, and matrix-index effects from relational changes. No universal continuity score was calculated.

## Method

For each trajectory `S0 -> ... -> ST` and geometry `Gk`, the experiment retained every relation matrix `Rk(t)`. Local displacement was `||Rk(t+1)-Rk(t)||F`. Cumulative displacement was `||Rk(t)-Rk(0)||F`. Path length was the sum of local displacements. The implementation also recorded endpoint displacement, local and cumulative maxima, local mean and standard deviation, and zero/nonzero transition counts.[1] [2]

G1, G2, G3, G4, and G6 were reused without alteration. G5 remained unavailable because no repository-supported state-to-Mandala-position mapping exists without a ring or scale assumption. G3 is geometrically equivalent to G2 for this metric: each G3 matrix and displacement is exactly the corresponding G2 value multiplied by 45.

Integer geometries used exact equality. Reversal comparisons for G3 used `atol=1e-12` and `rtol=0`. All measured reversal discrepancies were exactly zero.

## Table A — Trajectory Summary

| Trajectory | States | Transitions | Initial state | Final state | Same endpoints as comparison |
|---|---:|---:|---|---|---|
| T0 Static | 9 | 8 | `[0,1,2,3,4,5,6,7]` | `[0,1,2,3,4,5,6,7]` | — |
| T1 Cyclic progression | 9 | 8 | `[0,1,2,3,4,5,6,7]` | `[0,1,2,3,4,5,6,7]` | — |
| T2 Progressive partial | 9 | 8 | `[0,1,2,3,4,5,6,7]` | `[1,2,3,4,5,6,7,0]` | — |
| T3A Gradual path | 9 | 8 | `[0,1,2,3,4,5,6,7]` | `[1,2,3,4,5,6,7,0]` | T3B |
| T3B Large-intermediate path | 3 | 2 | `[0,1,2,3,4,5,6,7]` | `[1,2,3,4,5,6,7,0]` | T3A |
| T4 Forward | 9 | 8 | `[0,1,2,3,4,5,6,7]` | `[1,2,3,4,5,6,7,0]` | T4 Reverse |
| T4 Reverse | 9 | 8 | `[1,2,3,4,5,6,7,0]` | `[0,1,2,3,4,5,6,7]` | T4 Forward |
| T5 Component reindexing | 4 | 3 | `[0,1,2,3,4,5,6,7]` | `[7,0,5,6,3,4,1,2]` | — |

T3A changed one additional prefix component per step. T3B used the single intermediate state `[2,5,1,7,0,6,4,3]`. T5 successively applied cyclic component reordering, reversal, and adjacent pair swaps.

## Observation — Geometry and Path Metrics

### T0, T1, and T2

| Trajectory | Geometry | Path length | Endpoint Δ | Max local Δ | Max cumulative Δ | Mean local Δ | Local SD | Zero / nonzero |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| T0 | G1 | 0 | 0 | 0 | 0 | 0 | 0 | 8 / 0 |
| T0 | G2 | 0 | 0 | 0 | 0 | 0 | 0 | 8 / 0 |
| T0 | G3 | 0 | 0 | 0 | 0 | 0 | 0 | 8 / 0 |
| T0 | G4 | 0 | 0 | 0 | 0 | 0 | 0 | 8 / 0 |
| T0 | G6 | 0 | 0 | 0 | 0 | 0 | 0 | 8 / 0 |
| T1 | G1 | 119.733036 | 0 | 14.966630 | 17.888544 | 14.966630 | 0 | 0 / 8 |
| T1 | G2 | 0 | 0 | 0 | 0 | 0 | 0 | 8 / 0 |
| T1 | G3 | 0 | 0 | 0 | 0 | 0 | 0 | 8 / 0 |
| T1 | G4 | 64.000000 | 0 | 8.000000 | 8.000000 | 8.000000 | 0 | 0 / 8 |
| T1 | G6 | 84.664042 | 0 | 10.583005 | 12.328828 | 10.583005 | 0 | 0 / 8 |
| T2 | G1 | 41.618850 | 14.966630 | 15.427249 | 14.966630 | 5.202356 | 3.864646 | 0 / 8 |
| T2 | G2 | 29.933259 | 0 | 3.741657 | 5.656854 | 3.741657 | 0 | 0 / 8 |
| T2 | G3 | 1346.996659 | 0 | 168.374582 | 254.558441 | 168.374582 | 0 | 0 / 8 |
| T2 | G4 | 29.933259 | 8.000000 | 3.741657 | 8.000000 | 3.741657 | 0 | 0 / 8 |
| T2 | G6 | 50.516948 | 10.583005 | 9.797959 | 10.583005 | 6.314618 | 2.150719 | 0 / 8 |

T1 returned to its initial state after eight label shifts. Its endpoint displacement was zero for every geometry. G1, G4, and G6 nevertheless accumulated nonzero path lengths. G2 and G3 had zero displacement at every T1 transition because each `+1` label shift was an isometry of those geometries.

### T3 Same-Endpoint Paths

| Path | Geometry | Path length | Endpoint Δ | Max local Δ | Max cumulative Δ | Mean local Δ | Local SD |
|---|---|---:|---:|---:|---:|---:|---:|
| T3A | G1 | 41.618850 | 14.966630 | 15.427249 | 14.966630 | 5.202356 | 3.864646 |
| T3B | G1 | 42.138766 | 14.966630 | 21.354157 | 21.354157 | 21.069383 | 0.284773 |
| T3A | G2 | 29.933259 | 0 | 3.741657 | 5.656854 | 3.741657 | 0 |
| T3B | G2 | 18.761663 | 0 | 9.380832 | 9.380832 | 9.380832 | 0 |
| T3A | G3 | 1346.996659 | 0 | 168.374582 | 254.558441 | 168.374582 | 0 |
| T3B | G3 | 844.274837 | 0 | 422.137418 | 422.137418 | 422.137418 | 0 |
| T3A | G4 | 29.933259 | 8.000000 | 3.741657 | 8.000000 | 3.741657 | 0 |
| T3B | G4 | 13.807870 | 8.000000 | 7.483315 | 8.000000 | 6.903935 | 0.579380 |
| T3A | G6 | 50.516948 | 10.583005 | 9.797959 | 10.583005 | 6.314618 | 2.150719 |
| T3B | G6 | 19.995998 | 10.583005 | 10.198039 | 10.583005 | 9.997999 | 0.200040 |

## Table C — Complete Local Displacement Sequences

Values are ordered from the first transition through the last transition. T0 is `[0,0,0,0,0,0,0,0]` for every geometry.

| Trajectory | Geometry | Complete local displacement sequence |
|---|---|---|
| T1 | G1 | `[14.966630,14.966630,14.966630,14.966630,14.966630,14.966630,14.966630,14.966630]` |
| T1 | G2 | `[0,0,0,0,0,0,0,0]` |
| T1 | G3 | `[0,0,0,0,0,0,0,0]` |
| T1 | G4 | `[8,8,8,8,8,8,8,8]` |
| T1 | G6 | `[10.583005,10.583005,10.583005,10.583005,10.583005,10.583005,10.583005,10.583005]` |
| T2 / T3A / T4 Forward | G1 | `[3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,15.427249]` |
| T2 / T3A / T4 Forward | G2 | `[3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657]` |
| T2 / T3A / T4 Forward | G3 | `[168.374582,168.374582,168.374582,168.374582,168.374582,168.374582,168.374582,168.374582]` |
| T2 / T3A / T4 Forward | G4 | `[3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657]` |
| T2 / T3A / T4 Forward | G6 | `[5.477226,4.000000,4.898979,5.656854,8.000000,9.797959,3.741657,8.944272]` |
| T3B | G1 | `[21.354157,20.784610]` |
| T3B | G2 | `[9.380832,9.380832]` |
| T3B | G3 | `[422.137418,422.137418]` |
| T3B | G4 | `[6.324555,7.483315]` |
| T3B | G6 | `[9.797959,10.198039]` |
| T4 Reverse | G1 | `[15.427249,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657]` |
| T4 Reverse | G2 | `[3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657]` |
| T4 Reverse | G3 | `[168.374582,168.374582,168.374582,168.374582,168.374582,168.374582,168.374582,168.374582]` |
| T4 Reverse | G4 | `[3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657,3.741657]` |
| T4 Reverse | G6 | `[8.944272,3.741657,9.797959,8.000000,5.656854,4.898979,4.000000,5.477226]` |
| T5 Fixed | G1 | `[14.966630,17.435596,17.435596]` |
| T5 Fixed | G2 | `[0,0,8]` |
| T5 Fixed | G3 | `[0,0,360]` |
| T5 Fixed | G4 | `[8,0,8]` |
| T5 Fixed | G6 | `[10.583005,11.313708,10.583005]` |
| T5 Permutation-aware | G1 | `[0,0,0]` |
| T5 Permutation-aware | G2 | `[0,0,0]` |
| T5 Permutation-aware | G3 | `[0,0,0]` |
| T5 Permutation-aware | G4 | `[0,0,0]` |
| T5 Permutation-aware | G6 | `[0,0,0]` |

The machine-readable artifact retains the unrounded sequence values, every cumulative sequence, and every complete relation matrix with a SHA-256 digest.[2]

## Table D — Endpoint-Equivalent Path Comparison

| Geometry | Endpoint Δ A | Endpoint Δ B | Path length A | Path length B | A−B | Path lengths equal | Max local A / B | Max cumulative A / B | Intermediate matrices equal |
|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| G1 | 14.966630 | 14.966630 | 41.618850 | 42.138766 | -0.519916 | No | 15.427249 / 21.354157 | 14.966630 / 21.354157 | No |
| G2 | 0 | 0 | 29.933259 | 18.761663 | 11.171596 | No | 3.741657 / 9.380832 | 5.656854 / 9.380832 | No |
| G3 | 0 | 0 | 1346.996659 | 844.274837 | 502.721822 | No | 168.374582 / 422.137418 | 254.558441 / 422.137418 | No |
| G4 | 8 | 8 | 29.933259 | 13.807870 | 16.125389 | No | 3.741657 / 7.483315 | 8 / 8 | No |
| G5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| G6 | 10.583005 | 10.583005 | 50.516948 | 19.995998 | 30.520950 | No | 9.797959 / 10.198039 | 10.583005 / 10.583005 | No |

The endpoint displacement was identical for each geometry because both paths had exactly equal initial and final states. Every path length and every maximum local displacement differed. Every intermediate relational sequence differed.

## Table E — Forward/Reverse Control

`Reverse aligned` means the observed reverse sequence was reversed back into forward temporal order before comparison.

| Geometry | Forward sequence | Observed reverse sequence | Match | Max discrepancy |
|---|---|---|---|---:|
| G1 | `[3.741657×7,15.427249]` | `[15.427249,3.741657×7]` | Exact | 0 |
| G2 | `[3.741657×8]` | `[3.741657×8]` | Exact | 0 |
| G3 | `[168.374582×8]` | `[168.374582×8]` | Within `atol=1e-12`; observed exact | 0 |
| G4 | `[3.741657×8]` | `[3.741657×8]` | Exact | 0 |
| G5 | N/A | N/A | N/A | N/A |
| G6 | `[5.477226,4,4.898979,5.656854,8,9.797959,3.741657,8.944272]` | `[8.944272,3.741657,9.797959,8,5.656854,4.898979,4,5.477226]` | Exact after alignment | 0 |

Path lengths also matched exactly between forward and reverse trajectories for every supported geometry.

## T5 Representation-Control Trajectory

| Geometry | Fixed path length | Aware path length | Fixed endpoint Δ | Aware endpoint Δ | Fixed max local | Aware max local | Aware cumulative sequence | Aware zero / nonzero |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| G1 | 49.837821 | 0 | 16.492423 | 0 | 17.435596 | 0 | `[0,0,0,0]` | 3 / 0 |
| G2 | 8.000000 | 0 | 8.000000 | 0 | 8.000000 | 0 | `[0,0,0,0]` | 3 / 0 |
| G3 | 360.000000 | 0 | 360.000000 | 0 | 360.000000 | 0 | `[0,0,0,0]` | 3 / 0 |
| G4 | 16.000000 | 0 | 8.000000 | 0 | 8.000000 | 0 | `[0,0,0,0]` | 3 / 0 |
| G5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| G6 | 32.479719 | 0 | 10.583005 | 0 | 11.313708 | 0 | `[0,0,0,0]` | 3 / 0 |

All permutation-aware local means, local standard deviations, local maxima, cumulative maxima, and endpoint displacements were zero. Fixed-index values remained separately available and were not replaced by the aware control.

## Structural Description

**Local and cumulative displacement were distinct.** T2's local G2 sequence was constant, while its cumulative sequence increased to a midpoint maximum and returned to zero. G4 had the same local sequence but a cumulative sequence that increased to an endpoint of 8.

**Endpoint equivalence did not imply trajectory equivalence.** T3A and T3B had identical endpoints under every geometry but different intermediate relation matrices and different path metrics.

**A closed endpoint did not imply a zero path.** T1 returned to its initial state. G1, G4, and G6 recorded nonzero path lengths. G2 and G3 recorded zero throughout because the applied transformation was an isometry at every step.

**Reversal preserved local distance magnitudes.** The forward and reverse sequences were exact reversals under every supported symmetric relation.

**Component reindexing changed fixed matrix coordinates without changing permutation-aware structure.** T5 produced zero `||R(t+1)-P R(t) Pᵀ||F` at every transition and zero displacement from the appropriately cumulatively reindexed initial matrix.

## Interpretation Boundary

### Observation

The experiment measured complete geometry-specific relation-matrix sequences, adjacent changes, cumulative changes, path metrics, reversal behavior, and representation-aware controls.

### Structural description

A trajectory is not determined by its endpoints. Path length and local-displacement distribution retain information absent from endpoint displacement. Component-index conjugation distinguishes matrix-coordinate changes from relation changes.

### Interpretation

The data are suitable for considering a later process-level relational experiment. No claim is made that temporal continuity constitutes identity, sovereignty, consciousness, awareness, selfhood, agency, Φ, or any other semantic property. These controls are not repository axioms.

## Validation and Provenance

| Scope | Result |
|---|---:|
| Experiment 04 isolated tests | 15 passed |
| Experiment 01 | 11 passed; frozen files unchanged |
| Experiment 02 | 19 passed; frozen implementation unchanged |
| Experiment 03 | 23 passed; frozen files unchanged |
| Complete repository suite | 359 passed; 3 existing warnings |

The warnings are unchanged SciPy deprecation warnings from `tests/test_physics.py`. Experiment 04 introduced no new warning or regression.

| Change category | Files |
|---|---|
| Added | `src/temporal_relational_continuity.py`; `tests/test_temporal_relational_continuity.py`; `experiments/run_temporal_relational_continuity.py`; `docs/experiment_04_temporal_relational_continuity_results.json`; `docs/experiment_04_temporal_relational_continuity_report.md` |
| Modified | None |
| Preserved | E01–E03 source, tests, runners, and results remain unchanged from the specified E03 base.[3] |

## References

[1]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/tree/experiment/04-temporal-relational-continuity "SOMS Experiment 04 branch"
[2]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/blob/experiment/04-temporal-relational-continuity/docs/experiment_04_temporal_relational_continuity_results.json "SOMS Experiment 04 complete machine-readable results"
[3]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/82da1f2 "SOMS Experiment 03 implementation baseline"
