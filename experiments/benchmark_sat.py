"""
MAX-SAT Benchmark: SOMS Annealer vs Vanilla Simulated Annealing
================================================================
Compares the SOMS octahedral annealer against a baseline simulated
annealer on random MAX-SAT instances to measure whether octahedral
geometry actually helps.

Three arms, all with the same geometric cooling schedule, the same
number of single-cell proposals, and Metropolis acceptance:

  vanilla     : binary spins, energy = #unsatisfied clauses
  soms_geo    : SOMSEngine as shipped — energy is PURELY the geometric
                FRET coupling; the clauses never enter the energy.
                (This was the original benchmark. It measures the best
                of n_sweeps random assignments: one random assignment
                satisfies 1 - 1/8 = 87.5% of random 3-SAT clauses in
                expectation; the best of 100 lands around 94-96%.)
  soms_sat    : SOMSEngine with a clause-penalty term added to the
                local energy (+1 per unsatisfied clause, the encoding
                used by Mandala-Computing's MandalaComputer.encode_sat),
                on top of the geometric coupling. Distances are
                normalized so J_nn = 1 and T is on the same scale.

Decoding for both SOMS arms: states 0-3 → False, 4-7 → True.

Positive result: soms_sat beats vanilla → the geometric term is a useful
                 regularizer for this readout.
Negative result: soms_sat ≈ vanilla → geometry is neutral; the clause
                 term does all the work.
Either way, soms_geo shows what an unencoded problem looks like: a
best-of-N random draw, not a search.

Requirements: pip install numpy scipy
"""

import numpy as np
import os
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.mandala_structure import MandalaMap
from src.octahedral_physics import SOMSEngine


# ============================================================
# Random MAX-SAT instance generator
# ============================================================

def generate_max_sat(n_vars: int, n_clauses: int, k: int = 3,
                     seed: int = 42) -> list:
    """Random k-SAT: each clause is k (var_index, sign) literals."""
    rng = np.random.RandomState(seed)
    clauses = []
    for _ in range(n_clauses):
        vars_in_clause = rng.choice(n_vars, size=k, replace=False)
        signs = rng.choice([-1, 1], size=k)
        clauses.append([(int(v), int(s)) for v, s in zip(vars_in_clause, signs)])
    return clauses


def evaluate_sat(assignment: np.ndarray, clauses: list) -> int:
    """Count satisfied clauses given a binary assignment."""
    satisfied = 0
    for clause in clauses:
        for var_idx, sign in clause:
            val = assignment[var_idx]
            if (sign > 0 and val) or (sign < 0 and not val):
                satisfied += 1
                break
    return satisfied


def clauses_by_var(n_vars: int, clauses: list) -> list:
    """Index: variable → list of clauses that mention it (for local dE)."""
    idx = [[] for _ in range(n_vars)]
    for c in clauses:
        for v, _ in c:
            idx[v].append(c)
    return idx


def unsatisfied_in(assignment: np.ndarray, clause_list: list) -> int:
    return len(clause_list) - evaluate_sat(assignment, clause_list)


# ============================================================
# Vanilla simulated annealer (baseline)
# ============================================================

def vanilla_anneal(n_vars: int, clauses: list, n_proposals: int,
                   T_start: float = 5.0, T_final: float = 0.01,
                   seed: int = 0) -> dict:
    """Single-bit-flip SA on the binary assignment with local dE."""
    rng = np.random.RandomState(seed)
    by_var = clauses_by_var(n_vars, clauses)
    assignment = rng.randint(0, 2, size=n_vars)
    best_assignment = assignment.copy()
    best_sat = evaluate_sat(assignment, clauses)
    cur_sat = best_sat

    T = T_start
    ratio = (T_final / T_start) ** (1.0 / max(1, n_proposals - 1))

    for _ in range(n_proposals):
        i = rng.randint(n_vars)
        old_local = unsatisfied_in(assignment, by_var[i])
        assignment[i] ^= 1
        new_local = unsatisfied_in(assignment, by_var[i])
        dE = new_local - old_local
        if dE <= 0 or rng.random() < np.exp(-dE / max(T, 1e-12)):
            cur_sat -= dE
            if cur_sat > best_sat:
                best_sat = cur_sat
                best_assignment = assignment.copy()
        else:
            assignment[i] ^= 1
        T *= ratio

    return {"satisfied": best_sat, "total": len(clauses),
            "ratio": best_sat / len(clauses)}


# ============================================================
# SOMS annealers
# ============================================================

class SATEngine(SOMSEngine):
    """
    SOMSEngine whose local energy also counts unsatisfied clauses.

    E_local(i) = geometric(i) + clause_weight * #unsat clauses touching i
    Same encoding as MandalaComputer.encode_sat (state >= 4 → True).
    """

    def __init__(self, num_cells, clauses, n_vars, clause_weight=1.0,
                 problem_type="SAT"):
        super().__init__(num_cells=num_cells, problem_type=problem_type)
        self.n_vars = n_vars
        self.clauses = clauses
        self.by_var = clauses_by_var(n_vars, clauses)
        self.clause_weight = clause_weight

    def assignment(self):
        return (self.state_indices[:self.n_vars] >= 4).astype(int)

    def _local_energy(self, cell_idx, j_ij):
        e = super()._local_energy(cell_idx, j_ij)
        if cell_idx < self.n_vars:
            e += self.clause_weight * unsatisfied_in(self.assignment(),
                                                     self.by_var[cell_idx])
        return e

    def energy_landscape(self, j_ij):
        return (super().energy_landscape(j_ij)
                + self.clause_weight * unsatisfied_in(self.assignment(), self.clauses))


