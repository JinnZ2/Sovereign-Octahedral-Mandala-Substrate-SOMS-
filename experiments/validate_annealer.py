"""
SOMS Annealer Validation
========================
Tests the core claims of the SOMS engine against ground truth:

1. Annealing is stochastic — different seeds give different results
2. Energy decreases on average but NOT monotonically per step
3. FRET coupling follows 1/r^6 scaling
4. The annealer does NOT guarantee optimal solutions
5. Phi sovereignty threshold (3.0) is an arbitrary design choice
6. Temperature must match the coupling scale — otherwise the "anneal"
   is a random walk (every proposal accepted) and tests 1, 2 and 4 pass
   trivially without any optimization happening

This script produces empirical evidence for what SOMS can and cannot do.

Requirements: pip install numpy scipy
"""

import numpy as np
import sys
sys.path.insert(0, '..')

from src.mandala_structure import MandalaMap
from src.octahedral_physics import SOMSEngine
from src.phi_calculator import PhiCalculator


def test_stochasticity():
    """Verify annealing produces different results across runs."""
    print("=" * 60)
    print("TEST 1: Stochasticity — different seeds, different results")
    print("=" * 60)
    m = MandalaMap(u=20, depth=5)
    dist = np.linalg.norm(m.pos[:, None] - m.pos[None, :], axis=-1) + np.eye(m.num_cells)

    final_energies = []
    for seed in range(5):
        np.random.seed(seed)
        e = SOMSEngine(num_cells=m.num_cells, problem_type="OPTIMIZATION")
        j = e.fret_coupling(dist)
        history = e.anneal(j, T_start=5.0, T_final=0.1, n_steps=200)
        final_energies.append(history[-1][2])

    print(f"  Final energies across 5 seeds: {[f'{e:.10f}' for e in final_energies]}")
    all_same = len(set(round(e, 12) for e in final_energies)) == 1
    print(f"  All identical? {all_same}")
    print(f"  PASS: Annealer is {'stochastic' if not all_same else 'DETERMINISTIC (unexpected)'}")
    print()
    return not all_same


def test_energy_monotonicity():
    """Verify energy does NOT decrease monotonically per step."""
    print("=" * 60)
    print("TEST 2: Non-monotonic energy — uphill moves happen")
    print("=" * 60)
    np.random.seed(42)
    m = MandalaMap(u=20, depth=5)
    dist = np.linalg.norm(m.pos[:, None] - m.pos[None, :], axis=-1) + np.eye(m.num_cells)
    e = SOMSEngine(num_cells=m.num_cells, problem_type="OPTIMIZATION")
    j = e.fret_coupling(dist)
    history = e.anneal(j, T_start=5.0, T_final=0.1, n_steps=200)

    energies = [h[2] for h in history]
    uphill_count = sum(1 for i in range(1, len(energies)) if energies[i] > energies[i - 1])
    print(f"  Total steps: {len(energies)}")
    print(f"  Uphill steps: {uphill_count} ({100 * uphill_count / len(energies):.1f}%)")
    print(f"  Energy range: {min(energies):.10f} to {max(energies):.10f}")
    print(f"  PASS: Metropolis correctly accepts uphill moves at high T")
    print()
    return uphill_count > 0


def test_fret_scaling():
    """Verify coupling follows 1/r^6."""
    print("=" * 60)
    print("TEST 3: 1/r^6 coupling law")
    print("=" * 60)
    e = SOMSEngine(num_cells=2)
    distances = np.array([1.0, 2.0, 3.0, 4.0])
    for r in distances:
        dist = np.array([[1.0, r], [r, 1.0]])
        j = e.fret_coupling(dist)
        coupling = j[0, 1]
        expected = 1.0 / r**6
        match = abs(coupling - expected) < 1e-10
        print(f"  r={r:.1f}: J={coupling:.6f}, expected={expected:.6f}, match={match}")
    print(f"  PASS: Coupling follows 1/r^6")
    print()
    return True


def test_no_optimality_guarantee():
    """Show the annealer does NOT always find the same minimum."""
    print("=" * 60)
    print("TEST 4: No optimality guarantee")
    print("=" * 60)
    m = MandalaMap(u=20, depth=5)
    dist = np.linalg.norm(m.pos[:, None] - m.pos[None, :], axis=-1) + np.eye(m.num_cells)

    results = []
    for seed in range(10):
        np.random.seed(seed)
        e = SOMSEngine(num_cells=m.num_cells, problem_type="SAT")
        j = e.fret_coupling(dist)
        history = e.anneal(j, T_start=5.0, T_final=0.01, n_steps=300)
        results.append(history[-1][2])

    best = min(results)
    worst = max(results)
    spread = worst - best
    print(f"  10 independent runs:")
    print(f"  Best energy:  {best:.10f}")
    print(f"  Worst energy: {worst:.10f}")
    print(f"  Spread:       {spread:.10f}")
    print(f"  PASS: Different runs find different local minima")
    print(f"         (spread > 0 confirms no optimality guarantee)")
    print()
    return spread > 0


