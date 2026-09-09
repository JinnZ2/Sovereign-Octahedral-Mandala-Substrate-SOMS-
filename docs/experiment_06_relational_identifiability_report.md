# SOMS Experiment 06 — Relational Identifiability and Information Loss

**Author:** Manus AI

**Date:** 2026-09-09

**Branch:** `experiment/06-relational-identifiability`

**Base commit:** `ec224ddb5837efea6aaf258afa0c0c5d10c28984`

**Implementation commit:** `b45fc9504682752cfefd5eff78e8073e4f20947b`

**Machine-results commit:** `7c2642b00b6fbde03ee859c00fb9f4074edc05b0`

**Full-file SHA-256:** `370f914f1a7543423bbf2fb164aebb5498f3ee55f8a99df91da9ee833402eefe`

**Embedded canonical-result SHA-256:** `71bd260ff18cea8e6ae768cfc0862a54621e3dfc7e12c8e76deb4762e087d47a`

## Conclusion

Experiment 06 exhaustively partitioned all 4,096 vectors in `{0,…,7}⁴` by exact equality of their relation matrices.[1] The five supported geometries discarded different amounts of information. G2 and G3 produced the same partition, with G3 carrying no independent distinguishability because it is exactly G2 multiplied by 45. G4 produced the fewest classes. G1 and G6 admitted genuine representation collisions after tested component permutations and state-label automorphisms were excluded.

The joint representation `(G1,G2,G4,G6)` substantially reduced collisions. It produced 3,706 classes, including 3,456 singleton classes. However, it was not injective: 178 joint classes contained at least one pair not explained by the tested symmetries.

The smallest genuine-collision length was 1 for G1, G6, and the joint representation because every one-component relation matrix is the same zero matrix. G2, G3, and G4 had no genuine collision through length 4 after symmetry explanations were applied.

Temporal controls showed that fixed-index relational equivalence can appear or disappear between adjacent instants. A supplied component correspondence correctly removed the fixed-index difference for a pure permutation, including under G6. Temporal observation therefore adds distinguishability in some bounded cases, but does not eliminate the representation's instantaneous information loss.

## Formulation and Experimental Boundary

For geometry `G`, states were grouped by:

`S₁ ~G S₂` if and only if `R_G(S₁) = R_G(S₂)`.

Each distinct pair inside an equal-matrix class was classified in this precedence order:

1. **Component permutation:** one vector is a reordering of the other.
2. **State-label isometry:** one E03 geometry automorphism maps the first vector directly to the second.
3. **Combined symmetry:** a state-label isometry followed by a component permutation explains the pair.
4. **Representation collision:** none of the tested transformations explains the equal matrices.

The classification concerns the bounded tested transformations. Equal relation matrices establish equality under the selected representation. They do not establish equality of the underlying vectors.

G5 remained unavailable because the repository provides no unique state-to-Mandala-position mapping without an unsupported ring or scale assumption. G3 was retained only as a scale-control and was excluded from the joint representation.

## Exhaustive Length-4 Results

The reported singleton fraction uses the number of equivalence classes as its denominator. The machine artifact also records singleton vectors as a fraction of all 4,096 vectors.[2]

| Representation | Vectors | Distinct matrices / classes | Singleton classes | Singleton fraction | Nontrivial classes | Maximum class | Mean class size | Symmetry-explainable classes | Genuine-collision classes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| G1 Numeric | 4,096 | 848 | 0 | 0.000000 | 848 | 14 | 4.830189 | 328 | 520 |
| G2 Cyclic | 4,096 | 260 | 0 | 0.000000 | 260 | 16 | 15.753846 | 260 | 0 |
| G3 Angular | 4,096 | 260 | 0 | 0.000000 | 260 | 16 | 15.753846 | 260 | 0 |
| G4 Gray | 4,096 | 120 | 0 | 0.000000 | 120 | 48 | 34.133333 | 120 | 0 |
| G6 Cayley | 4,096 | 592 | 24 | 0.040541 | 568 | 48 | 6.918919 | 93 | 475 |
| Joint G1/G2/G4/G6 | 4,096 | 3,706 | 3,456 | 0.932542 | 250 | 8 | 1.105235 | 72 | 178 |

