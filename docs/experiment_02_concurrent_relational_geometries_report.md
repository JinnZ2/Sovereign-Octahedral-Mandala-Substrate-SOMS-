# SOMS Experiment 02 — Concurrent Relational Geometries

**Author:** Manus AI

**Date:** 2026-09-09

**Baseline:** Experiment 01 at `eb57c6d430f176bf762a8a760c9fa3321e6e71fd`

**Branch:** `experiment/02-concurrent-relational-geometries`

**Commit:** `4feb9e80bb8db8f07b5836c1898af1d46b1e3577`

## Conclusion

Experiment 02 measured each state transformation under five independently callable geometries. The same transformation produced different relational profiles. No geometries were combined into a universal score.[1] [2] Experiment 01 remained frozen at its specified baseline.[3]

The critical global cyclic transformation produced zero displacement under G2 cyclic and G3 angular geometry, but nonzero displacement under G1 numeric, G4 Gray-code, and G6 Cayley geometry. G5 Mandala geometry was reported as unavailable because the existing `MandalaMap` does not define a unique state-to-position relation for an arbitrary state vector.

Experiment 01 remained unchanged and passed. Experiment 02 passed independently. The integrated repository suite passed without regressions.

## Geometry Availability

Each available relation constructs an `8 × 8` pairwise matrix. Raw relational displacement is the Frobenius norm of the difference between the previous and current matrices. Per-geometry similarity is `1 - D / (8 × M)`, where `D` is raw displacement and `M` is that geometry's maximum pairwise separation over states `0..7`. Values are bounded to `[0,1]`.[2]

| Geometry | Availability | Independent relation | Raw unit | Maximum pair separation |
|---|---|---|---|---:|
| G1 — Numeric state | Available | `abs(a - b)` | Integer label steps | 7 |
| G2 — Cyclic octahedral | Available | `min(abs(a-b), 8-abs(a-b))` | Cyclic steps | 4 |
| G3 — Angular | Available | Minimum circular separation between existing angles `0°,45°,...,315°` | Degrees | 180 |
| G4 — Gray code | Available | Hamming distance from the existing `GRAY_TRANSITION_TABLE` | Bits | 3 |
| G5 — Mandala | N/A | No unique state-to-position mapping is defined for arbitrary state vectors | N/A | N/A |
| G6 — Cayley/group | Available | Existing Cayley distance between classical-state embeddings | Cayley steps | 5 |

G5 was not implemented. `MandalaMap` repeats state labels on multiple rings. Selecting one coordinate per state would require an unsupported ring or scale choice.

## Transformations

The initial state was `S0 = [0,1,2,3,4,5,6,7]`.

| Case | Current state | Definition |
|---|---|---|
| A | `[0,1,2,3,4,5,6,7]` | No transformation |
| B | `[1,2,3,4,5,6,7,0]` | Global cyclic shift `x -> (x+1) mod 8` |
| C | `[1,1,2,3,4,5,6,7]` | Single-component perturbation |
| D | `[0,2,2,4,4,6,6,0]` | Multiple nonuniform perturbations |
| E | `[2,5,1,7,0,6,4,3]` | Global permutation; every component changed |
| Fk | First `k` entries shifted by `+1 mod 8` | Progressive trajectory from F0 through F8 |

## Layer 1 — Observations

### Cases A–E: Raw Displacements

`Component Δ` is the Euclidean displacement of the numeric state vector. G1–G6 are raw relational-matrix displacements.

| Case | Changed | Component Δ | G1 Δ | G2 Δ | G3 Δ | G4 Δ | G5 Δ | G6 Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 0/8 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | N/A | 0.000000 |
| B | 8/8 | 7.483315 | 14.966630 | 0.000000 | 0.000000 | 8.000000 | N/A | 10.583005 |
| C | 1/8 | 1.000000 | 3.741657 | 3.741657 | 168.374582 | 3.741657 | N/A | 5.477226 |
| D | 4/8 | 7.211103 | 16.000000 | 5.656854 | 254.558441 | 5.656854 | N/A | 12.328828 |
| E | 8/8 | 8.602325 | 21.354157 | 9.380832 | 422.137418 | 6.324555 | N/A | 9.797959 |