def build_geometry(n_vars: int, normalize: bool):
    """Smallest MandalaMap with >= n_vars cells; optional J_nn = 1 scaling."""
    u = max(10, n_vars)
    while True:
        m = MandalaMap(u=u, depth=5)
        if m.num_cells >= n_vars:
            break
        u += 10
    n = m.num_cells
    dist = np.linalg.norm(m.pos[:, None] - m.pos[None, :], axis=-1)
    if normalize:
        dist = dist / dist[~np.eye(n, dtype=bool)].min()
    return m, dist + np.eye(n)


def soms_anneal_sat(n_vars: int, clauses: list, n_sweeps: int,
                    T_start: float = 5.0, T_final: float = 0.01,
                    seed: int = 0, encode_clauses: bool = True) -> dict:
    """
    SOMS annealer on SAT. One sweep = one relax_step = num_cells proposals.
    encode_clauses=False reproduces the original (geometry-only) benchmark.
    """
    np.random.seed(seed)
    m, dist = build_geometry(n_vars, normalize=encode_clauses)
    n = m.num_cells

    if encode_clauses:
        e = SATEngine(num_cells=n, clauses=clauses, n_vars=n_vars)
    else:
        e = SOMSEngine(num_cells=n, problem_type="SAT")
    j = e.fret_coupling(dist)

    best_sat = evaluate_sat((e.state_indices[:n_vars] >= 4).astype(int), clauses)
    T = T_start
    ratio = (T_final / T_start) ** (1.0 / max(1, n_sweeps - 1))
    for _ in range(n_sweeps):
        e.relax_step(j, temperature=T)
        sat = evaluate_sat((e.state_indices[:n_vars] >= 4).astype(int), clauses)
        best_sat = max(best_sat, sat)
        T *= ratio

    return {"satisfied": best_sat, "total": len(clauses),
            "ratio": best_sat / len(clauses), "cells_used": n}


# ============================================================
# Benchmark
# ============================================================

def run_benchmark(n_trials: int = 10, n_sweeps: int = 100):
    problems = [
        {"n_vars": 20, "n_clauses": 80, "label": "20v/80c (easy)"},
        {"n_vars": 30, "n_clauses": 120, "label": "30v/120c (medium)"},
        {"n_vars": 40, "n_clauses": 160, "label": "40v/160c (hard)"},
    ]

    print("=" * 70)
    print("MAX-SAT BENCHMARK: SOMS vs Vanilla Simulated Annealing")
    print("=" * 70)
    print(f"Trials per problem: {n_trials}")
    print(f"SOMS sweeps per trial: {n_sweeps} (vanilla gets the same number of proposals)")
    print(f"Random-assignment expectation on 3-SAT: {1 - 1/8:.1%}")
    print()

    arms = {
        "vanilla":  lambda nv, cl, cells, s: vanilla_anneal(nv, cl, n_proposals=n_sweeps * cells, seed=s),
        "soms_geo": lambda nv, cl, cells, s: soms_anneal_sat(nv, cl, n_sweeps, seed=s, encode_clauses=False),
        "soms_sat": lambda nv, cl, cells, s: soms_anneal_sat(nv, cl, n_sweeps, seed=s, encode_clauses=True),
    }

    for prob in problems:
        n_vars, n_clauses, label = prob["n_vars"], prob["n_clauses"], prob["label"]
        clauses = generate_max_sat(n_vars, n_clauses, k=3, seed=42)
        cells = build_geometry(n_vars, normalize=True)[0].num_cells

        print(f"--- {label} ({n_clauses} clauses, {cells} cells) ---")
        means = {}
        for name, fn in arms.items():
            scores, t0 = [], time.time()
            for trial in range(n_trials):
                scores.append(fn(n_vars, clauses, cells, trial)["ratio"])
            means[name] = np.mean(scores)
            print(f"  {name:9s} mean={np.mean(scores):6.1%}  best={np.max(scores):6.1%}  "
                  f"time={time.time() - t0:5.2f}s")
        diff = means["soms_sat"] - means["vanilla"]
        verdict = ("SOMS wins" if diff > 0.01 else
                   "Vanilla wins" if diff < -0.01 else "comparable")
        print(f"  soms_sat - vanilla: {diff:+.1%} ({verdict})")
        print()

    print("=" * 70)
    print("INTERPRETATION:")
    print("  soms_geo is a best-of-N random draw: the clauses never enter its")
    print("  energy, so it anneals a geometric landscape that has nothing to do")
    print("  with the SAT instance. Its score is set by N, not by search.")
    print("  soms_sat is the fair test: same clause penalty as vanilla, plus")
    print("  the octahedral coupling as a regularizer. Compare its line to")
    print("  vanilla to read the contribution of the geometry.")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
