"""
MANDALA COMPUTING SIMULATOR v2.0
Geometric Intelligence Through Natural Symmetry

Demonstrates computation via physical relaxation to ground state
using octahedral symmetry and golden ratio optimization.

Core Principle: The physics does the computation.

v2.0: JSON layer wiring, exploration algorithms, full encodings, sensor telemetry
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import pathlib
import copy
import math

# Optional: glyph-native arithmetic. If unavailable, factorization solutions
# omit glyph representations but all computation still works.
try:
    from octahedral_arithmetic import OctahedralNumber, states_to_number, factor_pair_glyphs
    HAS_GLYPH_MATH = True
except ImportError:
    HAS_GLYPH_MATH = False

# ---------------------------------------------------------------------------
# JSON Layer: load constants and glyphs from atlas/shapes.json and glyphs/
# ---------------------------------------------------------------------------

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent

_STATE_GLYPHS = ["\u2295", "\u2296", "\u2297", "\u2298", "\u2299", "\u229a", "\u229b", "\u229c"]

_ATLAS = None
_GLYPH_DATA = None

try:
    with open(_SCRIPT_DIR / "atlas" / "shapes.json") as _f:
        _ATLAS = json.load(_f)
except (FileNotFoundError, json.JSONDecodeError):
    pass

try:
    with open(_SCRIPT_DIR / "glyphs" / "mandala.json") as _f:
        _GLYPH_DATA = json.load(_f)
        _loaded = [g["unicode"] for g in _GLYPH_DATA.get("octahedral_state_glyphs", [])]
        if _loaded:
            _STATE_GLYPHS = _loaded
except (FileNotFoundError, json.JSONDecodeError, KeyError):
    pass


def _atlas_constant(name, default):
    """Read a constant from loaded atlas, falling back to default."""
    if _ATLAS and "constants" in _ATLAS:
        return _ATLAS["constants"].get(name, default)
    return default


# Golden ratio
PHI = _atlas_constant("PHI", (1 + math.sqrt(5)) / 2)

# Coupling parameters from atlas
FRET_CUTOFF = _atlas_constant("FRET_CUTOFF", 3.0 * PHI)
OCTAHEDRAL_STATES = int(_atlas_constant("OCTAHEDRAL_STATES", 8))
COUPLING_EXPONENT = int(_atlas_constant("COUPLING_EXPONENT", 6))

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class MandalaCell:
    """Computational cell with octahedral states."""
    state: int  # 0-7
    position: Tuple[float, float]
    depth: int
    neighbors: List[int]
    energy: float = 0.0


@dataclass
class SensorReading:
    """Single sensor telemetry reading."""
    sensor_id: str
    step: int
    value: object  # float, dict, or list
    metadata: Dict = field(default_factory=dict)


class ProblemType(Enum):
    """Types of problems encodable as geometric ground states."""
    FACTORIZATION = "factorization"
    SAT = "satisfiability"
    TSP = "traveling_salesman"
    GRAPH_COLORING = "graph_coloring"
    OPTIMIZATION = "optimization"


# ---------------------------------------------------------------------------
# MandalaComputer
# ---------------------------------------------------------------------------

class MandalaComputer:
    """
    Core Mandala Computing engine.

    Encodes problems as geometric configurations,
    lets physics find ground state,
    reads solution from minimum energy configuration.
    """

    def __init__(self,
                 golden_depth: int = 5,
                 sacred_geometry: int = OCTAHEDRAL_STATES,
                 dimensional_fold: int = 3,
                 temperature: float = 1.0):
        self.golden_depth = golden_depth
        self.sacred_geometry = sacred_geometry
        self.dimensions = dimensional_fold
        self.temperature = temperature

        # Mandala structure
        self.cells: List[MandalaCell] = []
        self.num_cells = 0

        # Energy landscape
        self.coupling_strength = 1.0
        self.fibonacci_eigenvalues = self._generate_fibonacci_eigenvalues()

        # Problem encoding
        self.problem_type: Optional[ProblemType] = None
        self.problem_data: Optional[Dict] = None

        # Solution
        self.ground_state: Optional[List[int]] = None
        self.solution: Optional[Dict] = None

        # Telemetry / introspection
        self.telemetry: List[SensorReading] = []
        self.energy_history: List[float] = []

        # Atlas / glyph config
        self._atlas = _ATLAS
        self._glyphs = _STATE_GLYPHS

        print(f"Mandala Computer initialized")
        print(f"   Depth: {golden_depth}  Symmetry: {sacred_geometry}-fold")
        print(f"   Temperature: {temperature}")
        if self._atlas:
            print(f"   Atlas loaded (shapes.json)")

    # ------------------------------------------------------------------
    # Fibonacci eigenvalues
    # ------------------------------------------------------------------

    def _generate_fibonacci_eigenvalues(self) -> np.ndarray:
        ev = np.array([PHI ** i for i in range(self.golden_depth)])
        return ev / np.sum(ev)

    # ------------------------------------------------------------------
    # Bloom engine
    # ------------------------------------------------------------------

    def bloom_mandala(self):
        """Expand symbol core into nested computational rings."""
        self.cells = []
        for depth in range(self.golden_depth):
            num_cells_at_depth = int(PHI ** (depth + 1))
            radius = PHI ** depth
            for i in range(num_cells_at_depth):
                angle = 2 * np.pi * i / num_cells_at_depth
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                cell = MandalaCell(
                    state=np.random.randint(0, self.sacred_geometry),
                    position=(x, y),
                    depth=depth,
                    neighbors=[],
                    energy=0.0,
                )
                self.cells.append(cell)
        self.num_cells = len(self.cells)
        self._establish_coupling()
        print(f"   Bloomed {self.num_cells} cells, {self._count_couplings()} couplings")

    def _establish_coupling(self):
        """FRET-like dipole coupling between nearby cells (1/r^6)."""
        for i, ci in enumerate(self.cells):
            for j, cj in enumerate(self.cells):
                if i >= j:
                    continue
                dx = ci.position[0] - cj.position[0]
                dy = ci.position[1] - cj.position[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if 0 < dist < FRET_CUTOFF:
                    ci.neighbors.append(j)
                    cj.neighbors.append(i)
        self._build_simd_arrays()

    def _build_simd_arrays(self):
        """
        Build numpy arrays for vectorized energy computation.

        Converts cell states, positions, and neighbor lists into
        dense arrays that numpy can process via SIMD.
        """
        n = self.num_cells
        # State vector (updated on every flip)
        self._states = np.array([c.state for c in self.cells], dtype=np.int32)
        # Cell energies
        self._cell_energies = np.array([c.energy for c in self.cells], dtype=np.float64)
        # Neighbor pairs as (i, j) array for vectorized coupling
        pairs = []
        for i, ci in enumerate(self.cells):
            for j in ci.neighbors:
                if j > i:
                    pairs.append((i, j))
        if pairs:
            self._neighbor_pairs = np.array(pairs, dtype=np.int32)
        else:
            self._neighbor_pairs = np.empty((0, 2), dtype=np.int32)

    def _sync_states_to_array(self):
        """Sync cell objects -> numpy array."""
        for i, c in enumerate(self.cells):
            self._states[i] = c.state

    def _sync_states_from_array(self):
        """Sync numpy array -> cell objects."""
        for i, c in enumerate(self.cells):
            c.state = int(self._states[i])

    def _count_couplings(self) -> int:
        return sum(len(c.neighbors) for c in self.cells) // 2

    # ------------------------------------------------------------------
    # Sensor telemetry
    # ------------------------------------------------------------------

    def _emit_sensor(self, sensor_id: str, step: int, value, metadata: dict = None):
        self.telemetry.append(SensorReading(
            sensor_id=sensor_id,
            step=step,
            value=value,
            metadata=metadata or {},
        ))

    # ------------------------------------------------------------------
    # Problem encodings
    # ------------------------------------------------------------------

    @staticmethod
    def _factor_register_size(N: int, base: int = 8) -> int:
        """
        How many cells (digits in base-8) needed to represent sqrt(N).

        1 cell: factors 2..9      (N up to 81)
        2 cells: factors 2..65    (N up to 4225)
        3 cells: factors 2..513   (N up to ~263k)
        """
        max_factor = int(math.isqrt(N)) + 1
        digits = 1
        # Factor range is [2, 2 + base^digits - 1] = [2, base^digits + 1]
        # so base^digits + 1 must be >= max_factor
        while (base ** digits) + 1 < max_factor:
            digits += 1
        return digits

    def _cells_to_factor(self, cell_indices: List[int]) -> int:
        """
        Decode a multi-cell factor register.

        Factor = 2 + sum(cell[i].state * base^i) for positional encoding.
        Minimum factor is always 2 (offset).
        """
        base = self.sacred_geometry
        value = 0
        for i, idx in enumerate(cell_indices):
            value += self.cells[idx].state * (base ** i)
        return 2 + value

    def encode_factorization(self, N: int):
        """
        Encode factorization with multi-cell factor registers.

        Each factor is represented by `digits_per_factor` cells in base-8
        positional encoding. Factor = 2 + sum(state_i * 8^i).

        1 digit:  factors [2..9]     — N up to 81
        2 digits: factors [2..65]    — N up to 4225
        3 digits: factors [2..513]   — N up to ~263k

        Cells are grouped: [fa_digit0, fa_digit1, ..., fb_digit0, fb_digit1, ...]
        """
        digits = self._factor_register_size(N, self.sacred_geometry)
        cells_per_pair = 2 * digits  # two factors, each `digits` cells wide
        max_factor = (self.sacred_geometry ** digits) + 1

        print(f"\n   Encoding factorization of N={N}")
        print(f"   Factor register: {digits} cells/factor (base-{self.sacred_geometry}), range [2..{max_factor}]")

        self.problem_type = ProblemType.FACTORIZATION
        self.problem_data = {
            "N": N,
            "digits_per_factor": digits,
            "cells_per_pair": cells_per_pair,
            "max_factor": max_factor,
        }
        self.bloom_mandala()
        for cell in self.cells:
            cell.energy = 0.0

    def encode_sat(self, clauses: List[List[int]]):
        """Encode SAT problem. States 0-3 = False, 4-7 = True."""
        print(f"\n   Encoding SAT with {len(clauses)} clauses")
        self.problem_type = ProblemType.SAT
        self.problem_data = {"clauses": clauses}
        variables = set()
        for clause in clauses:
            variables.update(abs(lit) for lit in clause)
        self.problem_data["num_vars"] = len(variables)
        self.bloom_mandala()

    def encode_tsp(self, cities: np.ndarray):
        """
        Encode TSP as ring topology with winding energy.

        Each cell represents a position in the tour. Cell state = which city
        to visit at that position. Energy penalizes:
          - Long edges (distance between consecutive cities in tour)
          - Repeated cities (same state in multiple cells)
        """
        print(f"\n   Encoding TSP with {len(cities)} cities")
        self.problem_type = ProblemType.TSP
        self.problem_data = {"cities": cities, "num_cities": len(cities)}
        self.bloom_mandala()

    def encode_graph_coloring(self, adjacency: List[List[int]], num_colors: int):
        """
        Encode graph coloring problem.

        Nodes map to cells. Colors are octahedral states mod num_colors.
        Adjacent nodes sharing a color incur energy penalty.
        """
        if not adjacency:
            raise ValueError("Adjacency list cannot be empty")
        num_nodes = max(max(e) for e in adjacency) + 1
        print(f"\n   Encoding graph coloring: {num_nodes} nodes, {num_colors} colors, {len(adjacency)} edges")
        self.problem_type = ProblemType.GRAPH_COLORING
        self.problem_data = {
            "adjacency": adjacency,
            "num_colors": num_colors,
            "num_nodes": num_nodes,
        }
        self.bloom_mandala()
        # Wire adjacency into cell neighbor lists
        for n_i, n_j in adjacency:
            if n_i < self.num_cells and n_j < self.num_cells:
                if n_j not in self.cells[n_i].neighbors:
                    self.cells[n_i].neighbors.append(n_j)
                if n_i not in self.cells[n_j].neighbors:
                    self.cells[n_j].neighbors.append(n_i)

    def encode_optimization(self, cost_fn: Callable[[List[int]], float], num_variables: int):
        """
        Encode generic optimization problem.

        cost_fn takes a list of cell states (0-7) and returns a cost to minimize.
        """
        print(f"\n   Encoding optimization with {num_variables} variables")
        self.problem_type = ProblemType.OPTIMIZATION
        self.problem_data = {"cost_fn": cost_fn, "num_variables": num_variables}
        self.bloom_mandala()

    # ------------------------------------------------------------------
    # Energy computation
    # ------------------------------------------------------------------

    def compute_total_energy(self) -> float:
        """
        E_total = sum(E_cell) + sum(E_coupling) + problem-specific terms.

        Uses numpy SIMD for coupling and factorization energy.
        Coupling computation is fully vectorized — no Python loops over pairs.
        """
        # Optimization: delegate entirely to cost function
        if self.problem_type == ProblemType.OPTIMIZATION and self.problem_data:
            cost_fn = self.problem_data.get("cost_fn")
            if cost_fn:
                return cost_fn([c.state for c in self.cells])

        # Sync state array
        self._sync_states_to_array()
        states = self._states

        total = float(np.sum(self._cell_energies))

        # --- Vectorized coupling energy (SIMD) ---
        if len(self._neighbor_pairs) > 0:
            coupling_scale = 0.1 if self.problem_type == ProblemType.FACTORIZATION else 1.0
            si = states[self._neighbor_pairs[:, 0]]
            sj = states[self._neighbor_pairs[:, 1]]
            diffs = np.abs(si - sj).astype(np.float64)
            coupling_e = coupling_scale * self.coupling_strength * np.sin(diffs * math.pi / 4) ** 2
            total += float(np.sum(coupling_e))

        # --- Vectorized factorization energy ---
        if self.problem_type == ProblemType.FACTORIZATION and self.problem_data:
            N = self.problem_data["N"]
            dpf = self.problem_data["digits_per_factor"]
            cpp = self.problem_data["cells_per_pair"]
            base_powers = np.array([self.sacred_geometry ** d for d in range(dpf)], dtype=np.int64)
            for pair_start in range(0, self.num_cells - cpp + 1, cpp):
                fa = 2 + int(np.sum(states[pair_start:pair_start + dpf] * base_powers))
                fb = 2 + int(np.sum(states[pair_start + dpf:pair_start + cpp] * base_powers))
                total += (fa * fb - N) ** 2

        # SAT energy
        if self.problem_type == ProblemType.SAT and self.problem_data:
            bool_vals = states >= 4  # vectorized: True if state 4-7
            for clause in self.problem_data["clauses"]:
                satisfied = False
                for literal in clause:
                    vi = abs(literal) - 1
                    if vi < self.num_cells:
                        if (literal > 0 and bool_vals[vi]) or (literal < 0 and not bool_vals[vi]):
                            satisfied = True
                            break
                if not satisfied:
                    total += 2.0

        # Graph coloring energy (vectorized via adjacency array)
        if self.problem_type == ProblemType.GRAPH_COLORING and self.problem_data:
            nc = self.problem_data["num_colors"]
            adj = np.array(self.problem_data["adjacency"], dtype=np.int32)
            mask = (adj[:, 0] < self.num_cells) & (adj[:, 1] < self.num_cells)
            valid = adj[mask]
            if len(valid) > 0:
                ci = states[valid[:, 0]] % nc
                cj = states[valid[:, 1]] % nc
                same = (ci == cj)
                total += float(np.sum(same) * 2.0 - np.sum(~same) * PHI)

        # TSP energy (vectorized tour length)
        if self.problem_type == ProblemType.TSP and self.problem_data:
            cities = self.problem_data["cities"]
            nc = self.problem_data["num_cities"]
            tour = states % nc
            # Tour distances: vectorized
            tour_next = np.roll(tour, -1)
            city_a = cities[tour]
            city_b = cities[tour_next]
            total += float(np.sum(np.linalg.norm(city_a - city_b, axis=1)))
            # Repetition penalty
            counts = np.bincount(tour, minlength=nc)
            total += float(np.sum(np.maximum(counts - 1, 0) * 5.0))
            total += float(np.sum((counts == 0).astype(float) * 3.0))

        return total

    # ------------------------------------------------------------------
    # Relaxation (Metropolis-Hastings)
    # ------------------------------------------------------------------

    def relax_step(self) -> float:
        """
        Single Metropolis-Hastings step. Returns energy change.

        For problems without custom energy (factorization, SAT, graph coloring, TSP),
        computes full energy diff. The vectorized compute_total_energy makes this
        fast even for large cell counts.
        """
        cell_idx = np.random.randint(0, self.num_cells)
        cell = self.cells[cell_idx]
        E_old = self.compute_total_energy()
        old_state = cell.state
        cell.state = np.random.randint(0, self.sacred_geometry)
        E_new = self.compute_total_energy()
        dE = E_new - E_old
        if dE < 0:
            return dE
        exp_arg = -dE / max(self.temperature, 1e-15)
        p_accept = math.exp(min(exp_arg, 500))
        if np.random.random() < p_accept:
            return dE
        cell.state = old_state
        return 0.0

    def relax_to_ground_state(self, max_steps: int = 10000,
                              convergence_threshold: float = 1e-6) -> Dict:
        """Let physics find ground state through thermal relaxation."""
        print(f"\n   Relaxing to ground state (T={self.temperature}, max={max_steps})")
        start = time.time()
        self.energy_history = []
        log_interval = max(100, max_steps // 100)

        for step in range(max_steps):
            dE = self.relax_step()
            E = self.compute_total_energy()
            self.energy_history.append(E)

            if step % log_interval == 0:
                self._emit_sensor("energy.total", step, E)
                self._emit_sensor("energy.delta", step, dE)
                self._emit_sensor("temperature", step, self.temperature)
                self._emit_sensor("symmetry.octahedral", step, self.get_state_distribution())
                rate = self.get_convergence_rate(window=log_interval)
                self._emit_sensor("convergence.rate", step, rate)
                print(f"   Step {step:>6d}: E={E:.4f}  {self.glyph_trace(8)}")

            window = min(10 * log_interval, len(self.energy_history))
            if window >= 20:
                recent = self.energy_history[-window:]
                if np.var(recent) < convergence_threshold:
                    print(f"   Converged at step {step}")
                    break

        elapsed = time.time() - start
        final_energy = self.compute_total_energy()
        self.ground_state = [c.state for c in self.cells]
        self.solution = self._extract_solution()
        return {
            "ground_state": self.ground_state,
            "final_energy": final_energy,
            "steps": step,
            "time": elapsed,
            "solution": self.solution,
        }

    # ------------------------------------------------------------------
    # Exploration: simulated annealing
    # ------------------------------------------------------------------

    def simulated_annealing(self, max_steps: int = 10000,
                            T_start: float = 2.0, T_end: float = 0.01,
                            schedule: str = "exponential") -> Dict:
        """
        Simulated annealing with configurable cooling schedule.

        Schedules: 'exponential', 'linear', 'boltzmann'
        """
        print(f"\n   Simulated annealing ({schedule}): T {T_start} -> {T_end}, {max_steps} steps")
        start = time.time()
        self.energy_history = []
        temperatures = []
        log_interval = max(100, max_steps // 100)

        for step in range(max_steps):
            frac = step / max(max_steps - 1, 1)
            if schedule == "linear":
                self.temperature = T_start + (T_end - T_start) * frac
            elif schedule == "boltzmann":
                self.temperature = T_start / (1 + math.log(1 + step))
            else:  # exponential
                self.temperature = T_start * (T_end / max(T_start, 1e-15)) ** frac

            dE = self.relax_step()
            E = self.compute_total_energy()
            self.energy_history.append(E)
            temperatures.append(self.temperature)

            if step % log_interval == 0:
                self._emit_sensor("energy.total", step, E)
                self._emit_sensor("temperature", step, self.temperature)
                print(f"   Step {step:>6d}: E={E:.4f}  T={self.temperature:.4f}  {self.glyph_trace(8)}")

        elapsed = time.time() - start
        final_energy = self.compute_total_energy()
        self.ground_state = [c.state for c in self.cells]
        self.solution = self._extract_solution()
        print(f"   Final energy: {final_energy:.4f} ({elapsed:.2f}s)")
        return {
            "ground_state": self.ground_state,
            "final_energy": final_energy,
            "steps": max_steps,
            "time": elapsed,
            "solution": self.solution,
            "schedule": schedule,
            "temperatures": temperatures,
        }

    # ------------------------------------------------------------------
    # Exploration: parallel tempering
    # ------------------------------------------------------------------

    def parallel_tempering(self, num_replicas: int = 4,
                           T_min: float = 0.1, T_max: float = 5.0,
                           steps_per_swap: int = 100,
                           max_steps: int = 10000) -> Dict:
        """Multiple replicas at geometrically spaced temperatures with swap moves."""
        print(f"\n   Parallel tempering: {num_replicas} replicas, T=[{T_min}..{T_max}]")
        start = time.time()

        # Geometric temperature ladder
        temps = [T_min * (T_max / T_min) ** (i / max(num_replicas - 1, 1))
                 for i in range(num_replicas)]

        # Save original cells, create replica states
        original_states = [c.state for c in self.cells]
        replicas = []
        for _ in range(num_replicas):
            rep = [np.random.randint(0, self.sacred_geometry) for _ in range(self.num_cells)]
            replicas.append(rep)
        replicas[0] = list(original_states)  # first replica starts from current

        energies = [0.0] * num_replicas
        for r in range(num_replicas):
            for k, c in enumerate(self.cells):
                c.state = replicas[r][k]
            energies[r] = self.compute_total_energy()

        best_energy = min(energies)
        best_replica = energies.index(best_energy)
        total_swaps = 0
        num_rounds = max_steps // steps_per_swap

        for round_i in range(num_rounds):
            # Relax each replica
            for r in range(num_replicas):
                for k, c in enumerate(self.cells):
                    c.state = replicas[r][k]
                self.temperature = temps[r]
                for _ in range(steps_per_swap):
                    self.relax_step()
                replicas[r] = [c.state for c in self.cells]
                energies[r] = self.compute_total_energy()

            # Attempt swaps between adjacent temperatures
            for r in range(num_replicas - 1):
                dBeta = (1.0 / temps[r]) - (1.0 / temps[r + 1])
                dE = energies[r] - energies[r + 1]
                swap_arg = min(dBeta * dE, 500)  # clamp to avoid overflow
                if swap_arg < 0 or np.random.random() < math.exp(swap_arg):
                    replicas[r], replicas[r + 1] = replicas[r + 1], replicas[r]
                    energies[r], energies[r + 1] = energies[r + 1], energies[r]
                    total_swaps += 1

            cur_best = min(energies)
            if cur_best < best_energy:
                best_energy = cur_best
                best_replica = energies.index(cur_best)

            self._emit_sensor("energy.total", round_i * steps_per_swap, best_energy)
            self.energy_history.append(best_energy)
            if round_i % max(1, num_rounds // 10) == 0:
                print(f"   Round {round_i}: best E={best_energy:.4f}, swaps={total_swaps}")

        # Restore best replica
        for k, c in enumerate(self.cells):
            c.state = replicas[best_replica][k]
        self.ground_state = [c.state for c in self.cells]
        self.solution = self._extract_solution()
        elapsed = time.time() - start
        print(f"   Best energy: {best_energy:.4f}, swaps: {total_swaps} ({elapsed:.2f}s)")
        return {
            "ground_state": self.ground_state,
            "final_energy": best_energy,
            "steps": max_steps,
            "time": elapsed,
            "solution": self.solution,
            "swaps": total_swaps,
            "temperatures": temps,
        }

    # ------------------------------------------------------------------
    # Exploration: sovereign tempering (pack-aware parallel tempering)
    # ------------------------------------------------------------------

    def sovereign_tempering(self, num_replicas: int = 6,
                            T_min: float = 0.05, T_max: float = 10.0,
                            steps_per_swap: int = 100,
                            max_steps: int = 10000) -> Dict:
        """
        Parallel tempering where replicas are a sovereign pack.

        Each replica is a specialist at a different temperature.
        Pack dynamics determine collective behavior:

        - Harmonic mean of convergence rates = pack floor
          (one stuck replica drags the whole ensemble)
        - Antifragile: replicas that survive swap rejections get stronger
          (their states persist, meaning they found robust configurations)
        - Complementary specialization: high-T replicas explore (scouts),
          low-T replicas exploit (settlers), medium-T bridge the gap
        - Sovereignty: when the harmonic mean of convergence rates exceeds
          threshold, the pack has found coherence — stop early

        The solver itself becomes sovereign.
        """
        print(f"\n   Sovereign tempering: {num_replicas} replicas as pack")
        start = time.time()

        temps = [T_min * (T_max / T_min) ** (i / max(num_replicas - 1, 1))
                 for i in range(num_replicas)]

        original_states = [c.state for c in self.cells]
        replicas = []
        for _ in range(num_replicas):
            replicas.append([np.random.randint(0, self.sacred_geometry)
                             for _ in range(self.num_cells)])
        replicas[0] = list(original_states)

        energies = [0.0] * num_replicas
        for r in range(num_replicas):
            for k, c in enumerate(self.cells):
                c.state = replicas[r][k]
            energies[r] = self.compute_total_energy()

        best_energy = min(energies)
        best_replica = energies.index(best_energy)
        total_swaps = 0
        num_rounds = max_steps // steps_per_swap

        # Pack dynamics tracking
        resiliences = [0.5] * num_replicas  # each replica's resilience
        stress_history = []                  # shared stress history
        convergence_rates = [0.0] * num_replicas
        prev_energies = list(energies)

        for round_i in range(num_rounds):
            # Relax each replica (each is a specialist at its temperature)
            for r in range(num_replicas):
                for k, c in enumerate(self.cells):
                    c.state = replicas[r][k]
                self.temperature = temps[r]
                for _ in range(steps_per_swap):
                    self.relax_step()
                replicas[r] = [c.state for c in self.cells]
                energies[r] = self.compute_total_energy()

                # Track convergence rate per replica
                if prev_energies[r] != 0:
                    improvement = (prev_energies[r] - energies[r]) / max(abs(prev_energies[r]), 1e-15)
                else:
                    improvement = 0.0
                convergence_rates[r] = abs(improvement)
                prev_energies[r] = energies[r]

            # Attempt swaps (with antifragile tracking)
            round_stress = 0.0
            for r in range(num_replicas - 1):
                dBeta = (1.0 / temps[r]) - (1.0 / temps[r + 1])
                dE = energies[r] - energies[r + 1]
                swap_arg = min(dBeta * dE, 500)
                if swap_arg < 0 or np.random.random() < math.exp(swap_arg):
                    replicas[r], replicas[r + 1] = replicas[r + 1], replicas[r]
                    energies[r], energies[r + 1] = energies[r + 1], energies[r]
                    total_swaps += 1
                else:
                    # Rejected swap = stress event
                    round_stress += 0.1
                    # Replica that survived rejection gets more resilient
                    resiliences[r] = min(resiliences[r] * 1.02, 1.0)

            stress_history.append(round_stress)

            # Antifragile adaptation: shared stress strengthens all
            if len(stress_history) > 5:
                mean_stress = sum(stress_history[-5:]) / 5
                for r in range(num_replicas):
                    resiliences[r] = min(resiliences[r] * (1 + mean_stress * 0.1), 1.0)

            cur_best = min(energies)
            if cur_best < best_energy:
                best_energy = cur_best
                best_replica = energies.index(cur_best)

            self._emit_sensor("energy.total", round_i * steps_per_swap, best_energy)
            self.energy_history.append(best_energy)

            # Pack sovereignty check: harmonic mean of convergence rates
            nonzero_rates = [max(cr, 1e-15) for cr in convergence_rates]
            hm_rate = num_replicas / sum(1.0 / r for r in nonzero_rates)

            if round_i % max(1, num_rounds // 10) == 0:
                hm_res = num_replicas / sum(1.0 / max(r, 1e-15) for r in resiliences)
                print(f"   Round {round_i}: E={best_energy:.4f}, swaps={total_swaps}, "
                      f"HM_resilience={hm_res:.3f}, convergence={hm_rate:.6f}")

            # Sovereignty: if all replicas have converged (harmonic mean of rates near 0
            # AND best energy is stable), the pack is sovereign — stop early
            if round_i > 5 and hm_rate < 1e-8:
                recent_best = self.energy_history[-5:]
                if len(recent_best) >= 5 and np.var(recent_best) < 1e-10:
                    print(f"   Pack sovereignty achieved at round {round_i}")
                    break

        # Restore best replica
        for k, c in enumerate(self.cells):
            c.state = replicas[best_replica][k]
        self.ground_state = [c.state for c in self.cells]
        self.solution = self._extract_solution()
        elapsed = time.time() - start

        hm_res = num_replicas / sum(1.0 / max(r, 1e-15) for r in resiliences)
        print(f"   Best energy: {best_energy:.4f}, swaps: {total_swaps}, "
              f"HM_resilience: {hm_res:.3f} ({elapsed:.2f}s)")

        return {
            "ground_state": self.ground_state,
            "final_energy": best_energy,
            "steps": max_steps,
            "time": elapsed,
            "solution": self.solution,
            "swaps": total_swaps,
            "temperatures": temps,
            "resiliences": resiliences,
            "hm_resilience": hm_res,
            "stress_history": stress_history,
            "sovereign": hm_rate < 1e-8 if 'hm_rate' in dir() else False,
        }

    # ------------------------------------------------------------------
    # Exploration: landscape scan
    # ------------------------------------------------------------------

    def landscape_scan(self, num_samples: int = 1000) -> Dict:
        """Randomly sample configurations and map the energy landscape."""
        print(f"\n   Scanning landscape ({num_samples} samples)...")
        energies = []
        best_energy = float("inf")
        best_config = None

        for s in range(num_samples):
            for c in self.cells:
                c.state = np.random.randint(0, self.sacred_geometry)
            E = self.compute_total_energy()
            energies.append(E)
            if E < best_energy:
                best_energy = E
                best_config = [c.state for c in self.cells]

        arr = np.array(energies)
        result = {
            "energies": arr,
            "min_energy": float(np.min(arr)),
            "max_energy": float(np.max(arr)),
            "mean_energy": float(np.mean(arr)),
            "std_energy": float(np.std(arr)),
            "best_config": best_config,
        }
        print(f"   E range: [{result['min_energy']:.4f}, {result['max_energy']:.4f}]")
        print(f"   E mean: {result['mean_energy']:.4f} +/- {result['std_energy']:.4f}")
        return result

    # ------------------------------------------------------------------
    # Solution extraction
    # ------------------------------------------------------------------

    def _extract_solution(self) -> Dict:
        if self.problem_type == ProblemType.FACTORIZATION:
            return self._extract_factorization_solution()
        elif self.problem_type == ProblemType.SAT:
            return self._extract_sat_solution()
        elif self.problem_type == ProblemType.TSP:
            return self._extract_tsp_solution()
        elif self.problem_type == ProblemType.GRAPH_COLORING:
            return self._extract_graph_coloring_solution()
        elif self.problem_type == ProblemType.OPTIMIZATION:
            return self._extract_optimization_solution()
        return {"raw_states": self.ground_state}

    def _extract_factorization_solution(self) -> Dict:
        N = self.problem_data["N"]
        dpf = self.problem_data["digits_per_factor"]
        cpp = self.problem_data["cells_per_pair"]
        best_pair = None
        best_residual = float("inf")
        all_factors = set()
        for pair_start in range(0, self.num_cells - cpp + 1, cpp):
            fa_indices = list(range(pair_start, pair_start + dpf))
            fb_indices = list(range(pair_start + dpf, pair_start + cpp))
            fa = self._cells_to_factor(fa_indices)
            fb = self._cells_to_factor(fb_indices)
            residual = (fa * fb - N) ** 2
            if residual < best_residual:
                best_residual = residual
                best_pair = (fa, fb)
            if fa > 1 and N % fa == 0:
                all_factors.add(fa)
            if fb > 1 and N % fb == 0:
                all_factors.add(fb)
        factors = sorted(all_factors)
        correct = best_pair is not None and best_pair[0] * best_pair[1] == N
        result = {
            "factors": factors,
            "best_pair": best_pair,
            "residual": best_residual,
            "N": N,
            "verified": correct,
        }
        # Enrich with glyph-native representation
        if HAS_GLYPH_MATH and best_pair:
            ga = OctahedralNumber.from_decimal(best_pair[0])
            gb = OctahedralNumber.from_decimal(best_pair[1])
            gN = OctahedralNumber.from_decimal(N)
            result["glyph_pair"] = (ga.to_glyphs(), gb.to_glyphs())
            result["glyph_N"] = gN.to_glyphs()
            result["glyph_product"] = (ga * gb).to_glyphs()
        return result

    def _extract_sat_solution(self) -> Dict:
        assignment = {}
        for i, cell in enumerate(self.cells):
            assignment[i + 1] = cell.state >= 4
        return {"assignment": assignment, "satisfies": self._verify_sat(assignment)}

    def _verify_sat(self, assignment: Dict) -> bool:
        for clause in self.problem_data["clauses"]:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                val = assignment.get(var, False)
                if (lit > 0 and val) or (lit < 0 and not val):
                    satisfied = True
                    break
            if not satisfied:
                return False
        return True

    def _extract_tsp_solution(self) -> Dict:
        tour = [c.state for c in self.cells]
        return {"tour": tour, "length": self._tour_length(tour)}

    def _tour_length(self, tour: List[int]) -> float:
        cities = self.problem_data["cities"]
        total = 0.0
        for i in range(len(tour)):
            a = tour[i] % len(cities)
            b = tour[(i + 1) % len(tour)] % len(cities)
            total += np.linalg.norm(cities[a] - cities[b])
        return total

    def _extract_graph_coloring_solution(self) -> Dict:
        nc = self.problem_data["num_colors"]
        coloring = {i: self.cells[i].state % nc for i in range(min(self.num_cells, self.problem_data["num_nodes"]))}
        violations = 0
        for n_i, n_j in self.problem_data["adjacency"]:
            if coloring.get(n_i) == coloring.get(n_j):
                violations += 1
        return {"coloring": coloring, "violations": violations, "valid": violations == 0}

    def _extract_optimization_solution(self) -> Dict:
        states = [c.state for c in self.cells]
        cost = self.problem_data["cost_fn"](states)
        return {"states": states, "cost": cost}

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_state_distribution(self) -> Dict[int, int]:
        """Histogram of cell states 0-7."""
        dist = {s: 0 for s in range(self.sacred_geometry)}
        for c in self.cells:
            dist[c.state] = dist.get(c.state, 0) + 1
        return dist

    def get_energy_breakdown(self) -> Dict[str, float]:
        """Per-component energy breakdown."""
        cell_e = sum(c.energy for c in self.cells)
        coupling_e = 0.0
        for i, ci in enumerate(self.cells):
            for j in ci.neighbors:
                if j > i:
                    sd = abs(ci.state - self.cells[j].state)
                    coupling_e += self.coupling_strength * math.sin(sd * math.pi / 4) ** 2
        return {"cell_energy": cell_e, "coupling_energy": coupling_e, "total": cell_e + coupling_e}

    def get_convergence_rate(self, window: int = 100) -> float:
        """Linear regression slope of energy over last `window` entries."""
        if len(self.energy_history) < 2:
            return 0.0
        recent = self.energy_history[-window:]
        n = len(recent)
        x = np.arange(n, dtype=float)
        y = np.array(recent)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / max(n * np.sum(x ** 2) - np.sum(x) ** 2, 1e-15)
        return float(slope)

    def glyph_trace(self, max_cells: int = 10) -> str:
        """Return cell states as glyph string."""
        glyphs = self._glyphs
        parts = []
        for c in self.cells[:max_cells]:
            g = glyphs[c.state] if c.state < len(glyphs) else str(c.state)
            parts.append(g)
        if self.num_cells > max_cells:
            parts.append("...")
        return "".join(parts)

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------

    def visualize_mandala(self):
        """Visualize mandala structure (requires matplotlib)."""
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 10))
            for cell in self.cells:
                x, y = cell.position
                color = plt.cm.hsv(cell.state / self.sacred_geometry)
                size = 100 * PHI ** (self.golden_depth - cell.depth)
                ax.scatter(x, y, c=[color], s=size, alpha=0.7)
            for i, ci in enumerate(self.cells):
                for j in ci.neighbors:
                    if j > i:
                        cj = self.cells[j]
                        ax.plot([ci.position[0], cj.position[0]],
                                [ci.position[1], cj.position[1]],
                                "k-", alpha=0.1, linewidth=0.5)
            ax.set_aspect("equal")
            ax.set_title("Mandala Computing Structure")
            ax.axis("off")
            plt.tight_layout()
            plt.savefig("/mnt/user-data/outputs/mandala_structure.png", dpi=150)
            print("   Visualization saved")
        except ImportError:
            print("   matplotlib not available for visualization")


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_factorization():
    """Demonstrate factorization through geometric relaxation."""
    print("=" * 60)
    print("DEMO: FACTORIZATION VIA GEOMETRIC GROUND STATE")
    print("=" * 60)

    for N in [15, 143, 221]:
        print(f"\n   --- N={N} ---")
        computer = MandalaComputer(golden_depth=5, sacred_geometry=8, temperature=0.5)
        computer.encode_factorization(N)
        result = computer.simulated_annealing(max_steps=8000, T_start=5.0, T_end=0.001)
        sol = result["solution"]
        glyph_info = ""
        if "glyph_pair" in sol:
            glyph_info = f"  glyph: {sol['glyph_pair'][0]} * {sol['glyph_pair'][1]} = {sol['glyph_N']}"
        print(f"   Best pair: {sol['best_pair']}, verified: {sol['verified']}{glyph_info}")

    return computer, result


def demo_sat():
    """Demonstrate SAT solving."""
    print("\n" + "=" * 60)
    print("DEMO: SAT SOLVING VIA GEOMETRIC GROUND STATE")
    print("=" * 60)
    clauses = [[1, 2], [-1, 3], [-2, -3]]
    computer = MandalaComputer(golden_depth=3, sacred_geometry=8, temperature=0.3)
    computer.encode_sat(clauses)
    result = computer.relax_to_ground_state(max_steps=3000)
    print(f"\n   Satisfies: {result['solution']['satisfies']}")
    return computer, result


def demo_graph_coloring():
    """Demonstrate graph coloring."""
    print("\n" + "=" * 60)
    print("DEMO: GRAPH COLORING")
    print("=" * 60)
    # Triangle graph: 3 nodes, 3 edges, 3 colors
    adjacency = [[0, 1], [1, 2], [0, 2]]
    num_colors = 3
    computer = MandalaComputer(golden_depth=3, sacred_geometry=8, temperature=0.5)
    computer.encode_graph_coloring(adjacency, num_colors)
    result = computer.simulated_annealing(max_steps=3000, T_start=2.0, T_end=0.01)
    sol = result["solution"]
    print(f"\n   Coloring: {sol['coloring']}")
    print(f"   Violations: {sol['violations']}, valid: {sol['valid']}")
    return computer, result


def demo_optimization():
    """Demonstrate generic optimization."""
    print("\n" + "=" * 60)
    print("DEMO: GENERIC OPTIMIZATION")
    print("=" * 60)
    # Minimize sum of squared differences between adjacent cell states
    def cost_fn(states):
        total = 0.0
        for i in range(len(states) - 1):
            total += (states[i] - states[i + 1]) ** 2
        return total

    computer = MandalaComputer(golden_depth=3, sacred_geometry=8, temperature=1.0)
    computer.encode_optimization(cost_fn, num_variables=10)
    result = computer.simulated_annealing(max_steps=3000, T_start=3.0, T_end=0.01)
    print(f"\n   Final cost: {result['solution']['cost']:.4f}")
    print(f"   States: {result['solution']['states'][:10]}")
    return computer, result


def demo_parallel_tempering():
    """Demonstrate parallel tempering exploration."""
    print("\n" + "=" * 60)
    print("DEMO: PARALLEL TEMPERING")
    print("=" * 60)
    N = 143
    computer = MandalaComputer(golden_depth=4, sacred_geometry=8)
    computer.encode_factorization(N)
    result = computer.parallel_tempering(num_replicas=4, T_min=0.1, T_max=5.0, max_steps=4000)
    print(f"\n   N={N}, factors={result['solution']['factors']}")
    print(f"   Swaps: {result['swaps']}")
    return computer, result


def demo_landscape():
    """Demonstrate landscape scanning."""
    print("\n" + "=" * 60)
    print("DEMO: ENERGY LANDSCAPE SCAN")
    print("=" * 60)
    N = 15
    computer = MandalaComputer(golden_depth=3, sacred_geometry=8)
    computer.encode_factorization(N)
    scan = computer.landscape_scan(num_samples=500)
    print(f"\n   Landscape mapped: {len(scan['energies'])} samples")
    return computer, scan


if __name__ == "__main__":
    print("=" * 60)
    print("MANDALA COMPUTING SIMULATOR v2.0")
    print("   Geometric Intelligence Through Natural Symmetry")
    print("=" * 60)

    demo_factorization()
    demo_sat()
    demo_graph_coloring()
    demo_optimization()
    demo_parallel_tempering()
    demo_landscape()

    print("\n" + "=" * 60)
    print("ALL DEMONSTRATIONS COMPLETE")
    print("=" * 60)
