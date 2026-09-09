# SOMS Experiment 05 — Correspondence and Relational Lineage Controls

**Author:** Manus AI

**Date:** 2026-09-09

**Branch:** `experiment/05-correspondence-relational-lineage`

**Base commit:** `f2f3afe02642762b7442cbfdf266625def969b08`

**Implementation and machine-results commit:** `ec224dd`

**Machine-results SHA-256:** `6f05d2ddcc2581d50e8008ef0cb1b9e34392b8f72d40e3108fbe8f5d454dce03`

## Conclusion

Experiment 05 separated state transformation, component correspondence, relational structure, and temporal sequence.[1] A known component permutation removed all relational displacement for pure reindexing under every supported geometry. Exhaustive recovery found the generating permutation among exact minima, but never uniquely, because relation matrices retain geometry-specific automorphisms.

Repeated-state case V5 had 576 exact state-vector correspondences but 1,152 zero-displacement relational correspondences under every geometry. Relational equivalence therefore had greater correspondence ambiguity than direct state equality.

Collision case V6 had no exact state-vector correspondence. Its two distinct state vectors nevertheless had identical fixed-index G1, G2, and G3 relation matrices. This computationally demonstrates non-injective relational representations without implying state equivalence.

Mutation residuals remained after representation effects were removed. Their matrix support depended on both the mutation and the selected geometry. Across a four-transition trajectory, the generating correspondence was recovered for pure reindexing and pure mutation, but mutations sometimes admitted lower-residual correspondences than the generating mapping.

## Method and Correspondence Convention

A correspondence `p` maps target index `i` to source index `p(i)`:

`target[i] = source[p(i)]`

The permutation matrix satisfies `P[i,p(i)] = 1`. The correspondence-aware expected matrix is therefore `P R_source Pᵀ`. The experiment retained two separate quantities:

- **Fixed-index displacement:** `||R_target - R_source||F`.
- **Correspondence-aware displacement:** `||R_target - P R_source Pᵀ||F`.

For hidden correspondences, all 40,320 permutations were evaluated. The implementation retained every global minimizer. Integer geometries used exact comparisons. G3 used `atol=1e-12` and `rtol=0`. G3 remained the G2 metric scaled by 45.[1] [2]

G1, G2, G3, G4, and G6 were reused without modification. G5 remained unavailable because the repository provides no unique state-to-Mandala-position mapping without a ring or scale assumption.

## Table A — Transformation Summary

| Case | Source → target construction | Permutation | Mutation | Repeated values | State stabilizer | Exact state correspondences | Expected ambiguity |
|---|---|---|---|---|---:|---:|---|
| V1 | Canonical → pure nonuniform reindexing | `[2,5,1,7,0,6,4,3]` | None | No | 1 | 1 | Relational automorphisms can make recovery nonunique |
| V2 | Canonical → identity mapping plus target index 0 set to 1 | Identity | One | Yes | 1 | 0 | Mutation creates a repeated value |
| V3 | Canonical → nonuniform reindexing plus target index 0 set to 3 | Nonuniform | One | Yes | 1 | Mutation may change the minimizing set |
| V4 | Canonical → nonuniform reindexing plus target indices 0 and 1 set to 3 and 4 | Nonuniform | Two | Yes | 1 | Multiple mutations may change the minimizing set |
| V5 | `[0,0,0,0,4,4,4,4]` → interleaved repeated values | `[4,0,5,1,6,2,7,3]` | None | Yes | 576 | 576 | State stabilizer and relational automorphisms |
| V6 | `[0,0,1,1,2,2,3,3]` → `[1,1,2,2,3,3,4,4]` | None exists | Not defined as lineage | Yes | 16 | 0 | Distinct states may have equal relation matrices |

## Table B — Exhaustive Correspondence Recovery

Every row tested 40,320 candidates. `True recovered` reports whether the generating permutation was among all minima. V6 has no true state-vector correspondence.