### Cases A–E: Per-Geometry Similarities

| Case | G1 similarity | G2 similarity | G3 similarity | G4 similarity | G5 similarity | G6 similarity |
|---|---:|---:|---:|---:|---:|---:|
| A | 1.000000 | 1.000000 | 1.000000 | 1.000000 | N/A | 1.000000 |
| B | 0.732739 | 1.000000 | 1.000000 | 0.666667 | N/A | 0.735425 |
| C | 0.933185 | 0.883073 | 0.883073 | 0.844098 | N/A | 0.863069 |
| D | 0.714286 | 0.823223 | 0.823223 | 0.764298 | N/A | 0.691779 |
| E | 0.618676 | 0.706849 | 0.706849 | 0.736477 | N/A | 0.755051 |

### Case F: Progressive Raw Displacements

| Step | Changed | Component Δ | G1 Δ | G2 Δ | G3 Δ | G4 Δ | G5 Δ | G6 Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| F0 | 0/8 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | N/A | 0.000000 |
| F1 | 1/8 | 1.000000 | 3.741657 | 3.741657 | 168.374582 | 3.741657 | N/A | 5.477226 |
| F2 | 2/8 | 1.414214 | 4.898979 | 4.898979 | 220.454077 | 4.898979 | N/A | 4.690416 |
| F3 | 3/8 | 1.732051 | 5.477226 | 5.477226 | 246.475151 | 5.477226 | N/A | 5.477226 |
| F4 | 4/8 | 2.000000 | 5.656854 | 5.656854 | 254.558441 | 6.324555 | N/A | 6.782330 |
| F5 | 5/8 | 2.236068 | 5.477226 | 5.477226 | 246.475151 | 6.782330 | N/A | 8.831761 |
| F6 | 6/8 | 2.449490 | 4.898979 | 4.898979 | 220.454077 | 7.483315 | N/A | 10.099505 |
| F7 | 7/8 | 2.645751 | 3.741657 | 3.741657 | 168.374582 | 7.874008 | N/A | 9.797959 |
| F8 | 8/8 | 7.483315 | 14.966630 | 0.000000 | 0.000000 | 8.000000 | N/A | 10.583005 |

### Case F: Progressive Similarities

| Step | G1 similarity | G2 similarity | G3 similarity | G4 similarity | G5 similarity | G6 similarity |
|---|---:|---:|---:|---:|---:|---:|
| F0 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | N/A | 1.000000 |
| F1 | 0.933185 | 0.883073 | 0.883073 | 0.844098 | N/A | 0.863069 |
| F2 | 0.912518 | 0.846907 | 0.846907 | 0.795876 | N/A | 0.882740 |
| F3 | 0.902192 | 0.828837 | 0.828837 | 0.771782 | N/A | 0.863069 |
| F4 | 0.898985 | 0.823223 | 0.823223 | 0.736477 | N/A | 0.830442 |
| F5 | 0.902192 | 0.828837 | 0.828837 | 0.717403 | N/A | 0.779206 |
| F6 | 0.912518 | 0.846907 | 0.846907 | 0.688195 | N/A | 0.747512 |
| F7 | 0.933185 | 0.883073 | 0.883073 | 0.671916 | N/A | 0.755051 |
| F8 | 0.732739 | 1.000000 | 1.000000 | 0.666667 | N/A | 0.735425 |

## Geometry-Divergence Diagnostic

For available geometries, the diagnostic is `|D_Gi - D_Gj|` using raw displacement. These differences are **unit-dependent** because the relations use label steps, cyclic steps, degrees, bits, and Cayley steps. They are numerical comparisons only. They are not scale-independent scores, errors, or assessments of truth.

