"""
RESONATE — Cross-Domain Coupling Engine
========================================
Turns N independent bridge encoders into a coupled dynamical system
where domains influence each other through physically motivated
coupling rules.

Without RESONATE, the mandala is N independent encoders in a wrapper.
With it, it's actual sensor fusion: electric fields couple to magnetic
via induction, sound couples to thermal via equation of state, gravity
couples weakly to everything.

Architecture:
  1. DomainState — current reading from one bridge encoder
  2. CouplingRule — how two domains influence each other
  3. ResonateEngine — runs coupled dynamics, detects cross-domain resonance
  4. Built-in rules for all physically motivated couplings

Usage:
    from src.resonate import ResonateEngine, DomainState

    engine = ResonateEngine()

    # Feed in readings from whatever bridges are available
    engine.set_state("electric", voltage=12.0, current=0.5)
    engine.set_state("magnetic", field_t=0.001)
    engine.set_state("thermal", temperature_c=45.0)
    engine.set_state("sound", frequency_hz=440.0, amplitude=0.8)

    # Run coupled dynamics
    result = engine.resonate(steps=100, dt=0.1)
    print(result.cross_domain_energy)
    print(result.resonance_pairs)
    print(result.dominant_coupling)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


@dataclass
class DomainState:
    """Current state of one bridge domain."""
    name: str
    values: Dict[str, float] = field(default_factory=dict)
    activation: float = 0.0  # 0=dormant, 1=fully active
    timestamp: float = 0.0

    def energy(self) -> float:
        """Scalar energy proxy: L2 norm of all values."""
        if not self.values:
            return 0.0
        return math.sqrt(sum(v * v for v in self.values.values()))

    def get(self, key: str, default: float = 0.0) -> float:
        return self.values.get(key, default)


@dataclass
class CouplingRule:
    """
    Defines how domain A influences domain B.

    The coupling function takes (state_a, state_b) and returns a
    delta dict of {field_name: adjustment} to apply to state_b.
    """
    source: str
    target: str
    weight: float
    bidirectional: bool
    physics_basis: str
    couple_fn: Callable[[DomainState, DomainState], Dict[str, float]]


@dataclass
class ResonanceResult:
    """Output of a RESONATE run."""
    steps_run: int
    cross_domain_energy: float
    per_domain_energy: Dict[str, float]
    resonance_pairs: List[Tuple[str, str, float]]
    dominant_coupling: Optional[Tuple[str, str]]
    energy_history: List[float]
    states: Dict[str, DomainState]
    coupling_matrix: Dict[Tuple[str, str], float]


# ============================================================
# Physics-motivated coupling functions
# ============================================================

def _couple_electric_magnetic(e: DomainState, m: DomainState) -> Dict[str, float]:
    """Faraday/Lenz: changing current induces magnetic field."""
    current = e.get("current", 0.0)
    return {"field_t": current * 1e-3}


def _couple_magnetic_electric(m: DomainState, e: DomainState) -> Dict[str, float]:
    """Faraday: changing magnetic field induces EMF."""
    field = m.get("field_t", 0.0)
    return {"voltage": -field * 0.1}


def _couple_sound_thermal(s: DomainState, t: DomainState) -> Dict[str, float]:
    """Equation of state: acoustic compression heats gas."""
    amplitude = s.get("amplitude", 0.0)
    freq = s.get("frequency_hz", 0.0)
    heating = amplitude * freq * 1e-8
    return {"temperature_c": heating}


def _couple_thermal_sound(t: DomainState, s: DomainState) -> Dict[str, float]:
    """Hot gas changes speed of sound, shifting resonance."""
    temp = t.get("temperature_c", 20.0)
    speed_shift = (temp - 20.0) * 0.6  # ~0.6 m/s per degree C
    return {"speed_of_sound": 343.0 + speed_shift}


def _couple_electric_thermal(e: DomainState, t: DomainState) -> Dict[str, float]:
    """Joule heating: P = I^2 * R."""
    current = e.get("current", 0.0)
    voltage = e.get("voltage", 0.0)
    power = abs(current * voltage)
    return {"temperature_c": power * 0.01}


def _couple_thermal_electric(t: DomainState, e: DomainState) -> Dict[str, float]:
    """Temperature changes resistance (PTC/NTC behavior)."""
    temp = t.get("temperature_c", 20.0)
    resistance_factor = 1.0 + (temp - 20.0) * 0.004  # typical copper PTC
    return {"resistance_factor": resistance_factor}


def _couple_gravity_any(g: DomainState, other: DomainState) -> Dict[str, float]:
    """Gravity couples weakly to everything via potential energy."""
    accel = g.get("acceleration", 0.0)
    return {"gravity_bias": accel * 0.001}


def _couple_electric_chemical(e: DomainState, c: DomainState) -> Dict[str, float]:
    """Electrochemistry: voltage drives ion migration."""
    voltage = e.get("voltage", 0.0)
    return {"reaction_rate_factor": 1.0 + abs(voltage) * 0.1}


def _couple_magnetic_light(m: DomainState, l: DomainState) -> Dict[str, float]:
    """Faraday rotation: magnetic field rotates light polarization."""
    field = m.get("field_t", 0.0)
    return {"polarization_rotation": field * 0.01}


def _couple_pressure_sound(p: DomainState, s: DomainState) -> Dict[str, float]:
    """Pressure changes acoustic impedance."""
    force = p.get("force_n", 0.0)
    return {"impedance_factor": 1.0 + force * 0.001}


def _couple_sound_pressure(s: DomainState, p: DomainState) -> Dict[str, float]:
    """Acoustic radiation pressure."""
    amplitude = s.get("amplitude", 0.0)
    freq = s.get("frequency_hz", 0.0)
    radiation_pressure = amplitude * amplitude * freq * 1e-9
    return {"force_n": radiation_pressure}


# ============================================================
# Default coupling rules
# ============================================================

DEFAULT_RULES = [
    CouplingRule("electric", "magnetic", 0.5, True,
                 "Faraday induction: dI/dt → B, dB/dt → EMF",
                 _couple_electric_magnetic),
    CouplingRule("magnetic", "electric", 0.5, False,
                 "Lenz's law: changing flux induces opposing EMF",
                 _couple_magnetic_electric),
    CouplingRule("sound", "thermal", 0.2, True,
                 "Acoustic compression heats gas (equation of state)",
                 _couple_sound_thermal),
    CouplingRule("thermal", "sound", 0.2, False,
                 "Temperature shifts speed of sound",
                 _couple_thermal_sound),
    CouplingRule("electric", "thermal", 0.3, True,
                 "Joule heating: P = IV",
                 _couple_electric_thermal),
    CouplingRule("thermal", "electric", 0.15, False,
                 "PTC/NTC resistance change with temperature",
                 _couple_thermal_electric),
    CouplingRule("gravity", "electric", 0.05, False,
                 "Gravitational potential bias (weak universal coupling)",
                 _couple_gravity_any),
    CouplingRule("gravity", "magnetic", 0.05, False,
                 "Gravitational potential bias (weak universal coupling)",
                 _couple_gravity_any),
    CouplingRule("gravity", "thermal", 0.05, False,
                 "Gravitational potential bias (weak universal coupling)",
                 _couple_gravity_any),
    CouplingRule("gravity", "sound", 0.05, False,
                 "Gravitational potential bias (weak universal coupling)",
                 _couple_gravity_any),
    CouplingRule("electric", "chemical", 0.25, False,
                 "Electrochemistry: voltage drives ion transport",
                 _couple_electric_chemical),
    CouplingRule("magnetic", "light", 0.1, False,
                 "Faraday rotation of polarization",
                 _couple_magnetic_light),
    CouplingRule("pressure", "sound", 0.3, True,
                 "Pressure modifies acoustic impedance",
                 _couple_pressure_sound),
    CouplingRule("sound", "pressure", 0.15, False,
                 "Acoustic radiation pressure",
                 _couple_sound_pressure),
]


# ============================================================
# RESONATE engine
# ============================================================

class ResonateEngine:
    """
    Cross-domain coupling engine.

    Runs coupled dynamics across bridge domains so that electric
    fields influence magnetic, sound influences thermal, etc.
    Produces a resonance map showing which domain pairs are
    strongly coupled in the current configuration.
    """

    def __init__(self, rules: Optional[List[CouplingRule]] = None):
        self._states: Dict[str, DomainState] = {}
        self._rules = list(rules or DEFAULT_RULES)
        self._active_rules: List[CouplingRule] = []

    def set_state(self, domain: str, **kwargs):
        """Set or update a domain's state from sensor readings."""
        if domain not in self._states:
            self._states[domain] = DomainState(name=domain)
        state = self._states[domain]
        state.values.update(kwargs)
        state.activation = 1.0
        self._rebuild_active_rules()

    def add_rule(self, rule: CouplingRule):
        """Add a custom coupling rule."""
        self._rules.append(rule)
        self._rebuild_active_rules()

    def active_domains(self) -> List[str]:
        """Domains that have been set."""
        return sorted(self._states.keys())

    def active_couplings(self) -> List[Tuple[str, str, str]]:
        """Active coupling pairs with physics basis."""
        return [(r.source, r.target, r.physics_basis)
                for r in self._active_rules]

    def _rebuild_active_rules(self):
        """Filter rules to only those connecting active domains."""
        active = set(self._states.keys())
        self._active_rules = [
            r for r in self._rules
            if r.source in active and r.target in active
        ]

    def resonate(self, steps: int = 50, dt: float = 0.1,
                 damping: float = 0.95) -> ResonanceResult:
        """
        Run coupled dynamics for N steps.

        Each step:
          1. For each active coupling rule, compute influence
          2. Apply weighted deltas to target domain states
          3. Apply damping (prevents runaway)
          4. Record total cross-domain energy

        Returns ResonanceResult with energy history, resonance pairs,
        and the final coupled state.
        """
        energy_history = []
        coupling_energy: Dict[Tuple[str, str], float] = {}

        for step in range(steps):
            deltas: Dict[str, Dict[str, float]] = {
                d: {} for d in self._states
            }

            for rule in self._active_rules:
                src = self._states[rule.source]
                tgt = self._states[rule.target]

                influence = rule.couple_fn(src, tgt)
                pair_energy = 0.0

                for field_name, delta_val in influence.items():
                    weighted = delta_val * rule.weight * dt
                    deltas[rule.target][field_name] = (
                        deltas[rule.target].get(field_name, 0.0) + weighted
                    )
                    pair_energy += abs(weighted)

                pair_key = (rule.source, rule.target)
                coupling_energy[pair_key] = (
                    coupling_energy.get(pair_key, 0.0) + pair_energy
                )

            # Apply deltas with damping
            for domain, delta_dict in deltas.items():
                state = self._states[domain]
                for k, v in delta_dict.items():
                    old = state.values.get(k, 0.0)
                    state.values[k] = (old + v) * damping

            total_e = sum(s.energy() for s in self._states.values())
            energy_history.append(total_e)

        # Build resonance pairs sorted by coupling strength
        resonance_pairs = sorted(
            [(s, t, e) for (s, t), e in coupling_energy.items()],
            key=lambda x: -x[2],
        )

        dominant = (resonance_pairs[0][0], resonance_pairs[0][1]) if resonance_pairs else None

        per_domain = {name: s.energy() for name, s in self._states.items()}
        total_cross = sum(coupling_energy.values())

        return ResonanceResult(
            steps_run=steps,
            cross_domain_energy=total_cross,
            per_domain_energy=per_domain,
            resonance_pairs=resonance_pairs,
            dominant_coupling=dominant,
            energy_history=energy_history,
            states=dict(self._states),
            coupling_matrix=coupling_energy,
        )

    def resonance_report(self, result: ResonanceResult) -> str:
        """Human-readable resonance report."""
        lines = [
            "RESONATE Cross-Domain Coupling Report",
            "=" * 50,
            f"Active domains: {', '.join(self.active_domains())}",
            f"Active couplings: {len(self._active_rules)}",
            f"Steps: {result.steps_run}",
            f"Total cross-domain energy: {result.cross_domain_energy:.6f}",
            "",
            "Per-domain energy:",
        ]
        for name, e in sorted(result.per_domain_energy.items()):
            lines.append(f"  {name}: {e:.6f}")

        if result.resonance_pairs:
            lines.append("")
            lines.append("Coupling strengths (descending):")
            for src, tgt, e in result.resonance_pairs[:10]:
                lines.append(f"  {src} -> {tgt}: {e:.6f}")

        if result.dominant_coupling:
            lines.append(f"\nDominant coupling: "
                         f"{result.dominant_coupling[0]} <-> "
                         f"{result.dominant_coupling[1]}")

        return "\n".join(lines)


