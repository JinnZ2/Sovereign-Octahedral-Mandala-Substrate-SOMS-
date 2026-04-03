"""
Holographic Engine — Boundary encoding + renormalization + entanglement.

Adapted from Mandala-Computing/holographic_mandala.py to work natively
with SOMS's SOMSEngine + MandalaMap (no external MandalaComputer dependency).

Three computational principles woven into SOMSEngine:

1. HOLOGRAPHIC:  Problem encoded on the outermost mandala ring (boundary).
   Information projects inward through PHI-scaled compression.
   Solution crystallizes at the center.

2. RENORMALIZATION (Self-Symmetry):  Each depth level solves a scaled
   version of the same problem.  Coarse solutions seed fine refinement.
   Corrections propagate bidirectionally.

3. ENTANGLEMENT:  Cross-depth correlations link cells at different
   scales.  Correlated state updates propagate information without
   explicit message passing — classical analog of quantum entanglement.

Usage:
    from src.holographic_engine import HolographicEngine
    from src.mandala_structure import MandalaMap
    m = MandalaMap(u=20, depth=5)
    he = HolographicEngine(m)
    he.build()
    result = he.renormalization_anneal(j_ij, n_sweeps=3)

Source: github.com/JinnZ2/Mandala-Computing  (CC0 / MIT)
"""

from __future__ import annotations
import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

from src.octahedral_lookup import PHI
from src.mandala_structure import MandalaMap
from src.octahedral_physics import SOMSEngine


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class HolographicRing:
    """A single concentric ring in the mandala."""
    depth: int
    radius: float
    cell_indices: List[int]
    scale_factor: float = 1.0


@dataclass
class EntanglementLink:
    """Cross-depth entanglement between cells at different rings."""
    cell_a: int          # outer ring cell
    cell_b: int          # inner ring cell
    depth_a: int
    depth_b: int
    strength: float
    phase: float = 0.0
    initial_strength: float = 0.0
    correlation_history: List[bool] = field(default_factory=list)


# ---------------------------------------------------------------------------
# HolographicEngine
# ---------------------------------------------------------------------------