| Case | G1:G2 | G1:G3 | G1:G4 | G1:G6 | G2:G3 | G2:G4 | G2:G6 | G3:G4 | G3:G6 | G4:G6 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| B | 14.967 | 14.967 | 6.967 | 4.384 | 0.000 | 8.000 | 10.583 | 8.000 | 10.583 | 2.583 |
| C | 0.000 | 164.633 | 0.000 | 1.736 | 164.633 | 0.000 | 1.736 | 164.633 | 162.897 | 1.736 |
| D | 10.343 | 238.558 | 10.343 | 3.671 | 248.902 | 0.000 | 6.672 | 248.902 | 242.230 | 6.672 |
| E | 11.973 | 400.783 | 15.030 | 11.556 | 412.757 | 3.056 | 0.417 | 415.813 | 412.339 | 3.473 |

The accompanying JSON dataset contains all raw measurements, similarities, and all pairwise divergences for A–E and F0–F8.

## Layer 2 — Structural Description

**Invariance was geometry-specific.** G2 and G3 were invariant under the global cyclic shift in B and F8. G1, G4, and G6 were not invariant under that same transformation.

**G2 and G3 were scale-equivalent for these states.** G3 raw displacement was 45 times G2 raw displacement whenever nonzero. Their normalized similarities were therefore identical throughout the experiment. The raw divergence between them records different units rather than different normalized profiles.

**The progressive profiles were non-monotonic for several geometries.** G1, G2, and G3 decreased in displacement after F4 before the final transformation. G6 also varied non-monotonically. G4 displacement increased at every progressive step.

**The Gray and Cayley relations were sensitive to the global label shift.** At F8, G4 and G6 remained displaced even though G2 and G3 returned to zero displacement.

**The global permutation did not produce one common ordering.** In Case E, G6 had the highest normalized similarity, followed by G4, G2/G3, and G1. This is a description of the selected measurements, not a ranking of geometries.

## Unexpected Results

G1 and G2 produced equal raw displacements from F1 through F7, but their normalized similarities differed because their maximum pairwise separations differ. At F8, their raw displacements separated sharply: G1 rose to `14.966630`, while G2 returned to `0`.

G4 did not preserve the complete pairwise Gray-code distance matrix under a global cyclic label shift, even though consecutive states in the canonical sequence are Gray-adjacent. Adjacency along the sequence does not make every cyclic label shift an isometry of the full Hamming-distance matrix.

G6 displacement at F2 was lower than at F1. It then increased non-monotonically across later steps. No monotonic correction or smoothing was applied.

## Test and Isolation Results

| Scope | Result | Notes |
|---|---:|---|
| Experiment 01 | 11 passed | Files match frozen baseline exactly |
| Experiment 02 | 19 passed | Independent module and test set |
| Pre-existing repository tests | 291 passed; 3 warnings | No regressions |
| Complete integrated suite | 321 passed; 3 warnings | No regressions |

The three warnings are existing SciPy deprecation warnings from `tests/test_physics.py`. Experiment 02 introduced no new warnings.

| Change category | Files |
|---|---|
| Added | `src/concurrent_relational_geometries.py`; `tests/test_concurrent_relational_geometries.py` |
| Modified | None |
| Intentionally untouched | Experiment 01 module and tests; existing SOMS behavior; historical documentation and interpretations; package exports; fieldlink configuration |

## Empirical Motivation

The computational result is qualitatively compatible with the general idea that multiple relational organizations can coexist over the same changing substrate: one state transformation produced several concurrent measurements with different invariances and sensitivities. This statement is only a comparison of structural form. The experiment contains no biological model and provides no biological validation.

## Layer 3 — Interpretation

**No semantic interpretation is assigned.** The relational profiles do not establish or assume identity, sovereignty, consciousness, awareness, selfhood, Φ, or persistence of a subject. The experiment shows only that independently defined geometries can produce different measurements for the same transformation.

## References

[1]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/tree/experiment/02-concurrent-relational-geometries "SOMS Experiment 02 branch"
[2]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/4feb9e80bb8db8f07b5836c1898af1d46b1e3577 "SOMS Experiment 02 commit"
[3]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/eb57c6d430f176bf762a8a760c9fa3321e6e71fd "Frozen SOMS Experiment 01 baseline"