| Case | Geometry | Fixed Δ | Minimum Δ | Minimizers | True recovered | Unique |
|---|---|---:|---:|---:|---|---|
| V1 | G1 | 21.354157 | 0 | 2 | Yes | No |
| V1 | G2 | 9.380832 | 0 | 16 | Yes | No |
| V1 | G3 | 422.137418 | 0 | 16 | Yes | No |
| V1 | G4 | 6.324555 | 0 | 48 | Yes | No |
| V1 | G6 | 9.797959 | 0 | 2 | Yes | No |
| V2 | G1 | 3.741657 | 3.741657 | 4 | Yes | No |
| V2 | G2 | 3.741657 | 3.741657 | 32 | Yes | No |
| V2 | G3 | 168.374582 | 168.374582 | 32 | Yes | No |
| V2 | G4 | 3.741657 | 3.741657 | 96 | Yes | No |
| V2 | G6 | 5.477226 | 3.741657 | 4 | No | No |
| V3 | G1 | 22.045408 | 3.741657 | 4 | Yes | No |
| V3 | G2 | 8.831761 | 3.741657 | 32 | Yes | No |
| V3 | G3 | 397.429239 | 168.374582 | 32 | Yes | No |
| V3 | G4 | 6.164414 | 3.741657 | 96 | Yes | No |
| V3 | G6 | 12.000000 | 4.000000 | 4 | Yes | No |
| V4 | G1 | 22.271057 | 5.656854 | 8 | Yes | No |
| V4 | G2 | 8.485281 | 5.656854 | 64 | Yes | No |
| V4 | G3 | 381.837662 | 254.558441 | 64 | Yes | No |
| V4 | G4 | 6.928203 | 4.898979 | 192 | Yes | No |
| V4 | G6 | 13.266499 | 5.656854 | 8 | No | No |
| V5 | G1 | 22.627417 | 0 | 1,152 | Yes | No |
| V5 | G2 | 22.627417 | 0 | 1,152 | Yes | No |
| V5 | G3 | 1018.233765 | 0 | 1,152 | Yes | No |
| V5 | G4 | 11.313708 | 0 | 1,152 | Yes | No |
| V5 | G6 | 16.970563 | 0 | 1,152 | Yes | No |
| V6 | G1 | 0 | 0 | 32 | N/A | No |
| V6 | G2 | 0 | 0 | 32 | N/A | No |
| V6 | G3 | 0 | 0 | 32 | N/A | No |
| V6 | G4 | 5.656854 | 5.656854 | 256 | N/A | No |
| V6 | G6 | 4.898979 | 4.898979 | 384 | N/A | No |

V1's exact state-vector correspondence was unique, but relational recovery was not unique for any geometry. Its minimizing counts matched the E03 automorphism counts. No recovery case produced a unique relational correspondence.

For V2 and V4 under G6, the generating permutation was not a global minimizer. A different correspondence reduced the residual after mutation. This does not change the known lineage; it shows that relation-only optimization need not recover the generating mapping once state mutation is present.

## Table C — Fixed Versus Supplied Correspondence

For V1–V5, `Correspondence Δ` uses the supplied generating mapping. For V6, it is the exhaustive minimum because no state-vector correspondence exists.

