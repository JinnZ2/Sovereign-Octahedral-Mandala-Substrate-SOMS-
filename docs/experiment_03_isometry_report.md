# SOMS Experiment 03 — Isometry and Representation Controls

**Author:** Manus AI

**Date:** 2026-09-09

**Branch:** `experiment/03-isometry-representation-controls`

**Implementation and machine-results commit:** `82da1f2`

**Machine-results SHA-256:** `3fcf30688b76cb4f2169b11cb21e348327d25481719d52448c81f0b8f8f68ccc`

## Conclusion

Experiment 03 exhaustively separated **state-label isometries** from **component-index reordering**. It evaluated all `8! = 40,320` permutations for each of five supported state geometries and for each of six component vectors.[1] [2]

The state-label automorphism counts were G1 = 2, G2 = 16, G3 = 16, G4 = 48, and G6 = 2. G2 and G3 had identical symmetry sets. The intersection across all five supported geometries contained only the identity permutation.

Every one of the `1,209,600` component-index evaluations passed the permutation-aware comparison `R(S') = P R(S) Pᵀ`. Fixed-index equality counts varied from 2 to 1,152. The experiment therefore directly established that a changed fixed-index matrix does not by itself establish changed relational structure when component indices were reordered.

## Method

The supported state space was `{0,...,7}`. G1 used numeric distance, G2 used cyclic distance, G3 used the existing eight angular values with circular distance, G4 reused the repository's Gray-code distance table, and G6 reused the existing classical-state Cayley embedding. G5 remained unavailable because the repository does not define a unique Mandala position for each state label without a ring or scale choice.[1] [2]

For every state-label permutation `p`, the experiment tested every pair `(a,b)` for preservation of `R[a,b] = R[p(a),p(b)]`. All 40,320 permutations were generated in deterministic lexicographic order. Integer-valued geometries used exact array equality. G3 used `rtol = 0` and an explicit absolute tolerance of `1e-12`; all recorded preserved G3 cases nevertheless had zero numerical displacement.

For component-index permutation `p`, the implementation constructed `S'[i] = S[p(i)]` and a permutation matrix with `P[i,p(i)] = 1`. It then performed two independent comparisons:

1. **Fixed-index control:** `R(S')` versus `R(S)`.
2. **Permutation-aware control:** `R(S')` versus `P R(S) Pᵀ`.

Every comparison recorded equality, Frobenius displacement, and maximum elementwise displacement. The reproducible runner and complete machine-readable output are committed with the experiment.[2]

## Observation — State-Label Symmetries

| Geometry | Permutations tested | Exact automorphisms | Share of S8 | Identity | Global +1 shift | Cyclic shifts present | Reversal | Maximum Frobenius Δ | Maximum element Δ |
|---|---:|---:|---:|---|---|---:|---|---:|---:|
| G1 Numeric | 40,320 | 2 | 0.004960% | Yes | No | 1/8 | Yes | 21.908902 | 6 |
| G2 Cyclic | 40,320 | 16 | 0.039683% | Yes | Yes | 8/8 | Yes | 13.266499 | 3 |
| G3 Angular | 40,320 | 16 | 0.039683% | Yes | Yes | 8/8 | Yes | 596.992462 | 135° |
| G4 Gray | 40,320 | 48 | 0.119048% | Yes | No | 4/8 | Yes | 9.797959 | 2 bits |
| G5 Mandala | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| G6 Cayley | 40,320 | 2 | 0.004960% | Yes | No | 1/8 | No | 14.142136 | 4 steps |

G4 preserved cyclic offsets `0`, `2`, `4`, and `6`, but not odd offsets. G1 preserved the identity and reversal. G6 preserved the identity and the label swap `(4 5)`; it did not preserve reversal.

The measured permutation-order distributions were:

| Geometry | Automorphism order distribution |
|---|---|
| G1 | order 1: 1; order 2: 1 |
| G2 | order 1: 1; order 2: 9; order 4: 2; order 8: 4 |
| G3 | order 1: 1; order 2: 9; order 4: 2; order 8: 4 |
| G4 | order 1: 1; order 2: 19; order 3: 8; order 4: 12; order 6: 8 |
| G6 | order 1: 1; order 2: 1 |

## Observation — Symmetry-Set Comparisons

