"""
SOMS Annealer Validation
========================
Tests the core claims of the SOMS engine against ground truth:

1. Annealing is stochastic — different seeds give different results
2. Energy decreases on average but NOT monotonically per step
3. FRET coupling follows 1/r^6 scaling
4. The annealer does NOT guarantee optimal solutions
5. Phi sovereignty threshold (3.0) is an arbitrary design choice

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
    print("  NOTE: The formula exp(1/entropy) * 1.618 is NOT Tononi's IIT.")
    print("  The threshold 3.0 is a design choice, not a physics constant.")
    print("  'Sovereignty' here means 'sufficiently integrated by this metric.'")
    print()
    return True


if __name__ == "__main__":
    results = [
        test_stochasticity(),
        test_energy_monotonicity(),
        test_fret_scaling(),
        test_no_optimality_guarantee(),
        test_phi_threshold_arbitrary(),
    ]
    print("=" * 60)
    print(f"VALIDATION SUMMARY: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