| Case | Geometry | Fixed Δ | Correspondence Δ | Fixed minus correspondence |
|---|---|---:|---:|---:|
| V1 | G1 | 21.354157 | 0 | 21.354157 |
| V1 | G2 | 9.380832 | 0 | 9.380832 |
| V1 | G3 | 422.137418 | 0 | 422.137418 |
| V1 | G4 | 6.324555 | 0 | 6.324555 |
| V1 | G6 | 9.797959 | 0 | 9.797959 |
| V2 | G1 | 3.741657 | 3.741657 | 0 |
| V2 | G2 | 3.741657 | 3.741657 | 0 |
| V2 | G3 | 168.374582 | 168.374582 | 0 |
| V2 | G4 | 3.741657 | 3.741657 | 0 |
| V2 | G6 | 5.477226 | 5.477226 | 0 |
| V3 | G1 | 22.045408 | 3.741657 | 18.303750 |
| V3 | G2 | 8.831761 | 3.741657 | 5.090103 |
| V3 | G3 | 397.429239 | 168.374582 | 229.054657 |
| V3 | G4 | 6.164414 | 3.741657 | 2.422757 |
| V3 | G6 | 12.000000 | 4.000000 | 8.000000 |
| V4 | G1 | 22.271057 | 5.656854 | 16.614203 |
| V4 | G2 | 8.485281 | 5.656854 | 2.828427 |
| V4 | G3 | 381.837662 | 254.558441 | 127.279221 |
| V4 | G4 | 6.928203 | 4.898979 | 2.029224 |
| V4 | G6 | 13.266499 | 6.928203 | 6.338296 |
| V5 | G1 | 22.627417 | 0 | 22.627417 |
| V5 | G2 | 22.627417 | 0 | 22.627417 |
| V5 | G3 | 1018.233765 | 0 | 1018.233765 |
| V5 | G4 | 11.313708 | 0 | 11.313708 |
| V5 | G6 | 16.970563 | 0 | 16.970563 |
| V6 | G1 | 0 | 0 | 0 |
| V6 | G2 | 0 | 0 | 0 |
| V6 | G3 | 0 | 0 | 0 |
| V6 | G4 | 5.656854 | 5.656854 | 0 |
| V6 | G6 | 4.898979 | 4.898979 | 0 |

## Repeated-State Ambiguity

| Geometry | State stabilizer | Exact state correspondences | Relational minimizers | Relational ambiguity greater? | Minimum Δ |
|---|---:|---:|---:|---|---:|
| G1 | 576 | 576 | 1,152 | Yes | 0 |
| G2 | 576 | 576 | 1,152 | Yes | 0 |
| G3 | 576 | 576 | 1,152 | Yes | 0 |
| G4 | 576 | 576 | 1,152 | Yes | 0 |
| G6 | 576 | 576 | 1,152 | Yes | 0 |

The 576 state correspondences are the permutations within the four `0` positions and four `4` positions. The relation matrix additionally permits interchange of those blocks, doubling the minimum set to 1,152.

## V6 Non-Injective Representation Control

V6 compared two distinct vectors with no exact component permutation mapping one into the other.

| Geometry | States equal | Exact state correspondences | Matrices equal | Fixed Δ | Minimum correspondence Δ | Minimizers |
|---|---|---:|---|---:|---:|---:|
| G1 | No | 0 | Yes | 0 | 0 | 32 |
| G2 | No | 0 | Yes | 0 | 0 | 32 |
| G3 | No | 0 | Yes | 0 | 0 | 32 |
| G4 | No | 0 | No | 5.656854 | 5.656854 | 256 |
| G6 | No | 0 | No | 4.898979 | 4.898979 | 384 |

G1–G3 therefore produced identical relation matrices for distinct state configurations. The equality establishes only relational equivalence under those selected metrics. It does not establish state equivalence.

## Table D — Mutation Residual Localization

The table reports the globally minimizing correspondence. Matrix-entry counts include both `(i,j)` and `(j,i)`.

| Case | Geometry | Residual Frobenius | Max element | Changed entries | Affected component pairs |
|---|---|---:|---:|---:|---|
| V2 | G1 | 3.741657 | 1 | 14 | `(0,1)` through `(0,7)` |
| V2 | G2 | 3.741657 | 1 | 14 | `(0,1)` through `(0,7)` |
| V2 | G3 | 168.374582 | 45° | 14 | `(0,1)` through `(0,7)` |
| V2 | G4 | 3.741657 | 1 bit | 14 | `(0,1)` through `(0,7)` |
| V2 | G6 | 3.741657 | 1 step | 14 | `(0,1)` through `(0,7)` |
| V3 | G1 | 3.741657 | 1 | 14 | `(0,1)` through `(0,7)` |
| V3 | G2 | 3.741657 | 1 | 14 | `(0,7)` through `(6,7)` |
| V3 | G3 | 168.374582 | 45° | 14 | `(0,7)` through `(6,7)` |
| V3 | G4 | 3.741657 | 1 bit | 14 | `(0,1)` through `(0,7)` |
| V3 | G6 | 4.000000 | 2 steps | 4 | `(0,3)`, `(0,7)` |
| V4 | G1 | 5.656854 | 2 | 26 | `(0,1..7)` plus `(1..5,6)` and `(6,7)` |
| V4 | G2 | 5.656854 | 2 | 26 | `(0..5,6)`, `(0..5,7)`, and `(6,7)` |
| V4 | G3 | 254.558441 | 90° | 26 | Same support as G2 |
| V4 | G4 | 4.898979 | 1 bit | 24 | `(0,2..7)` and `(1,2..7)` |
| V4 | G6 | 5.656854 | 2 steps | 8 | `(0,3)`, `(0,7)`, `(1,6)`, `(2,6)` |