# ============================================================
# G2B alternative compute integration
# ============================================================

def _try_import_gravity_alt():
    """Try to import gravity alternative compute from G2B."""
    try:
        from bridges.gravity_alternative_compute import (
            classify_gravity_ternary,
            TernaryGravityState,
        )
        return classify_gravity_ternary, TernaryGravityState
    except ImportError:
        return None, None


def _try_import_electric_alt():
    """Try to import electric alternative compute from G2B."""
    try:
        from bridges.electric_alternative_compute import (
            classify_charge_ternary,
            classify_current_ternary,
            TernaryChargeState,
            TernaryCurrentState,
        )
        return classify_charge_ternary, classify_current_ternary
    except ImportError:
        return None, None


def _try_import_sound_alt():
    """Try to import sound alternative compute from G2B."""
    try:
        from bridges.sound_alternative_compute import (
            classify_phase_ternary,
            TernaryPhaseState,
        )
        return classify_phase_ternary, TernaryPhaseState
    except ImportError:
        return None, None


class DomainIntersectionRule:
    """
    A rule that uses real G2B alternative compute modules to
    classify domain states before coupling. Replaces toy projectors
    with actual physics.
    """

    def __init__(self):
        self._gravity_classify, self._GravState = _try_import_gravity_alt()
        self._charge_classify, self._current_classify = _try_import_electric_alt()
        self._phase_classify, self._PhaseState = _try_import_sound_alt()

    @property
    def gravity_available(self) -> bool:
        return self._gravity_classify is not None

    @property
    def electric_available(self) -> bool:
        return self._charge_classify is not None

    @property
    def sound_available(self) -> bool:
        return self._phase_classify is not None

    def classify_gravity(self, accel_vector: List[float],
                         mass_positions: Optional[List] = None) -> Dict:
        """Classify gravitational state using real ternary physics."""
        if not self.gravity_available:
            mag = math.sqrt(sum(x * x for x in accel_vector))
            return {"state": "attract" if mag > 0.01 else "null",
                    "magnitude": mag, "source": "fallback"}
        state = self._gravity_classify(accel_vector, mass_positions)
        return {
            "state": state.name.lower(),
            "value": int(state),
            "symbol": state.symbol,
            "meaning": state.physical_meaning,
            "source": "g2b_alternative_compute",
        }

    def classify_electric(self, charge: float = 0.0,
                          current: float = 0.0) -> Dict:
        """Classify electrical state using real ternary physics."""
        if not self.electric_available:
            return {"charge_state": "positive" if charge > 0 else "negative",
                    "current_state": "forward" if current > 0 else "reverse",
                    "source": "fallback"}
        c_state = self._charge_classify(charge)
        i_state = self._current_classify(current)
        return {
            "charge_state": c_state.name.lower(),
            "charge_value": int(c_state),
            "current_state": i_state.name.lower(),
            "current_value": int(i_state),
            "source": "g2b_alternative_compute",
        }

    def classify_sound(self, phase_radians: float) -> Dict:
        """Classify acoustic phase using real ternary physics."""
        if not self.sound_available:
            return {"state": "compression" if phase_radians < math.pi else "rarefaction",
                    "source": "fallback"}
        state = self._phase_classify(phase_radians)
        return {
            "state": state.name.lower(),
            "value": int(state),
            "source": "g2b_alternative_compute",
        }

    def summary(self) -> str:
        g = "LIVE" if self.gravity_available else "fallback"
        e = "LIVE" if self.electric_available else "fallback"
        s = "LIVE" if self.sound_available else "fallback"
        return f"DomainIntersectionRule(gravity={g}, electric={e}, sound={s})"


# ============================================================
# Demo
# ============================================================

if __name__ == "__main__":
    engine = ResonateEngine()

    engine.set_state("electric", voltage=12.0, current=0.5)
    engine.set_state("magnetic", field_t=0.001)
    engine.set_state("thermal", temperature_c=45.0)
    engine.set_state("sound", frequency_hz=440.0, amplitude=0.8)
    engine.set_state("gravity", acceleration=9.81)
    engine.set_state("pressure", force_n=101325.0)

    print(f"Active domains: {engine.active_domains()}")
    print(f"Active couplings: {len(engine.active_couplings())}")
    for s, t, basis in engine.active_couplings():
        print(f"  {s} -> {t}: {basis}")

    result = engine.resonate(steps=100, dt=0.1)
    print()
    print(engine.resonance_report(result))