The joint singleton-vector fraction was `3,456 / 4,096 = 0.84375`. The joint class fraction was `3,456 / 3,706 = 0.932542`. No individual geometry except G6 produced a singleton class.

### Central Output by Geometry

| Geometry | Measured partition statement |
|---|---|
| G1 | The map partitioned 4,096 vectors into 848 classes. No class was singleton. Of 848 nontrivial classes, 328 were fully symmetry-explainable and 520 contained a genuine collision pair. |
| G2 | The map partitioned 4,096 vectors into 260 classes. No class was singleton. All 260 classes were explained by tested symmetries; no genuine collision was found through length 4. |
| G3 | The map reproduced G2's 260-class partition at 45× scale. It added no independent distinguishability. |
| G4 | The map partitioned 4,096 vectors into 120 classes. No class was singleton. All 120 classes were explained by tested symmetries; no genuine collision was found through length 4. |
| G6 | The map partitioned 4,096 vectors into 592 classes. Twenty-four classes were singleton. Of 568 nontrivial classes, 93 were fully symmetry-explainable and 475 contained a genuine collision pair. |
| Joint | The map partitioned 4,096 vectors into 3,706 classes. A fraction 0.932542 of classes were singleton. Of 250 nontrivial classes, 72 were fully symmetry-explainable and 178 contained a genuine collision pair. |

## Pair-Level Collision Classification

Every unordered pair inside every nontrivial class was retained and classified. The counts below are pair counts rather than class counts.

| Representation | Component-permutation pairs | Label-isometric pairs | Combined-symmetry pairs | Genuine-collision pairs | Total equal-matrix pairs |
|---|---:|---:|---:|---:|---:|
| G1 | 420 | 1,964 | 336 | 8,648 | 11,368 |
| G2 | 924 | 29,540 | 0 | 0 | 30,464 |
| G3 | 924 | 29,540 | 0 | 0 | 30,464 |
| G4 | 2,700 | 76,148 | 0 | 0 | 78,848 |
| G6 | 2,256 | 1,181 | 1,572 | 20,131 | 25,140 |
| Joint | 120 | 0 | 0 | 548 | 668 |

Component permutation was evaluated before label isometry. A pair satisfying both conditions is therefore counted as component-permutation-equivalent, not twice.

## Minimal Genuine-Collision Search

The search exhaustively evaluated lengths 1 through 4. A one-component matrix contains only its zero diagonal and therefore loses the state label. The E03 full-state-space automorphism test does not map every singleton label to every other label under G1, G6, or the intersection used by the joint representation.

| Representation | Genuine-collision classes at n=1 / 2 / 3 / 4 | Minimum length | First retained pair | Result |
|---|---|---:|---|---|
| G1 | 1 / 6 / 61 / 520 | 1 | `[0]`, `[1]` | Genuine collision |
| G2 | 0 / 0 / 0 / 0 | None through 4 | — | Every equal-matrix pair was symmetry-explainable |
| G3 | 0 / 0 / 0 / 0 | None through 4 | — | Same partition as G2 |
| G4 | 0 / 0 / 0 / 0 | None through 4 | — | Every equal-matrix pair was symmetry-explainable |
| G6 | 1 / 5 / 53 / 475 | 1 | `[0]`, `[1]` | Genuine collision |
| Joint | 1 / 6 / 73 / 178 | 1 | `[0]`, `[1]` | Genuine collision |

The machine artifact retains both vectors, both relation matrices, exact-equality evidence, symmetry-test witnesses, and cross-geometry measurements for each reported minimum.[2]

## Cross-Geometry Distinguishability

There were 28,216 unique length-4 genuine-collision pairs after duplicate pairs originating in multiple representations were merged. Every pair was evaluated under all supported geometries.

