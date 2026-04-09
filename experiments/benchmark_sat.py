"""
MAX-SAT Benchmark: SOMS Annealer vs Vanilla Simulated Annealing
================================================================
Compares the SOMS octahedral annealer against a baseline simulated
annealer on random MAX-SAT instances to measure whether octahedral
geometry actually helps.

Both annealers use the same:
  - Cooling schedule (geometric: T *= ratio each step)
  - Number of steps
  - Metropolis acceptance criterion

The ONLY difference is state encoding:
  - SOMS: 8 octahedral states with angular + tensor pathway coupling
  - Vanilla: 8 random integer states with Hamming-distance coupling

If SOMS geometry helps, it should find lower-energy solutions on average.
If it doesn't, that's valuable data too.

Requirements: pip install numpy scipy
"""

import numpy as np
import sys
import time
sys.path.insert(0, '..')

from src.mandala_structure import MandalaMap
from src.octahedral_physics import SOMSEngine


# ============================================================
# Random MAX-SAT instance generator
# ============================================================

def generate_max_sat(n_vars: int, n_clauses: int, k: int = 3,
                     seed: int = 42) -> list:
    """
    Generate a random k-SAT instance.
    Each clause is a list of k literals (positive = true, negative = negated).
    """
    rng = np.random.RandomState(seed)
    clauses = []
    for _ in range(n_clauses):
        vars_in_clause = rng.choice(n_vars, size=k, replace=False)
        signs = rng.choice([-1, 1], size=k)
        clause = [(int(v), int(s)) for v, s in zip(vars_in_clause, signs)]
        clauses.append(clause)
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


# ============================================================
# Vanilla simulated annealer (baseline)
# ============================================================

def vanilla_anneal(n_vars: int, clauses: list, n_steps: int = 300,
                   T_start: float = 5.0, T_final: float = 0.01,
                   seed: int = 0) -> dict:
    """
    Standard simulated annealing on binary assignment.
    Flip one random bit per step, Metropolis acceptance.
    """
    rng = np.random.RandomState(seed)
    assignment = rng.randint(0, 2, size=n_vars)
    best_assignment = assignment.copy()
    best_sat = evaluate_sat(assignment, clauses)

    T = T_start
    ratio = (T_final / T_start) ** (1.0 / max(1, n_steps - 1))

    for step in range(n_steps):
        # Propose: flip one random bit
        flip_idx = rng.randint(n_vars)
        new_assignment = assignment.copy()
        new_assignment[flip_idx] = 1 - new_assignment[flip_idx]

        old_sat = evaluate_sat(assignment, clauses)
        new_sat = evaluate_sat(new_assignment, clauses)

        # We want to MAXIMIZE satisfied clauses, so dE = old - new
        # (higher is better, so accept if new > old)
        dE = old_sat - new_sat  # negative = improvement
        if dE <= 0 or rng.random() < np.exp(-dE / max(T, 1e-12)):
            assignment = new_assignment
            if new_sat > best_sat:
                best_sat = new_sat
                best_assignment = new_assignment.copy()

        T *= ratio

    return {
        "satisfied": best_sat,
        "total": len(clauses),
        "ratio": best_sat / len(clauses),
    }


# ============================================================
# SOMS annealer on SAT encoding
# ============================================================

def soms_anneal_sat(n_vars: int, clauses: list, n_steps: int = 300,
                    T_start: float = 5.0, T_final: float = 0.01,
                    seed: int = 0) -> dict:
    """
    SOMS annealer applied to SAT. Each cell represents a variable.
    States 0-3 = False, States 4-7 = True (binary threshold on
    octahedral state index).
    """
    np.random.seed(seed)
    # Scale u until MandalaMap produces enough cells
    u = max(10, n_vars)
    while True:
        m = MandalaMap(u=u, depth=5)
        if m.num_cells >= n_vars:
            break
        u += 10
    actual_cells = m.num_cells

    e = SOMSEngine(num_cells=actual_cells, problem_type="SAT")
    dist = np.linalg.norm(m.pos[:, None] - m.pos[None, :], axis=-1)
    dist += np.eye(actual_cells)  # avoid div by zero
    j = e.fret_coupling(dist)

    # Run the SOMS annealer
    e.anneal(j, T_start=T_start, T_final=T_final, n_steps=n_steps)

    # Decode: states 0-3 → False, 4-7 → True (use first n_vars cells)
    assignment = (e.state_indices[:n_vars] >= 4).astype(int)

    best_sat = evaluate_sat(assignment, clauses)

    return {
        "satisfied": best_sat,
        "total": len(clauses),
        "ratio": best_sat / len(clauses),
        "cells_used": actual_cells,
    }


# ============================================================
# Benchmark
# ============================================================

def run_benchmark():
    problems = [
        {"n_vars": 20, "n_clauses": 80, "label": "20v/80c (easy)"},
        {"n_vars": 30, "n_clauses": 120, "label": "30v/120c (medium)"},
        {"n_vars": 40, "n_clauses": 160, "label": "40v/160c (hard)"},
    ]
    n_trials = 10
    n_steps = 300

    print("=" * 70)
    print("MAX-SAT BENCHMARK: SOMS vs Vanilla Simulated Annealing")
    print("=" * 70)
    print(f"Trials per problem: {n_trials}")
    print(f"Steps per trial: {n_steps}")
    print()

    for prob in problems:
        n_vars = prob["n_vars"]
        n_clauses = prob["n_clauses"]
        label = prob["label"]

        clauses = generate_max_sat(n_vars, n_clauses, k=3, seed=42)

        vanilla_scores = []
        soms_scores = []
        vanilla_time = 0.0
        soms_time = 0.0

        for trial in range(n_trials):
            t0 = time.time()
            v_result = vanilla_anneal(n_vars, clauses, n_steps=n_steps,
                                      seed=trial)
            vanilla_time += time.time() - t0
            vanilla_scores.append(v_result["ratio"])

            t0 = time.time()
            s_result = soms_anneal_sat(n_vars, clauses, n_steps=n_steps,
                                       seed=trial)
            soms_time += time.time() - t0
            soms_scores.append(s_result["ratio"])

        v_mean = np.mean(vanilla_scores)
        s_mean = np.mean(soms_scores)
        v_best = np.max(vanilla_scores)
        s_best = np.max(soms_scores)

        print(f"--- {label} ({n_clauses} clauses) ---")
        print(f"  Vanilla SA:  mean={v_mean:.1%}  best={v_best:.1%}  "
              f"time={vanilla_time:.2f}s")
        print(f"  SOMS:        mean={s_mean:.1%}  best={s_best:.1%}  "
              f"time={soms_time:.2f}s")
        diff = s_mean - v_mean
        print(f"  Difference:  {diff:+.1%} "
              f"({'SOMS wins' if diff > 0.01 else 'Vanilla wins' if diff < -0.01 else 'comparable'})")
        print()

    print("=" * 70)
    print("INTERPRETATION:")
    print("  If SOMS consistently outperforms vanilla SA, octahedral geometry")
    print("  is providing useful structure to the energy landscape.")
    print("  If they're comparable or vanilla wins, the geometry may not help")
    print("  for MAX-SAT specifically (it might help for other problem types).")
    print()
    print("  NOTE: The SOMS encoding (state >= 4 → True) is naive.")
    print("  A better encoding would map clause structure onto the octahedral")
    print("  coupling matrix. This benchmark tests the baseline, not the ceiling.")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