| Pair | Intersection | Only first | Only second | Equal sets |
|---|---:|---:|---:|---|
| G1:G2 | 2 | 0 | 14 | No |
| G1:G3 | 2 | 0 | 14 | No |
| G1:G4 | 2 | 0 | 46 | No |
| G1:G6 | 1 | 1 | 1 | No |
| G2:G3 | 16 | 0 | 0 | Yes |
| G2:G4 | 8 | 8 | 40 | No |
| G2:G6 | 1 | 15 | 1 | No |
| G3:G4 | 8 | 8 | 40 | No |
| G3:G6 | 1 | 15 | 1 | No |
| G4:G6 | 1 | 47 | 1 | No |

The all-geometry intersection was `{identity}`. G1's two symmetries were contained in G2, G3, and G4, but only its identity was shared with G6.

## Observation — Component-Permutation Counts

Each cell reports `fixed-index equal / permutation-aware equal` out of 40,320 tested component permutations.

| Vector | G1 | G2 | G3 | G4 | G5 | G6 |
|---|---:|---:|---:|---:|---:|---:|
| V0 `[0,1,2,3,4,5,6,7]` | 2 / 40,320 | 16 / 40,320 | 16 / 40,320 | 48 / 40,320 | N/A | 2 / 40,320 |
| V1 `[1,2,3,4,5,6,7,0]` | 2 / 40,320 | 16 / 40,320 | 16 / 40,320 | 48 / 40,320 | N/A | 2 / 40,320 |
| V2 `[1,1,2,3,4,5,6,7]` | 2 / 40,320 | 2 / 40,320 | 2 / 40,320 | 4 / 40,320 | N/A | 4 / 40,320 |
| V3 `[0,2,2,4,4,6,6,0]` | 32 / 40,320 | 128 / 40,320 | 128 / 40,320 | 384 / 40,320 | N/A | 16 / 40,320 |
| V4 `[2,5,1,7,0,6,4,3]` | 2 / 40,320 | 16 / 40,320 | 16 / 40,320 | 48 / 40,320 | N/A | 2 / 40,320 |
| V5 `[0,0,0,0,4,4,4,4]` | 1,152 / 40,320 | 1,152 / 40,320 | 1,152 / 40,320 | 1,152 / 40,320 | N/A | 1,152 / 40,320 |

The maximum permutation-aware Frobenius and elementwise displacements were both exactly `0` for every vector and every supported geometry.

### Fixed-Index Frobenius Displacement Ranges

All minimum values were `0` because the identity permutation was included.

| Vector | G1 maximum | G2 maximum | G3 maximum | G4 maximum | G5 | G6 maximum |
|---|---:|---:|---:|---:|---:|---:|
| V0 | 21.908902 | 13.266499 | 596.992462 | 9.797959 | N/A | 14.142136 |
| V1 | 21.908902 | 13.266499 | 596.992462 | 9.797959 | N/A | 14.142136 |
| V2 | 20.199010 | 13.856406 | 623.538291 | 9.797959 | N/A | 14.422205 |
| V3 | 22.627417 | 16.000000 | 720.000000 | 8.000000 | N/A | 16.970563 |
| V4 | 21.908902 | 13.266499 | 596.992462 | 9.797959 | N/A | 14.142136 |
| V5 | 22.627417 | 22.627417 | 1018.233765 | 11.313708 | N/A | 16.970563 |

### Fixed-Index Maximum Elementwise Displacement

| Vector | G1 | G2 | G3 | G4 | G5 | G6 |
|---|---:|---:|---:|---:|---:|---:|
| V0 | 6 | 3 | 135° | 2 bits | N/A | 4 steps |
| V1 | 6 | 3 | 135° | 2 bits | N/A | 4 steps |
| V2 | 6 | 4 | 180° | 3 bits | N/A | 5 steps |
| V3 | 6 | 4 | 180° | 2 bits | N/A | 4 steps |
| V4 | 6 | 3 | 135° | 2 bits | N/A | 4 steps |
| V5 | 4 | 4 | 180° | 2 bits | N/A | 3 steps |

The JSON artifact additionally records the fixed-index mean Frobenius displacement, every named identity/cyclic/reversal comparison, and all automorphism permutations.

## E02 Global Cyclic-Shift Control

The E02 vector `[1,2,3,4,5,6,7,0]` can be described in two distinct ways when starting from the canonical vector: as the state-label mapping `x -> (x+1) mod 8`, or as a cyclic component-index reordering. These descriptions were evaluated separately.