| Indistinguishable geometry signature | Pair count | Distinguishable complement |
|---|---:|---|
| G1, G2, G3 | 4,060 | G4, G6 |
| G1, G2, G3, G4 | 4,020 | G6 |
| G1, G2, G3, G4, G6 | 548 | None |
| G1, G2, G3, G6 | 100 | G4 |
| G2, G3, G4, G6 | 232 | G1 |
| G2, G3, G6 | 348 | G1, G4 |
| G4, G6 | 1,596 | G1, G2, G3 |
| G6 | 17,312 | G1, G2, G3, G4 |

The 548 pairs indistinguishable under all five supported geometries are precisely the genuine equal-pair count remaining in the joint representation. G2 and G3 always appear together, as required by their exact scaling relationship.

## Selected Length-8 Controls

The result artifact identifies the originating experiments and control IDs for every inherited control.[2]

| Control | Provenance | G1 Δ | G2 Δ | G3 Δ | G4 Δ | G6 Δ | Separation signature |
|---|---|---:|---:|---:|---:|---:|---|
| E05 V6 | E05 `V6_collision_case` | 0 | 0 | 0 | 5.656854 | 4.898979 | Equal in G1–G3; separated by G4 and G6 |
| Canonical component permutation | E03 component-index control; E05 V1 | 21.354157 | 9.380832 | 422.137418 | 6.324555 | 9.797959 | Fixed-index matrices differ in all geometries |
| Canonical global cyclic shift | E02/E03 global cyclic; E04 T1 | 14.966630 | 0 | 0 | 8 | 10.583005 | Equal in G2/G3 only |
| Half-cycle candidate | E06 deliberate control | 0 | 0 | 0 | 0 | 12.649111 | Equal in G1–G4; separated by G6 |

The E05 V6 pair is a genuine G1 collision but is label-isometric under G2 and G3. This distinction demonstrates why equal matrices must be classified rather than counted uniformly as collisions.

## Joint Representation

The joint key concatenated the exact G1, G2, G4, and G6 relation matrices. G3 was excluded because it duplicates G2 up to scale. The four joint geometries shared only the identity state-label automorphism over the full eight-state space.

| Metric | Best individual value | Joint value | Change |
|---|---:|---:|---|
| Distinct classes | G1: 848 | 3,706 | Increased by 2,858 |
| Singleton classes | G6: 24 | 3,456 | Increased by 3,432 |
| Maximum class size | G1/G2: 14–16 | 8 | Reduced |
| Nontrivial classes | G4: 120 | 250 | More classes remain, but they cover only 640 vectors |
| Genuine-collision classes | G2/G3/G4: 0 after their larger symmetry groups | 178 | Joint symmetries are stricter; 548 pairs remain unexplained |

The joint representation reduced fixed-index equivalence substantially, but did not become injective.

## Temporal Identifiability Controls

Each scenario retained both vectors and both relation matrices at every time, instantaneous fixed-index equivalence, pair displacement, optional validated correspondence, and within-trajectory transition displacement.

| Scenario | Geometry | Instantaneous equivalence sequence | Pair displacement sequence | Relationship sequence |
|---|---|---|---|---|
| Collision → collision | G1 | Equal → equal | `0 → 0` | Genuine → genuine |
| Collision → collision | G2/G3/G4 | Equal → equal | `0 → 0` | Label-isometric → label-isometric |
| Collision → collision | G6 | Different → equal | `2.828427 → 0` | None → genuine |
| Collision → distinguishable | G1/G2/G4 | Equal → different | `0 → 2.449490` | Genuine or label-isometric → none |
| Collision → distinguishable | G3 | Equal → different | `0 → 110.227038` | Label-isometric → none |
| Collision → distinguishable | G6 | Different → different | `2.828427 → 4` | None → none |
| Distinguishable → collision | G1/G2/G4 | Different → equal | `2.449490 → 0` | None → genuine or label-isometric |
| Distinguishable → collision | G3 | Different → equal | `110.227038 → 0` | None → label-isometric |
| Distinguishable → collision | G6 | Different → different | `4 → 2.828427` | None → none |
| Permutation → collision | G1 | Equal → equal | `0 → 0` | Component permutation → genuine |
| Permutation → collision | G2/G3/G4 | Equal → equal | `0 → 0` | Component permutation → label-isometric |
| Permutation → collision | G6 | Different → different | `2.828427 → 2.828427` | None → none |
| Mutation → collision | G1/G2/G4 | Different → equal | `2.449490 → 0` | None → genuine or label-isometric |
| Mutation → collision | G3 | Different → equal | `110.227038 → 0` | None → label-isometric |
| Mutation → collision | G6 | Different → different | `4 → 2.828427` | None → none |