A single state mutation changed pairwise relations between the affected component and multiple other components. Its relation-matrix signature was therefore row-and-column localized rather than confined to one matrix entry. Under relation-only recovery, the apparent affected component could move when multiple correspondences attained the same minimum.

## Table E — Temporal Correspondence

Permutation strings list `p(0)...p(7)`. Each row reports all 40,320-candidate recovery results for one transition.

| Geometry | Step | True P | Best P | Fixed Δ | True-P Δ | Best Δ | Minimizers | True recovered |
|---|---:|---|---|---:|---:|---:|---:|---|
| G1 | 1 | `25170643` | `25170643` | 21.354157 | 0 | 0 | 2 | Yes |
| G1 | 2 | `01234567` | `01234567` | 3.741657 | 3.741657 | 3.741657 | 4 | Yes |
| G1 | 3 | `76543210` | `07543216` | 8.000000 | 6.324555 | 4.898979 | 4 | No |
| G1 | 4 | `10325476` | `60213547` | 20.149442 | 19.131126 | 8.831761 | 8 | No |
| G2 | 1 | `25170643` | `03756421` | 9.380832 | 0 | 0 | 16 | Yes |
| G2 | 2 | `01234567` | `01234567` | 3.741657 | 3.741657 | 3.741657 | 32 | Yes |
| G2 | 3 | `76543210` | `06453127` | 7.483315 | 5.656854 | 0 | 2 | No |
| G2 | 4 | `10325476` | `62031574` | 10.488088 | 10.099505 | 5.477226 | 4 | No |
| G3 | 1 | `25170643` | `03756421` | 422.137418 | 0 | 0 | 16 | Yes |
| G3 | 2 | `01234567` | `01234567` | 168.374582 | 168.374582 | 168.374582 | 32 | Yes |
| G3 | 3 | `76543210` | `06453127` | 336.749165 | 254.558441 | 0 | 2 | No |
| G3 | 4 | `10325476` | `62031574` | 471.963982 | 454.477722 | 246.475151 | 4 | No |
| G4 | 1 | `25170643` | `01354267` | 6.324555 | 0 | 0 | 48 | Yes |
| G4 | 2 | `01234567` | `01234567` | 3.741657 | 3.741657 | 3.741657 | 96 | Yes |
| G4 | 3 | `76543210` | `04561327` | 6.324555 | 4.000000 | 0 | 4 | No |
| G4 | 4 | `10325476` | `24310756` | 6.164414 | 5.477226 | 3.741657 | 16 | No |
| G6 | 1 | `25170643` | `24170653` | 9.797959 | 0 | 0 | 2 | Yes |
| G6 | 2 | `01234567` | `01234567` | 4.000000 | 4.000000 | 4.000000 | 4 | Yes |
| G6 | 3 | `76543210` | `01543267` | 14.966630 | 4.000000 | 4.000000 | 12 | Yes |
| G6 | 4 | `10325476` | `10352476` | 16.000000 | 8.944272 | 8.485281 | 16 | No |

### Temporal Path Totals