| Geometry | Label isometry | Label Frobenius Δ | Label max Δ | Fixed-index equal | Fixed Frobenius Δ | Permutation-aware equal | Aware Frobenius Δ | Classification |
|---|---|---:|---:|---|---:|---|---:|---|
| G1 | No | 14.966630 | 6 | No | 14.966630 | Yes | 0 | State-space non-isometry and component-index representation effect |
| G2 | Yes | 0 | 0 | Yes | 0 | Yes | 0 | State-space isometry |
| G3 | Yes | 0 | 0 | Yes | 0 | Yes | 0 | State-space isometry |
| G4 | No | 8.000000 | 2 bits | No | 8.000000 | Yes | 0 | State-space non-isometry and component-index representation effect |
| G5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Unavailable |
| G6 | No | 10.583005 | 3 steps | No | 10.583005 | Yes | 0 | State-space non-isometry and component-index representation effect |

For G1, G4, and G6, the state-label transformation was a genuine non-isometry. The numerically identical final vector could also be produced by component reordering; under that description, the fixed-index matrix changed while the permutation-aware structure was exactly preserved. The result is therefore classified as **both**, depending on which explicitly defined transformation was applied.

For G2 and G3, the `+1` label mapping was an exact state-space isometry. The corresponding canonical-vector component reordering also left the fixed-index matrix unchanged because that reordering is itself a matrix symmetry.

## Structural Description

G2 and G3 had identical symmetry sets because the angular distance matrix is exactly the cyclic distance matrix multiplied by 45. This scale change altered raw displacement units but not exact isometry membership.

G4 had the largest measured symmetry set. Its 48 automorphisms preserved the existing three-bit Hamming-distance structure. Only the even cyclic label shifts were members of this set.

Repeated state values increased fixed-index matrix symmetry. V5 had 1,152 fixed-index-preserving component permutations under every supported geometry. This count reflects permutations within its two four-position blocks and interchange of those blocks under the selected symmetric pairwise relations.

The G6 classical-state embedding admitted only two label automorphisms. Its nonidentity automorphism swapped labels 4 and 5. This symmetry was not shared by G1, G2, G3, or G4.

## Interpretation Boundary

### Observation

The exhaustive enumeration measured distinct state-label symmetry groups. It also measured universal preservation under permutation-aware component reindexing for every tested vector and geometry.

### Structural description

State-label transformations act on relation values. Component-index permutations act on matrix coordinates. Conjugation by the corresponding permutation matrix removes coordinate-order effects and exposes whether the same relational structure remains.

### Interpretation

No broader semantic hypothesis is adopted. The results do not use or establish identity, sovereignty, consciousness, awareness, selfhood, Φ, agency, or persistence. They provide representation controls for later experiments without elevating those controls into repository axioms.

## Validation and Provenance

| Scope | Result |
|---|---:|
| Experiment 03 isolated tests | 23 passed |
| Frozen Experiment 01 tests | 11 passed |
| Frozen Experiment 02 tests | 19 passed |
| Complete repository suite | 344 passed; 3 warnings |
| State-label evaluations | 201,600 |
| Component-index evaluations | 1,209,600 |

The three warnings are unchanged SciPy deprecation warnings from `tests/test_physics.py`. No regression or new warning was observed.

| Change category | Files |
|---|---|
| Added | `src/isometry_controls.py`; `tests/test_isometry_controls.py`; `experiments/run_isometry_controls.py`; `docs/experiment_03_isometry_results.json`; `docs/experiment_03_isometry_report.md` |
| Modified | None |
| Preserved | E01 source and tests match `eb57c6d`.[5] E02 source and tests match `4feb9e8`.[4] Historical documentation and interpretations remain untouched. |

The E02 human- and machine-readable results were committed to the E02 branch at `59bea27ac7be37771082deb8b06ae032a8b5415c` before Experiment 03 began.[3]

## References

[1]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/tree/experiment/03-isometry-representation-controls "SOMS Experiment 03 branch"
[2]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/82da1f2 "SOMS Experiment 03 implementation and machine results"
[3]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/59bea27ac7be37771082deb8b06ae032a8b5415c "Committed SOMS Experiment 02 reports"
[4]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/4feb9e80bb8db8f07b5836c1898af1d46b1e3577 "Frozen SOMS Experiment 02 implementation baseline"
[5]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/eb57c6d430f176bf762a8a760c9fa3321e6e71fd "Frozen SOMS Experiment 01 baseline"