class HolographicEngine:
    """
    Holographic + renormalization + entanglement layer on top of
    a MandalaMap geometry and SOMSEngine physics.

    This does NOT subclass SOMSEngine — it wraps one.  The engine's
    dual-pathway energy (angular + tensor) remains intact; the
    holographic layer adds a third energy term and a multi-scale
    solving strategy.
    """

    def __init__(self, mandala: MandalaMap,
                 problem_type: str = "OPTIMIZATION",
                 entanglement_decay: float = 0.5,
                 holographic_weight: float = 1.0):
        self.mandala = mandala
        self.engine = SOMSEngine(num_cells=mandala.num_cells, problem_type=problem_type)
        self.entanglement_decay = entanglement_decay
        self.holographic_weight = holographic_weight

        self.rings: List[HolographicRing] = []
        self.entanglement_links: List[EntanglementLink] = []
        self.scale_solutions: Dict[int, List[int]] = {}

    # ------------------------------------------------------------------
    # Build ring + entanglement structure
    # ------------------------------------------------------------------

    def build(self):
        """Organize mandala cells into rings and establish entanglement."""
        self._build_rings()
        self._establish_entanglement()
        return self

    def _build_rings(self):
        self.rings = []
        max_depth = self.mandala.depth
        for d in range(max_depth + 1):
            indices = self.mandala.ring_cells(d)
            ring = HolographicRing(
                depth=d,
                radius=PHI ** d if d > 0 else 0.0,
                cell_indices=indices,
                scale_factor=PHI ** (max_depth - d),
            )
            self.rings.append(ring)

    def _establish_entanglement(self):
        self.entanglement_links = []
        positions = self.mandala.pos

        for d in range(1, len(self.rings)):
            outer = self.rings[d]
            inner = self.rings[d - 1]

            for oi in outer.cell_indices:
                best_inner, best_dist = None, float("inf")
                for ii in inner.cell_indices:
                    dist = np.linalg.norm(positions[oi] - positions[ii])
                    if dist < best_dist:
                        best_dist = dist
                        best_inner = ii

                if best_inner is not None:
                    strength = self.entanglement_decay ** 1  # one depth step
                    self.entanglement_links.append(EntanglementLink(
                        cell_a=oi, cell_b=best_inner,
                        depth_a=d, depth_b=d - 1,
                        strength=strength,
                        initial_strength=strength,
                    ))

    # ------------------------------------------------------------------
    # Holographic energy term
    # ------------------------------------------------------------------

    def holographic_energy(self) -> float:
        """
        Cross-ring consistency penalty.

        Dominant state of each inner ring should be consistent with
        its outer ring.  This is the holographic constraint: boundary
        information should project inward without contradiction.
        """
        if len(self.rings) < 2:
            return 0.0

        states = self.engine.state_indices
        energy = 0.0

        for d in range(len(self.rings) - 1):
            inner_idx = self.rings[d].cell_indices
            outer_idx = self.rings[d + 1].cell_indices
            if not inner_idx or not outer_idx:
                continue

            inner_states = [states[i] for i in inner_idx]
            outer_states = [states[i] for i in outer_idx]

            inner_mode = max(set(inner_states), key=inner_states.count)
            outer_mode = max(set(outer_states), key=outer_states.count)

            energy += 0.5 * (inner_mode != outer_mode)

        return energy

    def entanglement_energy(self) -> float:
        """
        Cross-depth entanglement with adaptive Berry phase.

        Phase determines correlation mode: same-state or complementary.
        """
        states = self.engine.state_indices
        energy = 0.0

        for link in self.entanglement_links:
            diff = abs(int(states[link.cell_a]) - int(states[link.cell_b]))
            phase_mode = math.cos(link.phase)

            if phase_mode >= 0:
                energy += link.strength * math.sin(diff * math.pi / 4) ** 2
            else:
                comp_diff = abs(diff - 4)
                energy += link.strength * math.sin(comp_diff * math.pi / 4) ** 2

            link.phase += diff * math.pi / 32
            correlated = (diff == 0) if phase_mode >= 0 else (abs(diff - 4) <= 1)
            link.correlation_history.append(correlated)
            if len(link.correlation_history) > 50:
                link.correlation_history.pop(0)

        return energy

    def total_energy(self, j_ij) -> float:
        """Base dual-pathway energy + holographic + entanglement."""
        E_base = self.engine.energy_landscape(j_ij)
        E_holo = self.holographic_energy()
        E_ent  = self.entanglement_energy()
        return E_base + self.holographic_weight * E_holo + E_ent

    # ------------------------------------------------------------------
    # Adaptive entanglement
    # ------------------------------------------------------------------

    def adapt_entanglement(self):
        """Strengthen useful links, weaken noisy ones."""
        for link in self.entanglement_links:
            if len(link.correlation_history) < 10:
                continue
            recent = link.correlation_history[-20:]
            rate = sum(recent) / len(recent)
            if rate > 0.6:
                link.strength = min(link.strength * 1.05, 0.95)
            elif rate < 0.3:
                link.strength = max(link.strength * 0.9, 0.01)

    # ------------------------------------------------------------------
    # Renormalization anneal: coarse-to-fine with bidirectional sweeps
    # ------------------------------------------------------------------

    def renormalization_anneal(self, j_ij,
                               n_sweeps: int = 3,
                               steps_per_ring: int = 200,
                               T_start: float = 5.0,
                               T_end: float = 0.1) -> Dict:
        """
        Multi-scale annealing:
        1. Solve coarsest scale (innermost ring) first
        2. Propagate outward as seed for next scale
        3. Refine at each scale with annealing
        4. Sweep bidirectionally for consistency

        Returns dict with ground_state, final_energy, energy_history.
        """
        if not self.rings:
            self.build()

        history = []

        for sweep in range(n_sweeps):
            outward = (sweep % 2 == 0)
            ring_order = range(len(self.rings)) if outward else range(len(self.rings) - 1, -1, -1)

            if sweep > 0:
                self.adapt_entanglement()

            for d in ring_order:
                ring = self.rings[d]
                active = set(ring.cell_indices)

                # Seed from adjacent solved ring
                if outward and d > 0 and (d - 1) in self.scale_solutions:
                    self._propagate(d - 1, d)

                # Freeze non-active cells
                frozen = {i: int(self.engine.state_indices[i])
                          for i in range(self.engine.num_cells) if i not in active}

                active_list = list(active)
                ratio = (T_end / T_start) ** (1.0 / max(steps_per_ring - 1, 1))
                T = T_start

                for step in range(steps_per_ring):
                    ci = active_list[np.random.randint(len(active_list))]
                    old_idx = self.engine.state_indices[ci]
                    old_ang = self.engine.orientations[ci]
                    old_E = self.total_energy(j_ij)

                    new_state = np.random.randint(0, 8)
                    self.engine.state_indices[ci] = new_state
                    self.engine.orientations[ci] = self.engine.ANGLES[new_state]

                    # Correlated entanglement update
                    correlated_changes = []
                    for link in self.entanglement_links:
                        partner = None
                        if link.cell_a == ci:
                            partner = link.cell_b
                        elif link.cell_b == ci:
                            partner = link.cell_a
                        if partner is not None and partner not in frozen:
                            if np.random.random() < link.strength:
                                correlated_changes.append(
                                    (partner, int(self.engine.state_indices[partner]),
                                     float(self.engine.orientations[partner])))
                                self.engine.state_indices[partner] = new_state
                                self.engine.orientations[partner] = self.engine.ANGLES[new_state]

                    new_E = self.total_energy(j_ij)
                    dE = new_E - old_E
                    accept = dE <= 0 or np.random.random() < math.exp(-dE / max(T, 1e-12))

                    if not accept:
                        self.engine.state_indices[ci] = old_idx
                        self.engine.orientations[ci] = old_ang
                        for pi, ps, pa in correlated_changes:
                            self.engine.state_indices[pi] = ps
                            self.engine.orientations[pi] = pa

                    # Restore frozen
                    for fi, fs in frozen.items():
                        self.engine.state_indices[fi] = fs
                        self.engine.orientations[fi] = self.engine.ANGLES[fs]

                    T *= ratio

                E = self.total_energy(j_ij)
                history.append(E)
                self.scale_solutions[d] = [int(self.engine.state_indices[i])
                                           for i in ring.cell_indices]

        final_E = self.total_energy(j_ij)
        return {
            "ground_state": self.engine.state_indices.tolist(),
            "final_energy": final_E,
            "energy_history": history,
            "scale_solutions": dict(self.scale_solutions),
        }

    def _propagate(self, from_depth: int, to_depth: int):
        """Propagate solved ring states via entanglement links."""
        if from_depth not in self.scale_solutions:
            return
        source_states = self.scale_solutions[from_depth]
        if not source_states:
            return
        dominant = max(set(source_states), key=source_states.count)

        seeded = set()
        for link in self.entanglement_links:
            if link.depth_a == to_depth and link.depth_b == from_depth:
                src_state = int(self.engine.state_indices[link.cell_b])
                self.engine.state_indices[link.cell_a] = src_state
                self.engine.orientations[link.cell_a] = self.engine.ANGLES[src_state]
                seeded.add(link.cell_a)
            elif link.depth_b == to_depth and link.depth_a == from_depth:
                src_state = int(self.engine.state_indices[link.cell_a])
                self.engine.state_indices[link.cell_b] = src_state
                self.engine.orientations[link.cell_b] = self.engine.ANGLES[src_state]
                seeded.add(link.cell_b)

        for idx in self.rings[to_depth].cell_indices:
            if idx not in seeded:
                self.engine.state_indices[idx] = dominant
                self.engine.orientations[idx] = self.engine.ANGLES[dominant]

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def profile(self) -> Dict:
        """State distribution at each ring depth."""
        states = self.engine.state_indices
        result = {}
        for ring in self.rings:
            ring_states = [int(states[i]) for i in ring.cell_indices]
            dist = {s: ring_states.count(s) for s in range(8)}
            dominant = max(dist, key=dist.get) if dist else None
            result[ring.depth] = {
                "radius": ring.radius,
                "cells": len(ring.cell_indices),
                "scale": ring.scale_factor,
                "dominant": dominant,
                "distribution": dist,
            }
        return result

    def entanglement_stats(self) -> Dict:
        """Summary statistics for entanglement links."""
        if not self.entanglement_links:
            return {"count": 0}
        states = self.engine.state_indices
        correlated = sum(1 for l in self.entanglement_links
                         if states[l.cell_a] == states[l.cell_b])
        strengths = [l.strength for l in self.entanglement_links]
        return {
            "count": len(self.entanglement_links),
            "correlated": correlated,
            "avg_strength": sum(strengths) / len(strengths),
            "min_strength": min(strengths),
            "max_strength": max(strengths),
        }
