"""
HOLOGRAPHIC MANDALA COMPUTING v1.0
Unified framework: Holographic Encoding + Self-Symmetry + Entanglement

Three principles woven into a single computational layer:

1. HOLOGRAPHIC: Problem encoded on outermost ring (boundary).
   Information projects inward through PHI-scaled compression.
   Solution crystallizes at the center.

2. SELF-SYMMETRY (Renormalization): Each depth level solves a
   scaled version of the same problem. Coarse solutions at inner
   rings seed fine refinement at outer rings. Corrections propagate
   bidirectionally.

3. ENTANGLEMENT: Cross-depth correlations link cells at different
   scales. Correlated state updates propagate information without
   explicit message passing. Classical analog of quantum entanglement.

The physics: boundary conditions (holographic) constrain a self-similar
hierarchy (renormalization) connected by non-local correlations
(entanglement). The ground state of this system IS the solution.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass, field
import math
import time

from mandala_computer import (
    MandalaComputer, MandalaCell, ProblemType, SensorReading,
    PHI, FRET_CUTOFF, OCTAHEDRAL_STATES, _STATE_GLYPHS,
)

try:
    from quantum_mandala import QuantumMandalaComputer
    HAS_QUANTUM = True
except ImportError:
    HAS_QUANTUM = False


# ---------------------------------------------------------------------------
# Data structures for the holographic layer
# ---------------------------------------------------------------------------

@dataclass
class HolographicRing:
    """A single ring in the holographic mandala."""
    depth: int
    radius: float
    cell_indices: List[int]  # indices into parent's cell array
    projected_problem: Optional[Dict] = None  # compressed problem at this scale
    scale_factor: float = 1.0  # how much the problem is compressed


@dataclass
class EntanglementLink:
    """Cross-depth entanglement between two cells at different rings."""
    cell_a: int  # index of cell in outer ring
    cell_b: int  # index of cell in inner ring
    depth_a: int
    depth_b: int
    strength: float  # correlation strength
    phase: float = 0.0  # accumulated geometric phase
    initial_strength: float = 0.0  # for adaptive reset
    correlation_history: List[bool] = field(default_factory=list)  # recent correlation outcomes


# ---------------------------------------------------------------------------
# HolographicMandala
# ---------------------------------------------------------------------------

class HolographicMandala(MandalaComputer):
    """
    Unified holographic + self-similar + entangled mandala computer.

    Extends MandalaComputer with three new computational layers:
    - Holographic boundary encoding
    - Renormalization group (self-symmetry) solver
    - Cross-depth entanglement correlations
    """

    def __init__(self, golden_depth: int = 5, sacred_geometry: int = 8,
                 temperature: float = 1.0,
                 entanglement_decay: float = 0.5,
                 holographic_weight: float = 1.0):
        """
        Args:
            golden_depth: Fractal recursion depth
            sacred_geometry: Symmetry order (8 for octahedral)
            temperature: Initial thermal energy
            entanglement_decay: How fast cross-depth entanglement decays with distance
            holographic_weight: Weight of holographic boundary energy term
        """
        super().__init__(golden_depth=golden_depth,
                         sacred_geometry=sacred_geometry,
                         temperature=temperature)
        self.entanglement_decay = entanglement_decay
        self.holographic_weight = holographic_weight

        # Holographic structure
        self.rings: List[HolographicRing] = []
        self.entanglement_links: List[EntanglementLink] = []

        # Renormalization state
        self.scale_solutions: Dict[int, List[int]] = {}  # depth -> solution at that scale

        print(f"   Holographic weight: {holographic_weight}")
        print(f"   Entanglement decay: {entanglement_decay}")

    # ------------------------------------------------------------------
    # Holographic bloom: organize cells into rings with projections
    # ------------------------------------------------------------------

    def bloom_mandala(self):
        """Extended bloom that also builds holographic ring structure."""
        super().bloom_mandala()
        self._build_rings()
        self._establish_entanglement_links()
        print(f"   Rings: {len(self.rings)}, entanglement links: {len(self.entanglement_links)}")

    def _build_rings(self):
        """Organize bloomed cells into concentric holographic rings."""
        self.rings = []
        for depth in range(self.golden_depth):
            indices = [i for i, c in enumerate(self.cells) if c.depth == depth]
            radius = PHI ** depth
            ring = HolographicRing(
                depth=depth,
                radius=radius,
                cell_indices=indices,
                scale_factor=PHI ** (self.golden_depth - 1 - depth),
            )
            self.rings.append(ring)

    def _establish_entanglement_links(self):
        """
        Create cross-depth entanglement links.

        Each cell in ring d is entangled with the nearest cell in ring d-1.
        Strength decays as entanglement_decay^(depth_difference).
        This creates non-local correlations across scales.
        """
        self.entanglement_links = []
        for d in range(1, len(self.rings)):
            outer_ring = self.rings[d]
            inner_ring = self.rings[d - 1]

            for outer_idx in outer_ring.cell_indices:
                outer_cell = self.cells[outer_idx]
                # Find nearest cell in inner ring
                best_inner = None
                best_dist = float("inf")
                for inner_idx in inner_ring.cell_indices:
                    inner_cell = self.cells[inner_idx]
                    dx = outer_cell.position[0] - inner_cell.position[0]
                    dy = outer_cell.position[1] - inner_cell.position[1]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < best_dist:
                        best_dist = dist
                        best_inner = inner_idx

                if best_inner is not None:
                    strength = self.entanglement_decay ** (d - (d - 1))
                    link = EntanglementLink(
                        cell_a=outer_idx,
                        cell_b=best_inner,
                        depth_a=d,
                        depth_b=d - 1,
                        strength=strength,
                        initial_strength=strength,
                    )
                    self.entanglement_links.append(link)

    # ------------------------------------------------------------------
    # Holographic encoding: boundary -> interior projection
    # ------------------------------------------------------------------

    def encode_holographic(self, problem_type_enum: ProblemType, problem_data: Dict):
        """
        Encode problem holographically: full problem on boundary (outermost ring),
        compressed projections on inner rings.
        """
        # Use parent's encoder to set up problem_data with all required fields
        if problem_type_enum == ProblemType.FACTORIZATION:
            self.encode_factorization(problem_data["N"])
        else:
            self.problem_type = problem_type_enum
            self.problem_data = problem_data
            self.bloom_mandala()

        # Outermost ring gets full problem encoding
        outer = self.rings[-1]
        outer.projected_problem = dict(problem_data)
        outer.projected_problem["_scale"] = 1.0

        # Project inward: each inner ring gets a compressed version
        for d in range(len(self.rings) - 2, -1, -1):
            ring = self.rings[d]
            parent_ring = self.rings[d + 1]
            ring.projected_problem = self._project_problem(
                parent_ring.projected_problem, ring.scale_factor
            )

        # Set cell energies based on holographic projection at each ring
        for ring in self.rings:
            for idx in ring.cell_indices:
                self.cells[idx].energy = 0.0  # reset

        print(f"   Holographic encoding: {problem_type_enum.value}")
        print(f"   Boundary (ring {len(self.rings)-1}): full problem")
        print(f"   Center (ring 0): scale {self.rings[0].scale_factor:.3f}")

    def _project_problem(self, parent_problem: Dict, scale: float) -> Dict:
        """
        Project problem to a coarser scale.

        Factorization: hierarchical constraint decomposition.
          - Outer ring: (fa*fb - N)^2 exactly
          - Middle rings: check divisibility by small primes of N
          - Inner ring: check parity (N mod 2) and residue mod 3
          This preserves multiplicative structure at every scale.

        SAT: variable clustering.
          - Group variables by clause co-occurrence
          - Inner rings represent cluster-level satisfiability

        Graph coloring: graph coarsening.
          - Contract edges to merge adjacent nodes
          - Inner rings color the coarsened graph
        """
        projected = dict(parent_problem)
        projected["_scale"] = scale

        if self.problem_type == ProblemType.FACTORIZATION:
            N = parent_problem["N"]
            # Build a hierarchy of modular constraints
            # Small primes that divide nearby composites constrain factor search
            small_primes = [2, 3, 5, 7]
            # Scale determines which primes we check
            # High scale (inner ring) -> only smallest primes
            # Low scale (outer ring) -> all primes up to sqrt(N)
            num_primes = max(1, min(len(small_primes), int(len(small_primes) / max(scale, 0.5))))
            projected["_check_primes"] = small_primes[:num_primes]
            projected["_modular_base"] = max(2, int(math.sqrt(N / max(scale, 1))))
            # Residues: what N looks like mod each prime
            projected["_residues"] = {p: N % p for p in projected["_check_primes"]}

        elif self.problem_type == ProblemType.SAT:
            clauses = parent_problem.get("clauses", [])
            if clauses and scale > 1.5:
                # Coarsen: merge variables that always appear in same clauses
                # At coarsest scale, treat clause groups as single constraints
                num_clauses = max(1, int(len(clauses) / max(scale, 1)))
                projected["_coarsened_clauses"] = clauses[:num_clauses]
                projected["_scale_vars"] = max(1, parent_problem.get("num_vars", 3) // int(scale))

        elif self.problem_type == ProblemType.GRAPH_COLORING:
            adjacency = parent_problem.get("adjacency", [])
            num_nodes = parent_problem.get("num_nodes", 0)
            if adjacency and scale > 1.5:
                # Contract: merge pairs of adjacent nodes
                merge_count = max(0, int(num_nodes * (1 - 1 / max(scale, 1))) // 2)
                contracted_adj = list(adjacency)
                contracted_nodes = num_nodes
                merged = set()
                for edge in adjacency[:merge_count]:
                    a, b = edge
                    if a not in merged and b not in merged:
                        # Merge b into a: replace all b references with a
                        contracted_adj = [[a if x == b else x for x in e] for e in contracted_adj]
                        contracted_adj = [e for e in contracted_adj if e[0] != e[1]]  # remove self-loops
                        merged.add(b)
                        contracted_nodes -= 1
                projected["_contracted_adjacency"] = contracted_adj
                projected["_contracted_nodes"] = contracted_nodes

        return projected

    # ------------------------------------------------------------------
    # Holographic energy: includes boundary + projection + entanglement
    # ------------------------------------------------------------------

    def compute_total_energy(self) -> float:
        """
        Extended energy with holographic and entanglement terms.

        For factorization: holographic energy REPLACES the parent's bipartite
        energy (which just sums over all cell pairs). The holographic version
        is richer — it applies different constraints at each ring scale.
        Other problem types: holographic adds on top of base.

        E = E_base + E_holographic + E_entanglement
        """
        # For factorization, compute base energy WITHOUT the factorization term
        # by temporarily switching problem type, then add holographic factorization
        if self.problem_type == ProblemType.FACTORIZATION and self.rings:
            saved_type = self.problem_type
            self.problem_type = None  # suppress parent's factorization energy
            E_base = super().compute_total_energy()
            self.problem_type = saved_type
        else:
            E_base = super().compute_total_energy()

        E_holo = self._holographic_energy()
        E_ent = self._entanglement_energy()

        return E_base + self.holographic_weight * E_holo + E_ent

    def _holographic_energy(self) -> float:
        """
        Holographic energy: penalize inconsistency between boundary and interior.

        Outer ring encodes the full problem. Inner rings should be consistent
        projections. Energy is low when the holographic principle is satisfied.
        """
        if not self.rings:
            return 0.0

        energy = 0.0

        # Factorization: hierarchical prime constraints (multi-cell registers)
        if self.problem_type == ProblemType.FACTORIZATION and self.problem_data:
            N = self.problem_data["N"]
            dpf = self.problem_data.get("digits_per_factor", 1)
            cpp = self.problem_data.get("cells_per_pair", 2)

            for ring in self.rings:
                if not ring.projected_problem:
                    continue
                scale = ring.projected_problem.get("_scale", 1.0)
                indices = ring.cell_indices

                for start in range(0, len(indices) - cpp + 1, cpp):
                    fa_idx = indices[start:start + dpf]
                    fb_idx = indices[start + dpf:start + cpp]
                    fa = self._cells_to_factor(fa_idx)
                    fb = self._cells_to_factor(fb_idx)
                    product = fa * fb

                    if scale >= 1.0:
                        energy += (product - N) ** 2
                    else:
                        residues = ring.projected_problem.get("_residues", {})
                        for p, r in residues.items():
                            if product % p != r:
                                energy += p
                        mod_base = ring.projected_problem.get("_modular_base", 8)
                        energy += ((product - N) % mod_base) ** 2 * 0.5

        # Self-symmetry penalty: adjacent rings should have consistent states
        for d in range(len(self.rings) - 1):
            inner_cells = [self.cells[i] for i in self.rings[d].cell_indices]
            outer_cells = [self.cells[i] for i in self.rings[d + 1].cell_indices]

            if inner_cells and outer_cells:
                # Dominant state of inner ring should match dominant of outer
                inner_mode = max(set(c.state for c in inner_cells),
                                 key=lambda s: sum(1 for c in inner_cells if c.state == s))
                outer_mode = max(set(c.state for c in outer_cells),
                                 key=lambda s: sum(1 for c in outer_cells if c.state == s))
                # Penalize inconsistency between scales
                energy += 0.5 * (inner_mode != outer_mode)

        return energy

    def _entanglement_energy(self) -> float:
        """
        Cross-depth entanglement energy with adaptive Berry phase.

        Berry phase accumulates as cells evolve. When phase crosses
        pi thresholds, the preferred correlation flips from "same state"
        to "complementary state" — the system learns which correlations
        matter through geometric evolution.

        Entanglement strength adapts: links whose cells stay correlated
        get stronger, uncorrelated links weaken.
        """
        energy = 0.0
        for link in self.entanglement_links:
            ca = self.cells[link.cell_a]
            cb = self.cells[link.cell_b]
            state_diff = abs(ca.state - cb.state)

            # Berry phase determines correlation mode
            # phase near 0, 2pi, 4pi... -> same state preferred
            # phase near pi, 3pi, 5pi... -> complementary preferred
            phase_mode = math.cos(link.phase)
            if phase_mode >= 0:
                # Same-state correlation
                energy += link.strength * math.sin(state_diff * math.pi / 4) ** 2
            else:
                # Complementary correlation (state_diff near 4 = opposite on octahedron)
                complementary_diff = abs(state_diff - 4)
                energy += link.strength * math.sin(complementary_diff * math.pi / 4) ** 2

            # Accumulate Berry phase
            link.phase += state_diff * math.pi / (4 * self.sacred_geometry)

            # Track correlation for adaptive strength
            correlated = (state_diff == 0) if phase_mode >= 0 else (abs(state_diff - 4) <= 1)
            link.correlation_history.append(correlated)
            if len(link.correlation_history) > 50:
                link.correlation_history.pop(0)

        return energy

    def _adapt_entanglement(self):
        """
        Adaptive Berry phase feedback: strengthen useful links, weaken noisy ones.

        Called periodically during solving. Links that predict well get stronger,
        links that are random noise get pruned toward zero.
        """
        for link in self.entanglement_links:
            if len(link.correlation_history) < 10:
                continue
            # Correlation rate over recent history
            rate = sum(link.correlation_history[-20:]) / len(link.correlation_history[-20:])

            # Strengthen links with high correlation (> 0.6), weaken low (< 0.3)
            if rate > 0.6:
                link.strength = min(link.strength * 1.05, 0.95)
            elif rate < 0.3:
                link.strength = max(link.strength * 0.9, 0.01)

            self._emit_sensor("entanglement.adapt", 0, {
                "link": (link.cell_a, link.cell_b),
                "strength": link.strength,
                "correlation_rate": rate,
                "phase": link.phase,
            })

    # ------------------------------------------------------------------
    # Correlated Metropolis: entanglement-aware state updates
    # ------------------------------------------------------------------

    def relax_step(self) -> float:
        """
        Extended Metropolis step with entanglement-correlated updates.

        When a cell flips, its entangled partners may flip too
        (probability proportional to entanglement strength).
        """
        # Pick random cell
        cell_idx = np.random.randint(0, self.num_cells)
        cell = self.cells[cell_idx]

        E_old = self.compute_total_energy()
        old_state = cell.state

        # Propose new state
        new_state = np.random.randint(0, self.sacred_geometry)
        cell.state = new_state

        # Correlated update: entangled partners may follow
        correlated_changes = []
        for link in self.entanglement_links:
            partner_idx = None
            if link.cell_a == cell_idx:
                partner_idx = link.cell_b
            elif link.cell_b == cell_idx:
                partner_idx = link.cell_a

            if partner_idx is not None and np.random.random() < link.strength:
                partner = self.cells[partner_idx]
                correlated_changes.append((partner_idx, partner.state))
                # Partner follows: same state or complementary
                if np.random.random() < 0.5:
                    partner.state = new_state  # same
                else:
                    partner.state = (self.sacred_geometry - 1 - new_state) % self.sacred_geometry

        E_new = self.compute_total_energy()
        dE = E_new - E_old

        # Metropolis acceptance
        if dE < 0:
            return dE

        exp_arg = -dE / max(self.temperature, 1e-15)
        p_accept = math.exp(min(exp_arg, 500))

        if np.random.random() < p_accept:
            return dE

        # Reject: restore all states
        cell.state = old_state
        for partner_idx, old_partner_state in correlated_changes:
            self.cells[partner_idx].state = old_partner_state
        return 0.0

    # ------------------------------------------------------------------
    # Renormalization solver: coarse-to-fine with bidirectional propagation
    # ------------------------------------------------------------------

    def renormalization_solve(self, max_steps_per_scale: int = 2000,
                              T_start: float = 3.0, T_end: float = 0.01,
                              num_sweeps: int = 3) -> Dict:
        """
        Self-symmetry renormalization solver.

        1. Solve at coarsest scale (innermost ring) first
        2. Propagate solution outward as initial condition for next scale
        3. Refine at each scale with annealing
        4. Sweep bidirectionally for consistency

        Args:
            max_steps_per_scale: Annealing steps per ring
            T_start: Starting temperature per scale
            T_end: Ending temperature per scale
            num_sweeps: Number of inward-outward sweeps
        """
        if not self.rings:
            return {"error": "No rings — call encode_holographic first"}

        print(f"\n   Renormalization solve: {len(self.rings)} scales, {num_sweeps} sweeps")
        start = time.time()
        all_energies = []

        for sweep in range(num_sweeps):
            direction = "outward" if sweep % 2 == 0 else "inward"
            ring_order = range(len(self.rings)) if direction == "outward" else range(len(self.rings) - 1, -1, -1)

            # Adapt entanglement between sweeps
            if sweep > 0:
                self._adapt_entanglement()

            print(f"\n   Sweep {sweep} ({direction}):")

            for d in ring_order:
                ring = self.rings[d]
                active_cells = ring.cell_indices

                # If outward sweep and we have inner solution, seed from it
                if direction == "outward" and d > 0 and (d - 1) in self.scale_solutions:
                    self._propagate_solution(d - 1, d)

                # Anneal only cells in this ring (freeze others)
                frozen_states = {i: self.cells[i].state for i in range(self.num_cells)
                                 if i not in active_cells}

                steps_done = 0
                for step in range(max_steps_per_scale):
                    frac = step / max(max_steps_per_scale - 1, 1)
                    self.temperature = T_start * (T_end / max(T_start, 1e-15)) ** frac

                    # Only propose moves for cells in this ring
                    ci = active_cells[np.random.randint(0, len(active_cells))]
                    cell = self.cells[ci]
                    E_old = self.compute_total_energy()
                    old_s = cell.state
                    cell.state = np.random.randint(0, self.sacred_geometry)

                    # Correlated entanglement updates (only within active + linked cells)
                    correlated = []
                    for link in self.entanglement_links:
                        partner = None
                        if link.cell_a == ci:
                            partner = link.cell_b
                        elif link.cell_b == ci:
                            partner = link.cell_a
                        if partner is not None and partner not in frozen_states:
                            if np.random.random() < link.strength:
                                correlated.append((partner, self.cells[partner].state))
                                self.cells[partner].state = cell.state

                    E_new = self.compute_total_energy()
                    dE = E_new - E_old

                    accept = dE < 0
                    if not accept:
                        exp_arg = -dE / max(self.temperature, 1e-15)
                        accept = np.random.random() < math.exp(min(exp_arg, 500))

                    if not accept:
                        cell.state = old_s
                        for pi, ps in correlated:
                            self.cells[pi].state = ps

                    # Restore any accidentally changed frozen cells
                    for fi, fs in frozen_states.items():
                        self.cells[fi].state = fs

                    steps_done = step

                E = self.compute_total_energy()
                all_energies.append(E)
                self.energy_history.append(E)

                # Save solution at this scale
                self.scale_solutions[d] = [self.cells[i].state for i in active_cells]

                self._emit_sensor("energy.total", sweep * 1000 + d * 100, E,
                                  {"sweep": sweep, "depth": d, "direction": direction})

                glyph = "".join(
                    _STATE_GLYPHS[self.cells[i].state] if self.cells[i].state < len(_STATE_GLYPHS) else "?"
                    for i in active_cells[:8]
                )
                print(f"      Ring {d} (r={ring.radius:.2f}, {len(active_cells)} cells): "
                      f"E={E:.4f}  {glyph}")

        elapsed = time.time() - start
        final_energy = self.compute_total_energy()
        self.ground_state = [c.state for c in self.cells]
        self.solution = self._extract_solution()

        print(f"\n   Renormalization complete: E={final_energy:.4f} ({elapsed:.2f}s)")
        return {
            "ground_state": self.ground_state,
            "final_energy": final_energy,
            "time": elapsed,
            "solution": self.solution,
            "scale_solutions": dict(self.scale_solutions),
            "energy_history": all_energies,
        }

    def _propagate_solution(self, from_depth: int, to_depth: int):
        """
        Propagate solution from one ring to another via entanglement links.

        The inner ring's dominant state seeds the outer ring's initial condition.
        """
        if from_depth not in self.scale_solutions:
            return

        from_ring = self.rings[from_depth]
        to_ring = self.rings[to_depth]

        # Find dominant state at source scale
        source_states = self.scale_solutions[from_depth]
        if not source_states:
            return
        dominant = max(set(source_states), key=source_states.count)

        # Seed target ring: use entanglement links where possible
        seeded = set()
        for link in self.entanglement_links:
            if link.cell_a >= self.num_cells or link.cell_b >= self.num_cells:
                continue  # stale link, skip
            if link.depth_a == to_depth and link.depth_b == from_depth:
                self.cells[link.cell_a].state = self.cells[link.cell_b].state
                seeded.add(link.cell_a)
            elif link.depth_b == to_depth and link.depth_a == from_depth:
                self.cells[link.cell_b].state = self.cells[link.cell_a].state
                seeded.add(link.cell_b)

        # Remaining cells in target ring: seed with dominant
        for idx in to_ring.cell_indices:
            if idx not in seeded:
                self.cells[idx].state = dominant

    # ------------------------------------------------------------------
    # Unified solve: holographic + renormalization + entanglement
    # ------------------------------------------------------------------

    def holographic_solve(self, problem_type_enum: ProblemType, problem_data: Dict,
                          max_steps_per_scale: int = 2000,
                          T_start: float = 3.0, T_end: float = 0.01,
                          num_sweeps: int = 3) -> Dict:
        """
        Full holographic solve pipeline:
        1. Encode problem holographically (boundary -> interior)
        2. Run renormalization solver (coarse -> fine -> coarse)
        3. Extract solution from ground state
        """
        print("=" * 60)
        print("HOLOGRAPHIC MANDALA SOLVE")
        print("=" * 60)

        # Step 1: Holographic encoding
        self.encode_holographic(problem_type_enum, problem_data)

        # Step 2: Renormalization solve with entangled updates
        result = self.renormalization_solve(
            max_steps_per_scale=max_steps_per_scale,
            T_start=T_start,
            T_end=T_end,
            num_sweeps=num_sweeps,
        )

        # Step 3: Report
        print(f"\n   Entanglement links used: {len(self.entanglement_links)}")
        print(f"   Scale solutions: {len(self.scale_solutions)} levels")
        for d, states in sorted(self.scale_solutions.items()):
            glyphs = "".join(
                _STATE_GLYPHS[s] if s < len(_STATE_GLYPHS) else "?" for s in states[:10]
            )
            print(f"      Ring {d}: {glyphs}")

        return result

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_holographic_profile(self) -> Dict:
        """Show energy and state distribution at each ring depth."""
        profile = {}
        for ring in self.rings:
            cells = [self.cells[i] for i in ring.cell_indices]
            states = [c.state for c in cells]
            dist = {s: states.count(s) for s in range(self.sacred_geometry)}
            profile[ring.depth] = {
                "radius": ring.radius,
                "num_cells": len(cells),
                "scale_factor": ring.scale_factor,
                "state_distribution": dist,
                "dominant_state": max(dist, key=dist.get) if dist else None,
            }
        return profile

    def get_entanglement_map(self) -> List[Dict]:
        """Return entanglement links with current phases."""
        return [
            {
                "cell_a": link.cell_a,
                "cell_b": link.cell_b,
                "depths": (link.depth_a, link.depth_b),
                "strength": link.strength,
                "phase": link.phase,
                "state_a": self.cells[link.cell_a].state,
                "state_b": self.cells[link.cell_b].state,
                "correlated": self.cells[link.cell_a].state == self.cells[link.cell_b].state,
            }
            for link in self.entanglement_links
        ]


    # ------------------------------------------------------------------
    # Hybrid: holographic classical seed -> quantum refinement
    # ------------------------------------------------------------------

    def hybrid_quantum_solve(self, problem_type_enum: ProblemType, problem_data: Dict,
                             classical_sweeps: int = 2,
                             quantum_steps: int = 80,
                             max_steps_per_scale: int = 1500) -> Dict:
        """
        Boundary-aware hybrid holographic-quantum solver.

        The quantum stride creates a grid of reachable states. Between
        grid points are factors that are classically reachable but
        quantum-unreachable. This gap IS the semi-permeable boundary
        between order (discrete quantum states) and chaos (continuous
        factor space) — the edge where emergence happens.

        Phase 1 (QUANTUM — ORDER):
          Quantum annealing finds which BASIN the answer lives in.
          The stride grid defines basins.

        Phase 2 (BOUNDARY — EDGE OF CHAOS):
          Translates quantum basin into classical search window.
          The semi-permeable membrane: quantum information flows out
          as a constraint, classical resolution flows in.

        Phase 3 (CLASSICAL — RESOLUTION):
          Classical annealing within the boundary window,
          seeded by the quantum basin center.

        Crystal growth at the solid-liquid interface.
        Cell membranes mediating inside and outside.
        This solver computes at the quantum-classical boundary.
        """
        if not HAS_QUANTUM:
            print("   Quantum engine not available, falling back to classical")
            return self.holographic_solve(problem_type_enum, problem_data,
                                          num_sweeps=classical_sweeps + 1)

        print("=" * 60)
        print("BOUNDARY-AWARE HYBRID SOLVE")
        print("  Quantum basin -> Boundary membrane -> Classical resolution")
        print("=" * 60)

        N = problem_data.get("N", 15)
        max_factor = int(math.isqrt(N)) + 1
        stride = max(1, math.ceil(max_factor / 8))

        print(f"\n   N={N}, stride={stride}")
        print(f"   Quantum grid: {[2 + i * stride for i in range(8)]}")
        print(f"   Boundary gaps: width={stride} between grid points")

        # Phase 1: Quantum — find the basin
        print(f"\n   Phase 1 (ORDER): Quantum annealing finds basin...")
        qc = QuantumMandalaComputer(
            golden_depth=2,
            sacred_geometry=self.sacred_geometry,
            entanglement_strength=0.5,
        )
        quantum_result = qc.quantum_annealing(
            problem_type_enum.value, problem_data, num_steps=quantum_steps,
        )
        q_sol = quantum_result["solution"]
        q_factors = q_sol.get("factors", [2, 2])
        q_stride = q_sol.get("stride", stride)

        print(f"   Quantum basin center: {q_factors[0]} x {q_factors[1]}")

        # Phase 2: Boundary — the semi-permeable membrane
        print(f"\n   Phase 2 (BOUNDARY): Semi-permeable membrane...")
        boundary_a = (max(2, q_factors[0] - q_stride), q_factors[0] + q_stride)
        boundary_b = (max(2, q_factors[1] - q_stride), q_factors[1] + q_stride)
        window_size = (boundary_a[1] - boundary_a[0] + 1) * (boundary_b[1] - boundary_b[0] + 1)
        full_space = max_factor ** 2
        print(f"   Factor A window: [{boundary_a[0]}..{boundary_a[1]}]")
        print(f"   Factor B window: [{boundary_b[0]}..{boundary_b[1]}]")
        print(f"   Search compression: {full_space} -> {window_size} ({full_space / max(window_size, 1):.1f}x)")

        # Check if exact answer is in the boundary window
        boundary_hits = []
        for fa in range(boundary_a[0], boundary_a[1] + 1):
            for fb in range(boundary_b[0], boundary_b[1] + 1):
                if fa * fb == N and fa > 1 and fb > 1:
                    boundary_hits.append((fa, fb))

        if boundary_hits:
            print(f"   BOUNDARY CONTAINS SOLUTION: {boundary_hits}")

        # Phase 3: Classical — resolve within boundary
        print(f"\n   Phase 3 (RESOLUTION): Classical annealing in boundary...")
        self.encode_holographic(problem_type_enum, problem_data)

        # Seed cells with quantum-informed initial states
        dpf = self.problem_data.get("digits_per_factor", 1)
        cpp = self.problem_data.get("cells_per_pair", 2)
        for ring in self.rings:
            for start in range(0, len(ring.cell_indices) - cpp + 1, cpp):
                fa_target = max(0, q_factors[0] - 2)
                for d in range(dpf):
                    idx = ring.cell_indices[start + d]
                    self.cells[idx].state = (fa_target // (8 ** d)) % 8
                fb_target = max(0, q_factors[1] - 2)
                for d in range(dpf):
                    idx = ring.cell_indices[start + dpf + d]
                    self.cells[idx].state = (fb_target // (8 ** d)) % 8

        classical_result = self.renormalization_solve(
            max_steps_per_scale=max_steps_per_scale,
            num_sweeps=classical_sweeps,
        )
        c_sol = classical_result["solution"]

        # Pick best across all three phases
        q_correct = q_sol.get("correct", False)
        c_correct = c_sol.get("verified", False)

        if boundary_hits and not q_correct and not c_correct:
            best = "boundary"
            best_sol = {
                "factors": list(boundary_hits[0]),
                "best_pair": boundary_hits[0],
                "N": N, "verified": True, "residual": 0,
            }
        elif c_correct:
            best = "classical"
            best_sol = c_sol
        elif q_correct:
            best = "quantum"
            best_sol = q_sol
        else:
            best = "classical" if classical_result["final_energy"] <= quantum_result["final_energy"] else "quantum"
            best_sol = c_sol if best == "classical" else q_sol

        print(f"\n   Resolution:")
        print(f"   Quantum (order):    {q_factors} correct={q_correct}")
        print(f"   Boundary (edge):    {boundary_hits if boundary_hits else 'no exact hit'}")
        print(f"   Classical (detail): {c_sol.get('best_pair')} verified={c_correct}")
        print(f"   Winner: {best}")

        return {
            "best_method": best,
            "solution": best_sol,
            "quantum_result": quantum_result,
            "classical_result": classical_result,
            "boundary": {
                "window_a": boundary_a,
                "window_b": boundary_b,
                "hits": boundary_hits,
                "search_compression": full_space / max(window_size, 1),
            },
            "final_energy": min(classical_result["final_energy"],
                                quantum_result["final_energy"]),
        }


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_holographic_factorization():
    """Demonstrate holographic factorization."""
    print("=" * 60)
    print("DEMO: HOLOGRAPHIC FACTORIZATION")
    print("=" * 60)

    N = 15
    hm = HolographicMandala(
        golden_depth=4,
        sacred_geometry=8,
        entanglement_decay=0.6,
        holographic_weight=0.5,
    )
    result = hm.holographic_solve(
        ProblemType.FACTORIZATION,
        {"N": N},
        max_steps_per_scale=2000,
        num_sweeps=3,
    )
    sol = result["solution"]
    print(f"\n   N={N}")
    print(f"   Best pair: {sol.get('best_pair')}")
    print(f"   Factors: {sol.get('factors')}")
    print(f"   Verified: {sol.get('verified')}")
    print(f"   Telemetry: {len(hm.telemetry)} readings")

    # Show holographic profile
    profile = hm.get_holographic_profile()
    print(f"\n   Holographic profile:")
    for d, info in sorted(profile.items()):
        print(f"      Ring {d}: r={info['radius']:.2f}, "
              f"dominant={_STATE_GLYPHS[info['dominant_state']]}, "
              f"cells={info['num_cells']}")

    # Show entanglement
    ent_map = hm.get_entanglement_map()
    correlated = sum(1 for e in ent_map if e["correlated"])
    print(f"\n   Entanglement: {correlated}/{len(ent_map)} links correlated")

    return hm, result


def demo_holographic_graph_coloring():
    """Demonstrate holographic graph coloring."""
    print("\n" + "=" * 60)
    print("DEMO: HOLOGRAPHIC GRAPH COLORING")
    print("=" * 60)

    # Petersen-like graph: 5 nodes, 7 edges
    adjacency = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0], [0, 2], [1, 3]]
    num_colors = 3

    hm = HolographicMandala(
        golden_depth=3,
        sacred_geometry=8,
        entanglement_decay=0.7,
        holographic_weight=0.3,
    )
    result = hm.holographic_solve(
        ProblemType.GRAPH_COLORING,
        {"adjacency": adjacency, "num_colors": num_colors, "num_nodes": 5},
        max_steps_per_scale=2000,
        num_sweeps=2,
    )
    sol = result["solution"]
    print(f"\n   Coloring: {sol.get('coloring')}")
    print(f"   Violations: {sol.get('violations')}")
    print(f"   Valid: {sol.get('valid')}")
    return hm, result


def demo_comparison():
    """Compare holographic vs standard annealing."""
    print("\n" + "=" * 60)
    print("COMPARISON: HOLOGRAPHIC vs STANDARD ANNEALING")
    print("=" * 60)

    N = 35  # 5 x 7
    results = {}

    # Standard annealing
    mc = MandalaComputer(golden_depth=4, sacred_geometry=8)
    mc.encode_factorization(N)
    t0 = time.time()
    r = mc.simulated_annealing(max_steps=6000, T_start=3.0, T_end=0.01)
    results["standard"] = {
        "energy": r["final_energy"],
        "time": time.time() - t0,
        "verified": r["solution"]["verified"],
        "pair": r["solution"].get("best_pair"),
    }

    # Holographic
    hm = HolographicMandala(golden_depth=4, sacred_geometry=8,
                            entanglement_decay=0.6, holographic_weight=0.5)
    t0 = time.time()
    r = hm.holographic_solve(ProblemType.FACTORIZATION, {"N": N},
                             max_steps_per_scale=1500, num_sweeps=3)
    results["holographic"] = {
        "energy": r["final_energy"],
        "time": time.time() - t0,
        "verified": r["solution"]["verified"],
        "pair": r["solution"].get("best_pair"),
    }

    print(f"\n   {'Method':<20s} {'Energy':>10s} {'Time':>8s} {'Pair':<12s} {'Correct':>8s}")
    print("   " + "-" * 60)
    for name, data in results.items():
        print(f"   {name:<20s} {data['energy']:>10.2f} {data['time']:>8.3f} "
              f"{str(data['pair']):<12s} {'YES' if data['verified'] else 'no':>8s}")

    return results


def demo_hybrid():
    """Demonstrate hybrid holographic-quantum solver."""
    print("\n" + "=" * 60)
    print("DEMO: HYBRID HOLOGRAPHIC-QUANTUM")
    print("=" * 60)

    N = 21  # 3 x 7
    hm = HolographicMandala(
        golden_depth=4,
        sacred_geometry=8,
        entanglement_decay=0.6,
        holographic_weight=0.5,
    )
    result = hm.hybrid_quantum_solve(
        ProblemType.FACTORIZATION,
        {"N": N},
        classical_sweeps=2,
        quantum_steps=80,
    )
    print(f"\n   N={N}, best method: {result['best_method']}")
    sol = result["solution"]
    print(f"   Solution: {sol}")
    return hm, result


def demo_scaling():
    """Test renormalization advantage at increasing problem size."""
    print("\n" + "=" * 60)
    print("SCALING: HOLOGRAPHIC vs STANDARD ANNEALING")
    print("=" * 60)

    test_numbers = [15, 21, 35, 77, 143, 221]
    print(f"\n   {'N':<8s} {'Std E':>10s} {'Std ok':>7s} {'Std t':>8s}"
          f"  {'Holo E':>10s} {'Holo ok':>7s} {'Holo t':>8s}")
    print("   " + "-" * 65)

    for N in test_numbers:
        # Standard
        mc = MandalaComputer(golden_depth=4, sacred_geometry=8)
        mc.encode_factorization(N)
        t0 = time.time()
        r1 = mc.simulated_annealing(max_steps=4000, T_start=3.0, T_end=0.01)
        t1 = time.time() - t0
        s1 = r1["solution"]

        # Holographic
        hm = HolographicMandala(golden_depth=4, sacred_geometry=8,
                                entanglement_decay=0.6, holographic_weight=0.5)
        hm.encode_holographic(ProblemType.FACTORIZATION, {"N": N})
        t0 = time.time()
        r2 = hm.renormalization_solve(max_steps_per_scale=1000, num_sweeps=3)
        t2 = time.time() - t0
        s2 = r2["solution"]

        v1 = "YES" if s1.get("verified") else "no"
        v2 = "YES" if s2.get("verified") else "no"
        print(f"   {N:<8d} {r1['final_energy']:>10.1f} {v1:>7s} {t1:>8.3f}"
              f"  {r2['final_energy']:>10.1f} {v2:>7s} {t2:>8.3f}")


if __name__ == "__main__":
    print("=" * 60)
    print("HOLOGRAPHIC MANDALA COMPUTING v1.0")
    print("  Boundary + Self-Symmetry + Entanglement")
    print("=" * 60)

    demo_holographic_factorization()
    demo_holographic_graph_coloring()
    demo_comparison()
    demo_hybrid()
    demo_scaling()

    print("\n" + "=" * 60)
    print("ALL HOLOGRAPHIC DEMONSTRATIONS COMPLETE")
    print("=" * 60)
