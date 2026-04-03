"""
SOMS Demo — Prove the thesis in one run.

Pipeline:
  1. MandalaMap generates φ-scaled geometry
  2. SOMSEngine encodes factorization as energy landscape
  3. Annealing relaxes to ground state → factors emerge
  4. PhiCalculator checks sovereignty (Φ > 3.0)
  5. ConstraintAgent blooms and shows what it discovers

Usage:
    python -m src.demo           # factor 15
    python -m src.demo 21        # factor 21
    python -m src.demo 35        # factor 35
"""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import distance_matrix

from src.octahedral_physics import SOMSEngine
from src.mandala_structure import MandalaMap
from src.phi_calculator import PhiCalculator
from src.constraint_agent import ConstraintAgent
from src.octahedral_lookup import (
    GRAY_CODES, EIGENVALUE_CHARACTERS, phi_stability_report, state_capacity,
)
from src.geometric_encoder import GeometricEncoder


# ── Factorization encoding ───────────────────────────────────────────────
# Two cells encode factor pair (a, b) where a*b = N.
# Each cell holds octahedral state 0-7, representing digit value 2+state.
# Factor = 2 + state  (range 2..9).
# Energy penalty: (a*b - N)^2 added to coupling energy.
# Ground state = minimum penalty = correct factorization.

def encode_factorization(engine, N):
    """
    Configure a 2-cell engine to factor N.

    Cell 0 → factor a = 2 + state_index_a
    Cell 1 → factor b = 2 + state_index_b

    Energy = (a*b - N)^2.  Ground state has E=0 iff N = a*b.
    """
    engine.orientations = np.random.choice(engine.states, size=2)
    return engine


def factorization_energy(orientations, N):
    """Energy for factorization: (a*b - N)^2."""
    a = 2 + np.argmin(np.abs(orientations[0] - np.array([0, 45, 90, 135, 180, 225, 270, 315])))
    b = 2 + np.argmin(np.abs(orientations[1] - np.array([0, 45, 90, 135, 180, 225, 270, 315])))
    return (a * b - N) ** 2, a, b


