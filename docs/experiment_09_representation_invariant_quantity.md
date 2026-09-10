# Experiment 09 — Representation-Invariant Quantity (measured case)

Status: **write-up of a measured instance**, not a synthetic harness.
The instance is the annealer scale finding in `experiments/README.md`
("Results", bottleneck 1). Nothing in the engine was changed for this note.

## 1. Setup

Take the standard configuration from the CLAUDE.md quick-start:

```
MandalaMap(u=20, depth=5)   ->  41 cells, pairwise distances d_ij in [20, 444]
SOMSEngine(problem_type="SAT")
J = fret_coupling(d)        ->  J_ij = d_ij^-6  (off-diagonal), J_ii pinned to 1
anneal(J, T_start=5.0, T_final=0.01, n_steps=300)
```

Apply the invertible transformation

```
A : d  ->  d / d_nn          d_nn = min_{i != j} d_ij = 20.0
A^-1 : d' ->  d' * d_nn      (A^-1 A d == d, checked)
```

A is a uniform rescaling of the geometry. It destroys no information: the
configuration, the ranking of every pair by distance, and every ratio of
distances are preserved.

## 2. Three levels of quantity

```
                        Q(x)                  Q(Ax)              relation           class
 ┌──────────────────────────────────────────────────────────────────────────────────────────┐
 │ Q_rep   J_ij (i≠j)     d^-6                (d/d_nn)^-6         Q(Ax) = c·Q(x)     covariant│
 │                                                                c = d_nn^6 = 6.4e7          │
 │ Q_sys   E(x) over      Σ J sin²(Δθ) + …    c·E(x)              same for EVERY x  covariant │
 │         all states     argmin E            argmin E            identical          INVARIANT│
 │                        rank order of E     rank order of E     identical          INVARIANT│
 │ Q_proc  anneal at      accept(tail) 1.00   accept(tail) 0.47   different          NOT      │
 │         fixed T        E_final/E_rand 1.19 E_final/E_rand 0.03                    invariant│
 │ Q_dec   "did it        no (random walk)    yes (search)        flipped            NOT      │
 │         optimize?"                                                                invariant│
 └──────────────────────────────────────────────────────────────────────────────────────────┘
```

Measured (seeds 0 and 1):

| quantity | raw d | A·d | raw d, T scaled by 1/c |
|---|---|---|---|
| off-diagonal J_A == c·J_raw | — | True | — |
| E_A == c·E_raw for 200 random states | — | True | — |
| argmin and full rank order of E identical | — | True | — |
| acceptance ratio, last 10% of steps (seed 0 / 1) | 1.00 / 1.00 | 0.47 / 0.50 | 0.48 |
| E_final / E_random (seed 0 / 1) | 1.19 / 1.14 | 0.03 / 0.17 | 0.10 |

The last column is the control that locates the non-invariance: scaling the
temperature schedule by the same constant, with the geometry untouched,
restores the search. The procedure is covariant under (J, T) → (cJ, cT) and
not under J → cJ alone.

## 3. Reading

```
 system state ──A (invertible)──▶ representation ──▶ measurement operator ──▶ reported Q ──▶ decision
      │                                │                      │                      │            │
   invariant                      covariant             NOT covariant           changes        flips
  (same argmin,                   (J → cJ)          (Metropolis at fixed T:    (accept 1.00     ("random walk"
   same ranking)                                     exp(-cΔE/T) ≠ exp(-ΔE/T))   → 0.47)          → "search")
```

Jin et al.'s distinction applies exactly. An invertible reparameterization
left `Q_system` unchanged and changed `Q_procedure` and `Q_decision`. The
annealer was reported for months as "stochastic, non-monotone, no optimality
guarantee" (validate_annealer tests 1, 2, 4) and all three held under both
frames, because those tests are also invariant under the frame change: a
random walk satisfies them too. The quantity that discriminated was the
acceptance ratio, which is procedure-level and frame-dependent by
construction.

## 4. What this settles and what it does not

Settled:

- The reported annealer outcome in the quick-start configuration is a
  property of the (J, T) pairing, not of the geometry. Any downstream claim
  built on `anneal()` with raw MandalaMap distances at u ≥ 2 inherits the
  frame.
- `fret_coupling` is not scale-free. Either it takes a reference distance
  (`J = (r0/r)^6`), or the temperature schedule is set from the energy scale
  (median |ΔE| of trial moves), or callers normalize. One of these is the
  engine fix; this note does not choose.

Not settled:

- Which invariant the *decision* should be built on. A decision quantity
  that is covariant with the procedure (acceptance ratio) will always flip
  under a frame change; one built on `Q_system` (energy ranking, argmin)
  cannot flip but is not what an annealer reports.
- Whether the same pattern holds in `HolographicEngine.renormalization_anneal`,
  which carries its own `T_start=5.0` default and the same distance input.

## 5. Reproduce

```python
import numpy as np
from src import MandalaMap, SOMSEngine
m = MandalaMap(u=20, depth=5); n = m.num_cells
d = np.linalg.norm(m.pos[:, None] - m.pos[None, :], axis=-1); off = ~np.eye(n, dtype=bool)
d_nn = d[off].min(); c = d_nn ** 6
e = SOMSEngine(num_cells=n, problem_type="SAT")
J_raw = e.fret_coupling(d + np.eye(n)); J_A = e.fret_coupling(d / d_nn + np.eye(n))
assert np.allclose(J_A[off], c * J_raw[off])                      # Q_rep covariant
S = [SOMSEngine(num_cells=n, problem_type="SAT") for _ in range(200)]
E_raw = np.array([s.energy_landscape(J_raw) for s in S]); E_A = np.array([s.energy_landscape(J_A) for s in S])
assert np.allclose(E_A, c * E_raw) and (np.argsort(E_raw) == np.argsort(E_A)).all()   # Q_sys invariant
for J in (J_raw, J_A):                                              # Q_proc not invariant
    np.random.seed(0); s = SOMSEngine(num_cells=n, problem_type="SAT")
    h = s.anneal(J, T_start=5.0, T_final=0.01, n_steps=300)
    print("accept(tail) =", np.mean([x[3] for x in h[-30:]]) / n)
```

Same numbers are produced by `experiments/validate_annealer.py` TEST 6.