| Geometry | Fixed-index path | Generating-correspondence path | Best-recovered path |
|---|---:|---:|---:|
| G1 | 53.245256 | 29.197339 | 17.472398 |
| G2 | 31.093892 | 19.498017 | 9.218883 |
| G3 | 1399.225147 | 877.410746 | 414.849733 |
| G4 | 22.555182 | 13.218883 | 7.483315 |
| G6 | 44.764589 | 16.944272 | 16.485281 |

Step 1 was pure reindexing and had zero correspondence-aware displacement under the true mapping. Step 2 was pure mutation under identity correspondence. Steps 3 and 4 combined reindexing with mutation. The best relation-only correspondence could differ from the generating lineage because it optimized residual distance after mutation.

## Structural Description

**Correspondence removed representation effects for pure permutations.** V1 and V5 had nonzero fixed-index displacement and zero displacement under their supplied mappings.

**Relational recovery was not unique.** Even canonical V1 had one exact state-vector mapping but multiple relational minima. The multiplicity matched each geometry's state-label automorphism count.

**Repeated values increased ambiguity.** V5's state correspondence set had size 576. Its relational minimum set had size 1,152.

**Mutation could redirect relation-only recovery.** For V2 and V4 under G6, the generating correspondence was not a minimizer. Temporal steps 3 and 4 showed the same effect in several geometries.

**Relational representation was non-injective.** V6 had no exact state correspondence, yet G1–G3 matrices were equal.

**Residual support was geometry-specific.** Single mutation signatures ranged from a full affected row and column to two affected unordered pairs under G6.

## Interpretation Boundary

### Observation

The experiment measured supplied-correspondence displacement, exhaustive minimizing sets, direct state correspondences, stabilizers, mutation residuals, collision behavior, and temporal recovery.

### Structural description

A correspondence is a mapping between component indices. It can remove matrix-coordinate changes caused by reindexing. Relation matrices may admit automorphisms or collisions that prevent unique recovery. After mutation, the minimum-residual relation mapping need not be the generating component lineage.

### Interpretation

Correspondence is not identity. Relational equivalence under one geometry and mapping does not prove that underlying states are equivalent. No claim is made about sovereignty, consciousness, awareness, selfhood, agency, Φ, or any semantic property.

## Reproducibility and Enumeration

| Enumeration category | Candidate evaluations |
|---|---:|
| V1–V6 recovery across five geometries | 1,209,600 |
| Separate V5 ambiguity recovery | 201,600 |
| Four temporal transitions across five geometries | 806,400 |
| **Total exhaustive evaluations** | **2,217,600** |

The implementation and machine-readable results were frozen at the first Experiment 05 commit.[4] The artifact retains every minimizing permutation, every known-correspondence measurement, every residual matrix and changed entry, every collision result, and every temporal transition.[2]

## Validation and Provenance

| Scope | Result |
|---|---:|
| Experiment 05 isolated tests | 27 passed |
| Experiment 01 | 11 passed; frozen files unchanged |
| Experiment 02 | 19 passed; frozen implementation unchanged |
| Experiment 03 | 23 passed; frozen files unchanged |
| Experiment 04 | 15 passed; frozen files unchanged |
| Complete repository suite | 386 passed; 3 existing warnings |

The warnings are unchanged SciPy deprecation warnings from `tests/test_physics.py`. Experiment 05 introduced no new warning or regression.

| Change category | Files |
|---|---|
| Added | `src/relational_correspondence.py`; `tests/test_relational_correspondence.py`; `experiments/run_relational_correspondence.py`; `docs/experiment_05_relational_correspondence_results.json`; `docs/experiment_05_relational_correspondence_report.md` |
| Modified | None |
| Preserved | E01–E04 files remain unchanged from the completed E04 base.[3] |

## References

[1]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/tree/experiment/05-correspondence-relational-lineage "SOMS Experiment 05 branch"
[2]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/blob/experiment/05-correspondence-relational-lineage/docs/experiment_05_relational_correspondence_results.json "SOMS Experiment 05 machine-readable results"
[3]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/f2f3afe02642762b7442cbfdf266625def969b08 "Completed SOMS Experiment 04 base"
[4]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/ec224dd "SOMS Experiment 05 implementation and machine results"
