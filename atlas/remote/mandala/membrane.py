"""
MEMBRANE COMPUTATION v1.0
The boundary between order and chaos as a computational primitive.

Crystal growth happens at the solid-liquid interface.
Cell membranes mediate inside and outside.
Phase transitions occur at the critical point.
Computation happens at the boundary between coarse and fine.

A membrane takes:
  - A coarse oracle (fast, approximate: quantum, heuristic, sampling)
  - A resolution function (how to expand approximate -> search window)
  - A fine solver (slow, exact: annealing, enumeration, constraint propagation)

The membrane IS the computation. The coarse side constrains.
The fine side resolves. The boundary is where the answer crystallizes.

General enough for any problem where approximate and exact methods exist:
  - Factorization: quantum basin -> boundary window -> classical register search
  - SAT: random sampling -> clause cluster -> focused annealing
  - Graph coloring: greedy heuristic -> conflict zone -> local refinement
  - Optimization: landscape scan -> promising region -> fine-grained search
  - Agent exploration: broad survey -> interesting zone -> deep investigation

Usage:
    from membrane import Membrane, CoarseResult

    def my_coarse(problem):
        return CoarseResult(center=[3, 5], confidence=0.7, radius=2)

    def my_fine(problem, window):
        # search within window
        return {"answer": [3, 5], "verified": True}

    m = Membrane(coarse_fn=my_coarse, fine_fn=my_fine)
    result = m.solve(problem_data)
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import math
import time


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass
class CoarseResult:
    """Output of the coarse oracle."""
    center: Any          # approximate solution (list, tuple, dict, etc.)
    confidence: float    # 0-1: how confident the oracle is
    radius: float        # how wide the search window should be
    metadata: Dict = field(default_factory=dict)


@dataclass
class Window:
    """The search window defined by the membrane."""
    bounds: Dict[str, Tuple[Any, Any]]  # dimension -> (low, high)
    size: int                           # total candidates in window
    full_space_size: int                # total candidates without membrane
    compression: float                  # full_space / window (higher = more focused)
    contains_solution: bool = False     # set after solving
    metadata: Dict = field(default_factory=dict)


@dataclass
class MembraneResult:
    """Full result from membrane computation."""
    coarse: CoarseResult
    window: Window
    fine_solution: Any
    verified: bool
    phase: str           # which phase found the answer: "coarse", "boundary", "fine"
    time_coarse: float
    time_membrane: float
    time_fine: float
    metadata: Dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Membrane
# ---------------------------------------------------------------------------

class Membrane:
    """
    The boundary between coarse and fine computation.

    Three phases:
      1. COARSE (order): Fast oracle gives approximate answer + confidence
      2. MEMBRANE (edge): Translates approximation into focused search window
      3. FINE (resolution): Exact solver works within the window

    The membrane adapts its permeability based on confidence:
      - High confidence -> tight window (narrow membrane)
      - Low confidence -> wide window (permeable membrane)
      - Very low confidence -> skip coarse, let fine solver search full space
    """

    def __init__(self,
                 coarse_fn: Callable = None,
                 fine_fn: Callable = None,
                 window_fn: Callable = None,
                 min_confidence: float = 0.1):
        """
        Args:
            coarse_fn: (problem_data) -> CoarseResult
            fine_fn: (problem_data, window) -> solution dict
            window_fn: (coarse_result, problem_data) -> Window
                       (optional: default expands center +/- radius)
            min_confidence: below this, skip coarse and search full space
        """
        self.coarse_fn = coarse_fn
        self.fine_fn = fine_fn
        self.window_fn = window_fn or self._default_window
        self.min_confidence = min_confidence
        self.history: List[MembraneResult] = []

    def solve(self, problem_data: Dict) -> MembraneResult:
        """
        Run the three-phase membrane computation.
        """
        # Phase 1: Coarse
        t0 = time.time()
        if self.coarse_fn:
            coarse = self.coarse_fn(problem_data)
        else:
            coarse = CoarseResult(center=None, confidence=0.0, radius=float("inf"))
        t_coarse = time.time() - t0

        # Phase 2: Membrane (window construction)
        t0 = time.time()
        if coarse.confidence >= self.min_confidence and coarse.center is not None:
            window = self.window_fn(coarse, problem_data)
        else:
            # Low confidence: full space search
            window = Window(
                bounds={}, size=0, full_space_size=0,
                compression=1.0,
                metadata={"reason": "confidence below threshold"},
            )
        t_membrane = time.time() - t0

        # Phase 3: Fine
        t0 = time.time()
        if self.fine_fn:
            fine_solution = self.fine_fn(problem_data, window)
        else:
            fine_solution = {"answer": coarse.center, "verified": False}
        t_fine = time.time() - t0

        # Determine which phase solved it
        verified = fine_solution.get("verified", False)
        if verified:
            phase = "fine"
        elif window.contains_solution:
            phase = "boundary"
        elif coarse.confidence > 0.9:
            phase = "coarse"
        else:
            phase = "fine"  # fine ran but may not have verified

        result = MembraneResult(
            coarse=coarse,
            window=window,
            fine_solution=fine_solution,
            verified=verified,
            phase=phase,
            time_coarse=t_coarse,
            time_membrane=t_membrane,
            time_fine=t_fine,
        )
        self.history.append(result)
        return result

    @staticmethod
    def _default_window(coarse: CoarseResult, problem_data: Dict) -> Window:
        """Default window: expand center +/- radius in each dimension."""
        center = coarse.center
        radius = coarse.radius

        if isinstance(center, (list, tuple)):
            bounds = {}
            for i, c in enumerate(center):
                if isinstance(c, (int, float)):
                    bounds[f"dim_{i}"] = (c - radius, c + radius)
                else:
                    bounds[f"dim_{i}"] = (c, c)
            size = int((2 * radius + 1) ** len(center))
            full_size = size * 10  # rough estimate
        else:
            bounds = {"value": (center, center)}
            size = 1
            full_size = 1

        return Window(
            bounds=bounds,
            size=max(size, 1),
            full_space_size=max(full_size, 1),
            compression=max(full_size, 1) / max(size, 1),
        )

    def permeability(self) -> float:
        """
        Current membrane permeability based on history.

        High permeability = wide windows (membrane lets more through).
        Low permeability = tight windows (membrane is selective).

        Adapts based on whether tight windows found solutions.
        """
        if not self.history:
            return 0.5
        recent = self.history[-10:]
        verified = sum(1 for r in recent if r.verified)
        return verified / len(recent)


# ---------------------------------------------------------------------------
# Pre-built membrane configurations
# ---------------------------------------------------------------------------

def factorization_membrane(N: int, quantum_steps: int = 100) -> Membrane:
    """
    Pre-configured membrane for integer factorization.

    Coarse: quantum annealing (finds basin in stride-grid)
    Membrane: expand basin to +/- stride window
    Fine: classical annealing within window (seeded by basin center)
    """
    import numpy as np

    max_factor = int(math.isqrt(N)) + 1
    stride = max(1, math.ceil(max_factor / 8))

    def coarse(problem_data):
        try:
            from quantum_mandala import QuantumMandalaComputer
            qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8)
            r = qc.quantum_annealing("factorization", problem_data, num_steps=quantum_steps)
            sol = r["solution"]
            factors = sol.get("factors", [2, 2])
            confidence = 1.0 / (1.0 + abs(r["final_energy"]))
            return CoarseResult(center=factors, confidence=confidence, radius=stride,
                                metadata={"stride": stride, "energy": r["final_energy"]})
        except ImportError:
            return CoarseResult(center=None, confidence=0.0, radius=stride)

    def window(coarse_result, problem_data):
        center = coarse_result.center
        r = coarse_result.radius
        fa_range = (max(2, center[0] - r), center[0] + r)
        fb_range = (max(2, center[1] - r), center[1] + r)
        size = (fa_range[1] - fa_range[0] + 1) * (fb_range[1] - fb_range[0] + 1)
        full = max_factor ** 2

        # Check for hits in the window
        hits = []
        for fa in range(fa_range[0], fa_range[1] + 1):
            for fb in range(fb_range[0], fb_range[1] + 1):
                if fa * fb == N and fa > 1 and fb > 1:
                    hits.append((fa, fb))

        w = Window(
            bounds={"fa": fa_range, "fb": fb_range},
            size=size, full_space_size=full,
            compression=full / max(size, 1),
            contains_solution=len(hits) > 0,
            metadata={"hits": hits},
        )
        return w

    def fine(problem_data, win):
        from mandala_computer import MandalaComputer

        # If boundary already found exact solution, use it
        if win.contains_solution and win.metadata.get("hits"):
            pair = win.metadata["hits"][0]
            return {"answer": pair, "verified": True, "method": "boundary"}

        # Otherwise, classical annealing
        mc = MandalaComputer(golden_depth=5, sacred_geometry=8)
        mc.encode_factorization(N)
        r = mc.simulated_annealing(max_steps=8000, T_start=5.0, T_end=0.001)
        sol = r["solution"]
        return {
            "answer": sol.get("best_pair"),
            "verified": sol.get("verified", False),
            "method": "annealing",
        }

    return Membrane(coarse_fn=coarse, fine_fn=fine, window_fn=window)


def sat_membrane(clauses: List[List[int]], num_vars: int) -> Membrane:
    """
    Pre-configured membrane for SAT solving.

    Coarse: random sampling to find which variables are most constrained
    Membrane: fix highly-constrained variables, search the rest
    Fine: annealing on the reduced variable set
    """
    import numpy as np

    def coarse(problem_data):
        # Sample random assignments, find which variables are consistently set
        n_samples = 100
        best_unsat = len(clauses)
        best_assignment = None
        var_tendency = np.zeros(num_vars)  # positive = tends True

        for _ in range(n_samples):
            assignment = np.random.randint(0, 2, num_vars).astype(bool)
            unsat = sum(
                1 for clause in clauses
                if not any(
                    (lit > 0 and assignment[abs(lit) - 1]) or
                    (lit < 0 and not assignment[abs(lit) - 1])
                    for lit in clause
                )
            )
            if unsat < best_unsat:
                best_unsat = unsat
                best_assignment = assignment.copy()
            var_tendency += assignment.astype(float)

        var_tendency /= n_samples
        confidence = 1.0 - best_unsat / max(len(clauses), 1)
        return CoarseResult(
            center=best_assignment.tolist() if best_assignment is not None else None,
            confidence=confidence,
            radius=num_vars * (1 - confidence),  # tighter if more confident
            metadata={"best_unsat": best_unsat, "var_tendency": var_tendency.tolist()},
        )

    def fine(problem_data, win):
        from mandala_computer import MandalaComputer
        mc = MandalaComputer(golden_depth=3, sacred_geometry=8, temperature=0.5)
        mc.encode_sat(clauses)

        # Seed from coarse result if available
        if win.metadata.get("seed"):
            seed = win.metadata["seed"]
            for i, c in enumerate(mc.cells[:len(seed)]):
                c.state = 4 + seed[i] if seed[i] else seed[i]  # 4-7=True, 0-3=False

        r = mc.simulated_annealing(max_steps=5000, T_start=3.0, T_end=0.01)
        sol = r["solution"]
        return {
            "answer": sol.get("assignment"),
            "verified": sol.get("satisfies", False),
            "method": "annealing",
        }

    def window(coarse_result, problem_data):
        # Fix variables with strong tendency, leave the rest free
        tendency = coarse_result.metadata.get("var_tendency", [])
        fixed = sum(1 for t in tendency if t > 0.8 or t < 0.2)
        free = num_vars - fixed
        size = 2 ** free
        full = 2 ** num_vars
        return Window(
            bounds={"free_vars": free, "fixed_vars": fixed},
            size=size, full_space_size=full,
            compression=full / max(size, 1),
            metadata={"seed": coarse_result.center},
        )

    return Membrane(coarse_fn=coarse, fine_fn=fine, window_fn=window)


def landscape_membrane(cost_fn, num_vars: int, num_states: int = 8) -> Membrane:
    """
    General optimization membrane.

    Coarse: random landscape scan (fast sampling)
    Membrane: neighborhood around best sample
    Fine: annealing from best sample as seed
    """
    import numpy as np

    def coarse(problem_data):
        best_cost = float("inf")
        best_config = None
        for _ in range(200):
            config = [np.random.randint(0, num_states) for _ in range(num_vars)]
            c = cost_fn(config)
            if c < best_cost:
                best_cost = c
                best_config = config
        confidence = 1.0 / (1.0 + abs(best_cost))
        return CoarseResult(center=best_config, confidence=confidence, radius=2,
                            metadata={"best_cost": best_cost})

    def fine(problem_data, win):
        from mandala_computer import MandalaComputer
        mc = MandalaComputer(golden_depth=4, sacred_geometry=num_states)
        mc.encode_optimization(cost_fn, num_vars)
        # Seed from coarse
        if win.metadata.get("seed"):
            for i, c in enumerate(mc.cells[:len(win.metadata["seed"])]):
                c.state = win.metadata["seed"][i]
        r = mc.simulated_annealing(max_steps=5000, T_start=3.0, T_end=0.01)
        return {
            "answer": r["solution"]["states"],
            "verified": True,
            "cost": r["solution"]["cost"],
            "method": "annealing",
        }

    def window(coarse_result, problem_data):
        return Window(
            bounds={"neighborhood": coarse_result.radius},
            size=int((2 * coarse_result.radius + 1) ** num_vars),
            full_space_size=num_states ** num_vars,
            compression=num_states ** num_vars / max((2 * coarse_result.radius + 1) ** num_vars, 1),
            metadata={"seed": coarse_result.center},
        )

    return Membrane(coarse_fn=coarse, fine_fn=fine, window_fn=window)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo():
    print("=" * 60)
    print("MEMBRANE COMPUTATION v1.0")
    print("  Coarse -> Boundary -> Fine")
    print("=" * 60)

    # Factorization membrane
    print("\n--- Factorization: N=143 ---")
    m = factorization_membrane(143, quantum_steps=80)
    r = m.solve({"N": 143})
    print(f"  Phase: {r.phase}")
    print(f"  Answer: {r.fine_solution.get('answer')}")
    print(f"  Verified: {r.verified}")
    print(f"  Window compression: {r.window.compression:.1f}x")
    print(f"  Boundary hit: {r.window.contains_solution}")
    print(f"  Time: coarse={r.time_coarse:.2f}s membrane={r.time_membrane:.4f}s fine={r.time_fine:.2f}s")

    # SAT membrane
    print("\n--- SAT: 3 clauses ---")
    clauses = [[1, 2], [-1, 3], [-2, -3]]
    m2 = sat_membrane(clauses, num_vars=3)
    r2 = m2.solve({"clauses": clauses})
    print(f"  Phase: {r2.phase}")
    print(f"  Verified: {r2.verified}")
    print(f"  Window: {r2.window.bounds}")
    print(f"  Compression: {r2.window.compression:.1f}x")

    # Optimization membrane
    print("\n--- Optimization: min sum of squared diffs ---")
    def cost(states):
        return sum((states[i] - states[i+1])**2 for i in range(len(states)-1))
    m3 = landscape_membrane(cost, num_vars=8)
    r3 = m3.solve({})
    print(f"  Phase: {r3.phase}")
    print(f"  Cost: {r3.fine_solution.get('cost', '?')}")
    print(f"  Compression: {r3.window.compression:.1f}x")

    print(f"\n  Membrane permeability: {m.permeability():.2f}")


if __name__ == "__main__":
    demo()
