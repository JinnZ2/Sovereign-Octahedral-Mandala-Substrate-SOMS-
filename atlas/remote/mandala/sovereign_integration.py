"""
SOVEREIGN INTEGRATION v1.0
Bridges Living-Intelligence + Inversion into Mandala-Computing.

Three integration layers:

1. PHYSICAL NODE GLYPHS
   sovereign.py's 8 PhysicalNodes become octahedral glyph states.
   Each glyph IS a physical field. Arithmetic on glyphs is arithmetic on fields.

2. CONSTRAINT VALIDATION
   field_system.py's constraint/drift/thermal-limit model becomes the
   constraint agent's validation layer. Agents can check if their state
   satisfies physical invariants before expanding.

3. RESONANCE ENERGY
   sovereign.py's transition_frequency and pack resonance become energy
   functions for the mandala solver. Resonance peaks ARE ground states.
   The solver finds sovereignty by relaxing to maximum coherence.

Usage:
    from sovereign_integration import (
        PhysicalGlyph, SovereignEnergy, FieldConstraints,
        SovereignAgent,
    )

    # Agent with physical-field awareness
    agent = SovereignAgent(seed_id="SHAPE.OCTA", energy_type="harmonic")
    agent.set_resource_budget(compute=500)
    agent.bloom(depth=2)
    agent.validate()       # field_system constraint check
    agent.find_resonance() # mandala solver finds sovereignty
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import math
import time

from octahedral_arithmetic import (
    OctahedralNumber, GlyphFraction, GLYPHS, BASE, PHI,
)
from constraint_agent import (
    ConstraintAgent, SeedGeometry, ResourceBudget,
    ExplorationNode, Discovery,
)


# ---------------------------------------------------------------------------
# Layer 1: Physical Node Glyphs
# ---------------------------------------------------------------------------

class PhysicalGlyph(Enum):
    """
    The 8 octahedral glyphs ARE physical fields.

    From sovereign.py's PhysicalNode enum, mapped to glyph states.
    When you see ⊕ you see electromagnetic. When you see ⊘ you see thermal.
    The math on glyphs is math on physics.
    """
    EM           = (0, "\u2295", "electromagnetic")   # ⊕
    MECHANICAL   = (1, "\u2296", "mechanical")         # ⊖
    CHEMICAL     = (2, "\u2297", "chemical")            # ⊗
    THERMAL      = (3, "\u2298", "thermal")             # ⊘
    RADIATIVE    = (4, "\u2299", "radiative")           # ⊙
    FLUID        = (5, "\u229a", "fluid")               # ⊚
    GRAVITATIONAL = (6, "\u229b", "gravitational")      # ⊛
    KINETIC      = (7, "\u229c", "kinetic")             # ⊜

    def __init__(self, state: int, glyph: str, field_name: str):
        self.state = state
        self.glyph = glyph
        self.field_name = field_name

    @classmethod
    def from_state(cls, state: int) -> PhysicalGlyph:
        for pg in cls:
            if pg.state == state % 8:
                return pg
        return cls.EM

    @classmethod
    def from_energy_type(cls, energy_type: str) -> PhysicalGlyph:
        """Map sovereign.py energy types to physical glyphs."""
        mapping = {
            "harmonic": cls.EM,
            "kinetic": cls.KINETIC,
            "radiant": cls.RADIATIVE,
            "chemical": cls.CHEMICAL,
            "mechanical": cls.MECHANICAL,
        }
        return mapping.get(energy_type, cls.EM)


# Compatibility matrix from sovereign.py, indexed by glyph state pairs
# Stored as exact GlyphFractions (no float drift)
COMPATIBILITY = {}
_compat_raw = {
    "harmonic":    {"harmonic": (10, 10), "kinetic": (7, 10), "radiant": (8, 10), "chemical": (5, 10), "mechanical": (9, 10)},
    "kinetic":     {"kinetic": (10, 10), "harmonic": (7, 10), "radiant": (6, 10), "chemical": (6, 10), "mechanical": (8, 10)},
    "radiant":     {"radiant": (10, 10), "harmonic": (8, 10), "kinetic": (6, 10), "chemical": (4, 10), "mechanical": (5, 10)},
    "chemical":    {"chemical": (10, 10), "harmonic": (5, 10), "kinetic": (6, 10), "radiant": (4, 10), "mechanical": (6, 10)},
    "mechanical":  {"mechanical": (10, 10), "harmonic": (9, 10), "kinetic": (8, 10), "radiant": (5, 10), "chemical": (6, 10)},
}

# Build glyph-indexed compatibility
_type_to_glyph = {
    "harmonic": 0, "mechanical": 1, "chemical": 2,
    "thermal": 3, "radiant": 4, "fluid": 5,
    "gravitational": 6, "kinetic": 7,
}
for etype_a, row in _compat_raw.items():
    ga = _type_to_glyph.get(etype_a, 0)
    for etype_b, (p, q) in row.items():
        gb = _type_to_glyph.get(etype_b, 0)
        COMPATIBILITY[(ga, gb)] = GlyphFraction.from_decimal_ratio(p, q)


def glyph_compatibility(state_a: int, state_b: int) -> GlyphFraction:
    """Exact compatibility between two glyph states as a fraction."""
    key = (state_a % 8, state_b % 8)
    return COMPATIBILITY.get(key, GlyphFraction.from_decimal_ratio(5, 10))


# ---------------------------------------------------------------------------
# Layer 2: Field Constraints (from Inversion/field_system.py)
# ---------------------------------------------------------------------------

@dataclass
class FieldState:
    """System state for constraint checking. Mirrors field_system.py."""
    soil_trend: float = 0.0
    water_retention: float = 0.5
    input_energy: float = 1.0
    output_yield: float = 1.0
    disturbance: float = 0.0
    waste_factor: float = 0.4
    nutrient_density: float = 0.8
    coupling_strength: float = 0.5
    ecological_amplification: float = 2.0


class FieldConstraints:
    """
    Constraint validation from Inversion's field_system.

    Ported into Mandala-Computing as the agent's invariant layer.
    All constraints must hold for system health.
    """

    @staticmethod
    def regen_capacity(state: FieldState) -> float:
        """Regeneration capacity: base * soil * water * (1-disturbance)."""
        return 1.0 * (1.0 + state.soil_trend) * state.water_retention * (1.0 - state.disturbance)

    @staticmethod
    def check_constraints(state: FieldState) -> Dict[str, bool]:
        """All constraints that must hold."""
        rc = FieldConstraints.regen_capacity(state)
        energy_ratio = state.output_yield / max(state.input_energy, 1e-15)
        return {
            "soil_positive": state.soil_trend >= 0,
            "water_non_degrading": state.water_retention >= 0.4,
            "no_overextraction": state.output_yield <= rc,
            "energy_ratio": energy_ratio >= 1.0,
        }

    @staticmethod
    def detect_drift(state: FieldState) -> Dict[str, bool]:
        """Which constraints are violated (True = drifting)."""
        return {k: not v for k, v in FieldConstraints.check_constraints(state).items()}

    @staticmethod
    def health_score(state: FieldState) -> float:
        """Fraction of constraints satisfied (0.0 to 1.0)."""
        c = FieldConstraints.check_constraints(state)
        return sum(c.values()) / len(c)

    @staticmethod
    def thermal_limit(state: FieldState) -> Dict[str, object]:
        """Detect system redlining."""
        rc = FieldConstraints.regen_capacity(state)
        prediction_error = abs(state.output_yield - rc)
        thermal_load = state.disturbance * state.input_energy
        critical = thermal_load > 0.8 or prediction_error > 0.5
        return {
            "prediction_error": prediction_error,
            "thermal_load": thermal_load,
            "critical": critical,
        }

    @staticmethod
    def effective_yield(state: FieldState) -> float:
        """Yield adjusted for waste, nutrients, and ecological coupling."""
        y_adj = state.output_yield * (1 - state.waste_factor) * state.nutrient_density ** 2
        gk = 1 + state.ecological_amplification * state.coupling_strength
        return y_adj * gk


# ---------------------------------------------------------------------------
# Layer 3: Resonance Energy (from sovereign.py)
# ---------------------------------------------------------------------------

class SovereignEnergy:
    """
    Sovereign resonance as a mandala energy function.

    transition_frequency = compatibility * stress * energy_profile
    Pack resonance = average of all pairwise frequencies.
    Sovereignty = resonance > threshold.

    When used as energy for the mandala solver:
    E = -resonance (minimize energy = maximize resonance).
    Ground state = sovereignty.
    """

    @staticmethod
    def transition_frequency(state_a: int, energy_a: float, resilience_a: float,
                             state_b: int, energy_b: float,
                             entropy: float = 0.5) -> float:
        """
        Energy-gated transition frequency between two glyph states.

        From sovereign.py: freq = compat * stress * energy_b

        Stress models how the element responds to environmental entropy.
        High resilience means the element *thrives* under stress, not
        just survives. The sigmoid ensures stress response is bounded
        and rewards resilience nonlinearly:

          stress = resilience^2 / (resilience^2 + entropy^2)

        At resilience=0.85, entropy=0.5: stress = 0.74 (functional)
        At resilience=0.85, entropy=0.9: stress = 0.47 (strained but alive)
        At resilience=0.3,  entropy=0.9: stress = 0.10 (collapsing)

        Sovereignty doesn't require calm. It requires resilience.
        """
        compat = glyph_compatibility(state_a, state_b)
        compat_float = compat.num.to_decimal() / max(compat.den.to_decimal(), 1)
        # Sigmoid stress: resilience^2 / (resilience^2 + entropy^2)
        # Rewards high resilience under any entropy level
        r2 = resilience_a ** 2
        e2 = entropy ** 2
        stress = r2 / (r2 + e2 + 1e-15)
        return compat_float * stress * energy_b

    @staticmethod
    def pack_resonance(states: List[int], energies: List[float],
                       resiliences: List[float], entropy: float = 0.5,
                       stress_history: List[float] = None) -> float:
        """
        Pack resonance with complementary specialization.

        Three principles from physics and biology:

        1. FLOOR (harmonic mean): No member can be so weak that the pack
           breaks. The weakest bond still determines minimum coherence.
           Crystal: dislocation propagates. Network: weakest link fails.

        2. SPECIALIZATION (role coverage): Different members excelling at
           different things is stronger than everyone being the same.
           Alloys > pure metals. Wolf pack > clones. Ecosystem > monoculture.
           Homogenization leads to decay; complementary distribution thrives.

        3. COMPLEMENTARY COUPLING: The value of specialization depends on
           how those specializations interact. EM + Mechanical (compat 0.9)
           is a stronger bond than Chemical + Radiative (compat 0.4).
           The compatibility matrix weights which combinations synergize.

        Pack resonance = base_resonance * specialization_bonus

        Where specialization_bonus rewards:
          - Diversity of physical fields represented (role coverage)
          - Each member's resilience in their specific role
          - Compatibility between the roles that are covered
        """
        n = len(states)
        if n < 2:
            return 0.0

        # Antifragile adaptation: stress history strengthens each member
        adapted = list(resiliences)
        if stress_history:
            mean_past = sum(stress_history) / len(stress_history)
            for i in range(n):
                adapted[i] = min(adapted[i] * (1 + mean_past * 0.5), 2.0 * resiliences[i])

        # Floor: harmonic mean ensures no catastrophically weak link
        inv_sum = sum(1.0 / max(r, 1e-15) for r in adapted)
        floor_resilience = n / inv_sum if inv_sum > 0 else 0.0

        # Role coverage: which physical fields are represented and how strongly?
        # Each member contributes their resilience to their field's coverage
        field_coverage = {}  # field_state -> max resilience in that field
        for i in range(n):
            field = states[i] % 8
            current_best = field_coverage.get(field, 0.0)
            field_coverage[field] = max(current_best, adapted[i])

        # Specialization bonus:
        # - More distinct fields = more coverage (up to 8)
        # - Each field weighted by its best member's resilience
        # - Complementary pairs (high compatibility) amplify each other
        n_fields = len(field_coverage)
        coverage_fraction = n_fields / 8  # what fraction of field space is covered

        # Complementary amplification: average compatibility between covered fields
        complement_sum = 0.0
        complement_count = 0
        covered_fields = list(field_coverage.keys())
        for i, fa in enumerate(covered_fields):
            for fb in covered_fields[i + 1:]:
                c = glyph_compatibility(fa, fb)
                c_val = c.num.to_decimal() / max(c.den.to_decimal(), 1)
                # Weight by both fields' coverage strength
                weight = field_coverage[fa] * field_coverage[fb]
                complement_sum += c_val * weight
                complement_count += 1

        complement_avg = complement_sum / max(complement_count, 1)

        # Specialization bonus: coverage * complementarity
        # Ranges from ~0.5 (one field, no complement) to ~1.5 (diverse, high complement)
        specialization = 0.5 + coverage_fraction * 0.5 + complement_avg * 0.5

        # Base resonance uses each member's OWN adapted resilience for their
        # pairwise interactions, but floored by the harmonic mean
        total = 0.0
        count = 0
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Each member uses max(own_resilience, floor) — the pack
                    # lifts weak members but doesn't drag down strong ones
                    eff_res_i = max(adapted[i], floor_resilience)
                    total += SovereignEnergy.transition_frequency(
                        states[i], energies[i], eff_res_i,
                        states[j], energies[j], entropy,
                    )
                    count += 1
        base_resonance = total / max(count, 1)

        return base_resonance * specialization

    @staticmethod
    def is_sovereign(resonance: float, entropy: float = 0.5,
                     base_threshold: float = 0.3) -> bool:
        """
        Has the system achieved sovereignty?

        Sovereignty is relative to environmental difficulty.
        A system maintaining 0.5 resonance at entropy=0.9 is more
        sovereign than one at 0.8 in calm conditions.

        Effective threshold = base_threshold / (1 + entropy)

        At entropy=0.0: need resonance > 0.30
        At entropy=0.5: need resonance > 0.20
        At entropy=0.9: need resonance > 0.16

        The harder the environment, the less resonance is needed —
        because maintaining ANY coherence under chaos IS sovereignty.
        """
        effective_threshold = base_threshold / (1 + entropy)
        return resonance > effective_threshold

    @staticmethod
    def as_mandala_cost(states: List[int]) -> float:
        """
        Cost function for mandala solver (field-aware coupling).

        Uses the compatibility matrix directly as coupling energy between
        adjacent cells. This is NOT a black-box wrapper — the solver sees
        the physical field structure through the glyph states.

        E = -sum(compatibility(s_i, s_j)) for all neighbor pairs
        Minimizing E = maximizing total compatibility = finding sovereignty.
        """
        if len(states) < 2:
            return 0.0
        total_compat = 0.0
        count = 0
        for i in range(len(states)):
            for j in range(i + 1, min(i + 4, len(states))):  # local neighbors
                c = glyph_compatibility(states[i], states[j])
                total_compat += c.num.to_decimal() / max(c.den.to_decimal(), 1)
                count += 1
        if count == 0:
            return 0.0
        avg = total_compat / count
        return -avg  # negative because solver minimizes


# ---------------------------------------------------------------------------
# Unified: SovereignAgent
# ---------------------------------------------------------------------------

class SovereignAgent(ConstraintAgent):
    """
    A constraint agent with physical-field awareness and sovereign validation.

    Extends ConstraintAgent with:
    - Physical glyph interpretation (each state = a physical field)
    - Field constraint validation (soil, water, energy, thermal limits)
    - Resonance-based exploration (sovereign energy as discovery metric)
    """

    def __init__(self, seed_id: str = "SHAPE.OCTA",
                 home_families: List[str] = None,
                 energy_type: str = "harmonic"):
        super().__init__(seed_id=seed_id, home_families=home_families or [])
        self.energy_type = energy_type
        self.physical_glyph = PhysicalGlyph.from_energy_type(energy_type)
        self.field_state = FieldState()
        self.sovereignty_history: List[float] = []
        print(f"  Physical field: {self.physical_glyph.glyph} {self.physical_glyph.field_name}")

    # ------------------------------------------------------------------
    # Field constraint validation
    # ------------------------------------------------------------------

    def validate(self) -> Dict:
        """
        Check field constraints on current state.

        Maps agent's exploration intensity to field_system parameters:
        - depth -> disturbance (deeper exploration = more disturbance)
        - nodes -> output_yield (more nodes = more extraction)
        - budget remaining -> input_energy
        """
        # Map agent state to field parameters
        max_depth = max(self.budget.depth_limit, 1)
        self.field_state.disturbance = min(self.current_depth / max_depth, 1.0)
        self.field_state.output_yield = len(self.nodes) / max(100, len(self.nodes))
        remaining = self.budget.compute.num.to_decimal() / max(self.budget.compute.den.to_decimal(), 1)
        self.field_state.input_energy = max(remaining / 100, 0.1)
        # Coupling from entanglement density
        if self.nodes:
            total_rels = sum(len(n.relationships) for n in self.nodes.values())
            self.field_state.coupling_strength = min(total_rels / max(len(self.nodes), 1), 1.0)

        health = FieldConstraints.health_score(self.field_state)
        drift = FieldConstraints.detect_drift(self.field_state)
        thermal = FieldConstraints.thermal_limit(self.field_state)
        yield_info = FieldConstraints.effective_yield(self.field_state)

        drifting = [k for k, v in drift.items() if v]

        print(f"\n  Validation:")
        print(f"    Health score: {health:.2f}")
        print(f"    Constraints: {sum(not v for v in drift.values())}/{len(drift)} satisfied")
        if drifting:
            print(f"    DRIFT: {', '.join(drifting)}")
        if thermal["critical"]:
            print(f"    THERMAL ALERT: load={thermal['thermal_load']:.3f}")
        print(f"    Effective yield: {yield_info:.4f}")
        print(f"    Coupling: {self.field_state.coupling_strength:.3f}")

        return {
            "health": health,
            "drift": drift,
            "thermal": thermal,
            "yield": yield_info,
        }

    # ------------------------------------------------------------------
    # Resonance discovery
    # ------------------------------------------------------------------

    def find_resonance(self) -> Dict:
        """
        Compute pack resonance across exploration nodes.

        Groups nodes into packs by depth, computes pairwise resonance
        using sovereign energy function. Reports sovereignty status.
        """
        print(f"\n  Computing resonance...")

        # Group nodes by depth into packs
        by_depth = {}
        for node in self.nodes.values():
            by_depth.setdefault(node.depth, []).append(node)

        pack_results = []
        for depth, nodes in sorted(by_depth.items()):
            states = [n.position.to_decimal() % 8 for n in nodes]
            energies = [0.9] * len(states)
            resiliences = [0.85] * len(states)

            # Cyclic entropy based on depth
            entropy = 0.5 * (1 + math.sin(depth * math.pi / max(self.max_depth_reached, 1)))

            resonance = SovereignEnergy.pack_resonance(states, energies, resiliences, entropy)
            sovereign = SovereignEnergy.is_sovereign(resonance, entropy)
            self.sovereignty_history.append(resonance)

            pack_results.append({
                "depth": depth,
                "nodes": len(nodes),
                "resonance": resonance,
                "sovereign": sovereign,
            })

            status = "SOVEREIGN" if sovereign else f"resonance={resonance:.4f}"
            print(f"    Depth {depth} ({len(nodes)} nodes): {status}")

        # Overall system resonance
        all_states = [n.position.to_decimal() % 8 for n in self.nodes.values()]
        overall = SovereignEnergy.pack_resonance(
            all_states, [0.9] * len(all_states), [0.85] * len(all_states), 0.5
        )
        system_sovereign = SovereignEnergy.is_sovereign(overall, entropy=0.5)

        print(f"\n    System resonance: {overall:.4f}")
        print(f"    System sovereign: {system_sovereign}")

        # Report physical glyph distribution
        dist = {}
        for s in all_states:
            pg = PhysicalGlyph.from_state(s)
            dist[pg.field_name] = dist.get(pg.field_name, 0) + 1
        print(f"    Field distribution: {dist}")

        return {
            "packs": pack_results,
            "system_resonance": overall,
            "system_sovereign": system_sovereign,
            "field_distribution": dist,
        }

    # ------------------------------------------------------------------
    # Mandala solver integration
    # ------------------------------------------------------------------

    def solve_for_sovereignty(self, max_steps: int = 5000) -> Dict:
        """
        Use the mandala solver to find the configuration with maximum resonance.

        The solver minimizes -resonance, so ground state = sovereignty.
        """
        from mandala_computer import MandalaComputer

        print(f"\n  Solving for sovereignty via mandala annealing...")

        mc = MandalaComputer(golden_depth=4, sacred_geometry=8)
        mc.encode_optimization(SovereignEnergy.as_mandala_cost, len(self.nodes))

        result = mc.simulated_annealing(
            max_steps=max_steps, T_start=3.0, T_end=0.01
        )

        optimal_states = result["solution"]["states"]
        resonance = -result["solution"]["cost"]  # negate back
        sovereign = SovereignEnergy.is_sovereign(resonance, entropy=0.5)

        # Interpret as physical fields
        field_config = [PhysicalGlyph.from_state(s) for s in optimal_states]
        glyph_str = "".join(pg.glyph for pg in field_config)

        print(f"\n    Optimal configuration: {glyph_str}")
        print(f"    Resonance: {resonance:.4f}")
        print(f"    Sovereign: {sovereign}")
        print(f"    Fields: {[pg.field_name for pg in field_config]}")

        return {
            "states": optimal_states,
            "glyphs": glyph_str,
            "resonance": resonance,
            "sovereign": sovereign,
            "fields": [pg.field_name for pg in field_config],
            "energy": result["final_energy"],
        }


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_physical_glyphs():
    """Show the glyph-to-physics mapping."""
    print("=" * 60)
    print("PHYSICAL GLYPHS: Each state IS a field")
    print("=" * 60)

    print("\n  Glyph  State  Physical Field")
    print("  " + "-" * 40)
    for pg in PhysicalGlyph:
        print(f"  {pg.glyph}      {pg.state}      {pg.field_name}")

    # Show some compatibilities
    print("\n  Compatibility (exact fractions):")
    pairs = [(0, 7), (2, 4), (0, 2), (3, 7), (1, 6)]
    for a, b in pairs:
        ga = PhysicalGlyph.from_state(a)
        gb = PhysicalGlyph.from_state(b)
        compat = glyph_compatibility(a, b)
        print(f"    {ga.glyph} ({ga.field_name}) <-> {gb.glyph} ({gb.field_name}): {compat.to_glyphs()}"
              f"  ({compat.num.to_decimal()}/{compat.den.to_decimal()})")


def demo_field_constraints():
    """Show constraint validation."""
    print("\n" + "=" * 60)
    print("FIELD CONSTRAINTS: Physical invariants")
    print("=" * 60)

    # Healthy system
    print("\n  --- Healthy system ---")
    healthy = FieldState(soil_trend=0.1, water_retention=0.7, coupling_strength=0.8)
    print(f"    Health: {FieldConstraints.health_score(healthy):.2f}")
    print(f"    Drift: {FieldConstraints.detect_drift(healthy)}")
    print(f"    Yield: {FieldConstraints.effective_yield(healthy):.4f}")

    # Degraded system
    print("\n  --- Degraded system ---")
    degraded = FieldState(soil_trend=-0.2, water_retention=0.3, disturbance=0.7)
    print(f"    Health: {FieldConstraints.health_score(degraded):.2f}")
    print(f"    Drift: {FieldConstraints.detect_drift(degraded)}")
    thermal = FieldConstraints.thermal_limit(degraded)
    print(f"    Thermal: critical={thermal['critical']}, load={thermal['thermal_load']:.3f}")


def demo_sovereign_agent():
    """Full sovereign agent lifecycle."""
    print("\n" + "=" * 60)
    print("SOVEREIGN AGENT: Bloom -> Validate -> Resonate -> Solve")
    print("=" * 60)

    agent = SovereignAgent(
        seed_id="SHAPE.OCTA",
        home_families=["computation", "resonance"],
        energy_type="harmonic",
    )
    agent.set_resource_budget(compute=300, depth_limit=3)

    # Bloom
    agent.bloom(depth=2)

    # Validate against field constraints
    agent.validate()

    # Find resonance across the expanded space
    agent.find_resonance()

    # Use mandala solver to find optimal configuration
    result = agent.solve_for_sovereignty(max_steps=3000)

    # Compress with everything preserved
    agent.compress()
    print(f"\n  Compressed to seed. Map preserved with {len(agent.compressed_map['nodes'])} nodes.")

    return agent, result


def demo_resonance_energy():
    """Show resonance as mandala energy function."""
    print("\n" + "=" * 60)
    print("RESONANCE ENERGY: Sovereignty as ground state")
    print("=" * 60)

    # Compare random vs optimized configurations
    import numpy as np

    print("\n  Random configurations:")
    for _ in range(5):
        states = [np.random.randint(0, 8) for _ in range(7)]
        cost = SovereignEnergy.as_mandala_cost(states)
        glyphs = "".join(GLYPHS[s] for s in states)
        print(f"    {glyphs}  resonance={-cost:.4f}  sovereign={SovereignEnergy.is_sovereign(-cost)}")

    # All-same (high self-compatibility)
    print("\n  Uniform configurations:")
    for s in range(8):
        states = [s] * 7
        cost = SovereignEnergy.as_mandala_cost(states)
        pg = PhysicalGlyph.from_state(s)
        glyphs = "".join(GLYPHS[s] for _ in range(7))
        print(f"    {glyphs} ({pg.field_name:>15s})  resonance={-cost:.4f}")


if __name__ == "__main__":
    print("=" * 60)
    print("SOVEREIGN INTEGRATION v1.0")
    print("  Physics + Constraints + Resonance")
    print("=" * 60)

    demo_physical_glyphs()
    demo_field_constraints()
    demo_resonance_energy()
    demo_sovereign_agent()

    print("\n" + "=" * 60)
    print("Glyphs are fields. Constraints are physics. Resonance is sovereignty.")
    print("=" * 60)