For the permutation scenario, the supplied reversal correspondence was validated. Its correspondence-aware displacement was zero under every geometry, including G6, even though G6's fixed-index matrices differed by `2.828427`. For the mutation scenario, the supplied identity mapping retained the nonzero mutation residual.

The G1 collision-to-distinguishable and distinguishable-to-collision cases directly establish that instantaneous equality need not persist through the next observation. The complete geometry-specific matrices and transition displacements remain in the result artifact.[2]

## Observation

The experiment directly enumerated every length-4 state, every relation class, every member of every non-singleton class, and every unordered pair within each non-singleton class. It also measured selected length-8 pairs and five paired temporal scenarios.

## Structural Description

A relational representation is a many-to-one projection when distinct vectors occupy the same equivalence class. Some multiplicity is explained by component reordering or geometry automorphisms. Other multiplicity remains after those tested transformations and is classified here as genuine representation collision. Combining relation matrices refines the partition but does not guarantee injectivity.

## Interpretation

The measurements identify which bounded state distinctions survive each relational projection. They do not assign meaning to those distinctions. **Correspondence is not identity.** Relational equivalence under a selected geometry and mapping does not establish equivalence of the underlying state configurations.

No claim is made concerning sovereignty, consciousness, awareness, selfhood, agency, Φ, or semantic identity.

## Reproducibility

The result generator is deterministic and uses no randomized operation. The exact command embedded in the artifact is:

```bash
SOMS_E06_IMPLEMENTATION_COMMIT=b45fc9504682752cfefd5eff78e8073e4f20947b PYTHONPATH=. python3 experiments/run_relational_identifiability.py > docs/experiment_06_relational_identifiability_results.json
```

The artifact records the implementation commit, SHA-256 of the generator source, complete experiment parameters, geometry definitions, all nontrivial class members, all pair classifications, cross-geometry evidence, joint results, temporal controls, and an independently verified canonical-result hash.[2] [3]

## Validation and Provenance

| Scope | Result |
|---|---:|
| Experiment 06 isolated tests | 27 passed |
| Experiment 01 | 11 passed; frozen files unchanged |
| Experiment 02 | 19 passed; frozen files unchanged |
| Experiment 03 | 23 passed; frozen files unchanged |
| Experiment 04 | 15 passed; frozen files unchanged |
| Experiment 05 | 27 passed; frozen implementation and result unchanged |
| Complete repository suite | 413 passed; 3 existing warnings |

The warnings are unchanged SciPy deprecation warnings from `tests/test_physics.py`. Experiment 06 introduced no new warning or regression.

| Change category | Files |
|---|---|
| Added | `src/relational_identifiability.py`; `tests/test_relational_identifiability.py`; `experiments/run_relational_identifiability.py`; `docs/experiment_06_relational_identifiability_results.json`; `docs/experiment_06_relational_identifiability_report.md` |
| Modified historical artifacts | None |
| Preserved | E01–E05 source, tests, runners, results, and historical reports remain unchanged from the authorized E05 implementation base.[4] |

## References

[1]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/tree/experiment/06-relational-identifiability "SOMS Experiment 06 branch"
[2]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/blob/experiment/06-relational-identifiability/docs/experiment_06_relational_identifiability_results.json "SOMS Experiment 06 complete machine-readable results"
[3]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/b45fc9504682752cfefd5eff78e8073e4f20947b "SOMS Experiment 06 reproducible implementation commit"
[4]: https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-/commit/ec224ddb5837efea6aaf258afa0c0c5d10c28984 "Authorized SOMS Experiment 05 implementation base"