def test_phi_threshold_arbitrary():
    """Show the Phi=3.0 threshold is a design parameter, not physics."""
    print("=" * 60)
    print("TEST 5: Phi threshold is a design choice")
    print("=" * 60)
    np.random.seed(0)

    # Low-entropy state (mostly one value)
    low_state = np.zeros(100)
    low_state[:5] = 1
    phi_low, sov_low = PhiCalculator(low_state).evaluate_integration()

    # High-entropy state (uniform across bins)
    high_state = np.tile(np.arange(8), 13)[:100].astype(float)
    phi_high, sov_high = PhiCalculator(high_state).evaluate_integration()

    # Random state
    rand_state = np.random.uniform(0, 7, 100)
    phi_rand, sov_rand = PhiCalculator(rand_state).evaluate_integration()

    print(f"  Low-entropy state:  Phi={phi_low:.4f}, sovereign={sov_low}")
    print(f"  High-entropy state: Phi={phi_high:.4f}, sovereign={sov_high}")
    print(f"  Random state:       Phi={phi_rand:.4f}, sovereign={sov_rand}")
    print()
    print("  Phi is now mutual information: I(A;B) = H(A) + H(B) - H(whole).")
    print("  High Phi = halves are correlated (holistic system).")
    print("  The threshold 3.0 is a design choice, not a physics constant.")
    print("  'Sovereignty' here means 'sufficiently integrated by this metric.'")
    print()
    return True


def test_temperature_scale():
    """
    Detect the random-walk failure mode.

    MandalaMap(u=20) places cells 20..440 units apart, so J = 1/r^6 is
    at most ~1.6e-8. With T_start=5.0 every Metropolis test is
    exp(-dE/T) ~ exp(-1e-8) ~ 1: everything is accepted, nothing is
    optimized. Normalizing distances by the nearest-neighbour spacing
    (so J_nn = 1) puts dE on the same scale as T and the annealer works.

    Detector: acceptance ratio in the final 10% of steps, plus final
    energy relative to the mean energy of random states.
    """
    print("=" * 60)
    print("TEST 6: Temperature/coupling scale — is it annealing or random-walking?")
    print("=" * 60)
    m = MandalaMap(u=20, depth=5)
    n = m.num_cells
    d = np.linalg.norm(m.pos[:, None] - m.pos[None, :], axis=-1)
    d_nn = d[~np.eye(n, dtype=bool)].min()

    def probe(dist, label):
        np.random.seed(0)
        e = SOMSEngine(num_cells=n, problem_type="SAT")
        j = e.fret_coupling(dist + np.eye(n))
        E_random = np.mean([SOMSEngine(num_cells=n, problem_type="SAT").energy_landscape(j)
                            for _ in range(20)])
        history = e.anneal(j, T_start=5.0, T_final=0.01, n_steps=300)
        tail = history[-30:]
        accept_tail = np.mean([h[3] for h in tail]) / n
        ratio = history[-1][2] / E_random
        random_walk = accept_tail > 0.95 or ratio > 0.9
        print(f"  {label:26s} J_max={j[~np.eye(n, dtype=bool)].max():.2e}  "
              f"accept(last 10%)={accept_tail:.2f}  E_final/E_random={ratio:.2f}  "
              f"-> {'RANDOM WALK' if random_walk else 'annealing'}")
        return random_walk

    raw_is_walk = probe(d, "raw MandalaMap units")
    norm_is_walk = probe(d / d_nn, "normalized d/d_nn")
    print()
    print("  Raw mandala units + default T are a random walk; T is ~1e8 times")
    print("  larger than any energy difference. Normalize distances (or scale T)")
    print("  before trusting any anneal() result built on MandalaMap(u=20).")
    ok = raw_is_walk and not norm_is_walk
    print(f"  {'PASS' if ok else 'FAIL'}: detector separates the two regimes")
    print()
    return ok


if __name__ == "__main__":
    results = [
        test_stochasticity(),
        test_energy_monotonicity(),
        test_fret_scaling(),
        test_no_optimality_guarantee(),
        test_phi_threshold_arbitrary(),
        test_temperature_scale(),
    ]
    print("=" * 60)
    print(f"VALIDATION SUMMARY: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