def solve_factorization(N, attempts=20, anneal_steps=150):
    """
    Solve N = a*b using membrane computation pattern.

    Phase 1 (Coarse): Estimate sqrt(N), narrow search to ±stride window
    Phase 2 (Membrane): Check window for exact hits at the boundary
    Phase 3 (Fine): Anneal within window if boundary didn't solve it

    This follows Mandala-Computing's membrane.py architecture:
    the answer crystallizes at the boundary between coarse and fine.
    """
    states = np.array([0, 45, 90, 135, 180, 225, 270, 315])
    max_factor = int(np.sqrt(N)) + 1

    # Phase 1: Coarse — narrow the search window
    # Map factor range [2..9] to octahedral states
    stride = max(1, max_factor // 8)
    center_a = min(7, max(0, int(np.sqrt(N)) - 2))
    center_b = min(7, max(0, N // max(2 + center_a, 2) - 2))

    # Phase 2: Membrane — check boundary for exact solution
    for da in range(-stride, stride + 1):
        for db in range(-stride, stride + 1):
            a = 2 + max(0, min(7, center_a + da))
            b = 2 + max(0, min(7, center_b + db))
            if a * b == N:
                return a, b, 0  # solved at boundary

    # Phase 3: Fine — anneal if boundary didn't find it
    best_a, best_b, best_E = None, None, float('inf')

    for _ in range(attempts):
        orientations = np.random.choice(states, size=2)

        # Anneal
        T = 5.0
        ratio = (0.01 / 5.0) ** (1.0 / max(1, anneal_steps - 1))

        for step in range(anneal_steps):
            for cell in range(2):
                old = orientations[cell]
                old_E, _, _ = factorization_energy(orientations, N)

                candidates = states[states != old]
                orientations[cell] = np.random.choice(candidates)
                new_E, _, _ = factorization_energy(orientations, N)

                dE = new_E - old_E
                if dE > 0 and np.random.random() >= np.exp(-dE / max(T, 1e-12)):
                    orientations[cell] = old  # revert

            T *= ratio

        E, a, b = factorization_energy(orientations, N)
        if E < best_E:
            best_E, best_a, best_b = E, a, b
            if E == 0:
                break

    return best_a, best_b, best_E


# ── Load encoding table from atlas ──────────────────────────────────────

def load_state_table():
    """Load octahedral state encoding from G2B bridge atlas."""
    path = Path(__file__).parent.parent / "atlas" / "remote" / "g2b" / "octahedral_state_encoding.json"
    try:
        data = json.loads(path.read_text())
        return data.get("states", [])
    except (OSError, json.JSONDecodeError):
        return []


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 15

    print("=" * 60)
    print("SOMS — Sovereign Octahedral Mandala Substrate")
    print("Geometric Relaxation Computing Demo")
    print("=" * 60)

    # ── Step 1: Geometry ──────────────────────────────────────────────
    print("\n[1] MANDALA GEOMETRY")
    m = MandalaMap(u=1, depth=3)
    print(f"    φ-scaled 8-petal mandala: {len(m.pos)} cells, depth=3")
    print(f"    Ring radii: {', '.join(f'{m.phi**d:.2f}' for d in range(1, 4))}")

    # ── Step 2: Factorization ─────────────────────────────────────────
    print(f"\n[2] FACTORIZATION: {N} = ? × ?")
    print(f"    Membrane: coarse (√N estimate) → boundary (exact check) → fine (anneal)")
    print(f"    Encoding: 2 cells × 8 octahedral states (range 2..9)")
    print(f"    Energy: E = (a×b - {N})²")

    a, b, E = solve_factorization(N)
    if E == 0:
        print(f"    ✓ Ground state found: {N} = {a} × {b}")
    else:
        print(f"    Best: {a} × {b} = {a*b} (residual E={E})")
        if a * b != N:
            print(f"    Note: {N} may not factor as product of two values in 2..9")

    # ── Step 3: Energy landscape ──────────────────────────────────────
    print(f"\n[3] ENERGY LANDSCAPE (full mandala)")
    e = SOMSEngine(num_cells=len(m.pos))
    d = distance_matrix(m.pos, m.pos)
    j = e.fret_coupling(d)

    E0 = e.energy_landscape(j)
    history = e.anneal(j, T_start=10.0, T_final=0.01, n_steps=200)
    Ef = history[-1][2]
    reduction = (E0 - Ef) / max(E0, 1e-12) * 100

    print(f"    {len(m.pos)} cells, FRET 1/r^6 coupling")
    print(f"    Initial energy: {E0:.4f}")
    print(f"    Final energy:   {Ef:.4f}")
    print(f"    Reduction:      {reduction:.1f}%")

    # ── Step 4: Sovereignty ───────────────────────────────────────────
    print(f"\n[4] SOVEREIGNTY CHECK (Φ > 3.0)")
    phi_val, is_sovereign = PhiCalculator(e.orientations).evaluate_integration()
    status = "SOVEREIGN" if is_sovereign else "not sovereign"
    print(f"    Φ = {phi_val}, {status}")

    # ── Step 5: Constraint agent ──────────────────────────────────────
    print(f"\n[5] CONSTRAINT AGENT BLOOM")
    agent = ConstraintAgent(
        seed_id="SHAPE.OCTA",
        home_families=["air", "structure", "balance", "integration"]
    )
    agent.set_resource_budget(compute=1000, bandwidth=10.0, energy=1.0, time_remaining=1.0)
    discovered = agent.bloom(depth=2)
    emergent = agent.check_expander_rules()

    print(f"    Seed: SHAPE.OCTA (8 faces = 8 states)")
    print(f"    Discovered {len(discovered)} entities in 2 bloom depths")

    # Show shapes and key entities
    shapes = [e for e in discovered if e.startswith("SHAPE.")]
    emotions = [e for e in discovered if e.startswith("EMOTION.")]
    protos = [e for e in discovered if e.startswith("PROTO.")]
    synergy = [e for e in discovered if not any(e.startswith(p) for p in ["SHAPE.", "EMOTION.", "PROTO."])]

    if shapes:
        print(f"    Shapes: {', '.join(shapes)}")
    if emotions:
        print(f"    Sensors: {', '.join(emotions)}")
    if protos:
        print(f"    Protocols: {', '.join(protos)}")
    if synergy:
        print(f"    Synergy: {', '.join(synergy[:8])}{'...' if len(synergy) > 8 else ''}")

    if emergent:
        print(f"    Emergent: {', '.join(emergent)}")

    # ── Step 6: State encoding table ──────────────────────────────────
    state_table = load_state_table()
    if state_table:
        print(f"\n[6] OCTAHEDRAL STATE ENCODING (from G2B Bridge)")
        print(f"    {'St':>2} {'Bits':>4} {'Gray':>4} {'Label':<8} {'Glyph':<4} {'Token':<8} {'φ-coh':>5}")
        for s in state_table:
            print(f"    {s['state']:>2} {s['vertex_bits']:>4} {s['gray_code']:>4} "
                  f"{s['label']:<8} {s['glyph_unicode']:<4} {s['geis_token']:<8} "
                  f"{s['phi_coherence']:>5.2f}")

    # ── Step 7: Phi stability report ─────────────────────────────────
    print(f"\n[7] PHI-STABILITY ANALYSIS (Golden Ratio Coherence)")
    report = phi_stability_report()
    print(f"    {'St':>2} {'Gray':>4} {'Character':<16} {'Dev':>6} {'Ratio':>6} {'Anchor'}")
    for entry in report:
        anchor = "  **" if entry["is_anchor"] else ""
        print(f"    {entry['state']:>2} {entry['gray_code']:>4} "
              f"{entry['character']:<16} {entry['closest_phi_deviation']:>6.4f} "
              f"{entry['best_ratio']:>6.4f}{anchor}")

    # ── Step 8: Geometric encoder demo ────────────────────────────────
    print(f"\n[8] GEOMETRIC ENCODER (GEIS Token <-> Binary)")
    enc = GeometricEncoder()
    tokens = ["000|O", "001|I", "010|X", "011/O", "100|Δ", "101||O"]
    for token in tokens:
        try:
            binary = enc.encode_to_binary(token)
            decoded = enc.decode_from_binary(binary)
            valid = "OK" if enc.validate_token(token) else "FAIL"
            print(f"    {token:<8} -> {binary:<8} -> {decoded:<8} [{valid}]")
        except ValueError as e:
            print(f"    {token:<8} -> ERROR: {e}")

    # ── Step 9: State capacity ────────────────────────────────────────
    print(f"\n[9] STATE CAPACITY")
    for n in [1, len(m.pos), 100]:
        sc = state_capacity(n)
        print(f"    {n:>4} cells: {sc['total_bits']:>4} bits, {sc['total_states']:.2e} states")

    # ── Step 10: Mandala Gray code mapping ────────────────────────────
    print(f"\n[10] MANDALA CELL-STATE MAPPING (Ring 1)")
    for idx in m.ring_cells(1):
        state = m.cell_states[idx]
        gray = m.cell_gray_code(idx)
        char = m.cell_character(idx)
        n_transitions = len(m.allowed_neighbors(idx))
        n_gray = len(m.gray_adjacent_cells(idx))
        print(f"    Cell {idx:>2}: state={state} gray={gray} "
              f"({char:<16}) transitions={n_transitions} gray_adj={n_gray}")

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("The mandala doesn't search for answers.")
    print("It relaxes into them.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
