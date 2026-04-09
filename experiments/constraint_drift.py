"""
Constraint Drift Detection Framework
=====================================
Detects when the meaning of a term has silently changed over time
by tracking which constraints were present historically versus now.

Core idea: A term like "sustainable farming" in 1985 carried implicit
constraints (local seed saving, soil health maintenance, community
continuity) that have been dropped by 2024 usage. This framework
makes that constraint loss visible and measurable.

Components:
  VectorTerm         — term as a point in [energy, physical, resonance] space
  TermConstraint     — constraint profiling with 4-axis scoring
  ConstraintVector   — temporal assumption tracking with drift computation
  ConstraintRegistry — historical constraint storage and audit
  align_terms_over_time()  — detect drift across time periods
  propagate_risk()         — cascading failure analysis
  detect_drift()           — measure constraint loss between eras
  bridge_constraints()     — test if modern term can claim continuity
  cascade_path()           — trace chain of failures from a seed term

Extracted from: Notes.md lines 2123-3062, 4549-4594
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Set


# ============================================================
# Core data structures
# ============================================================

class VectorTerm:
    """
    A term (concept, policy, practice) represented as a vector in
    constraint space: [energy, physical, resonance].

    - energy:    thermodynamic work content (0=none, 1=maximum)
    - physical:  material/system integrity (0=degraded, 1=intact)
    - resonance: alignment with surrounding constraints (0=mismatch, 1=coupled)
    """

    def __init__(self, term: str, year: int):
        self.term = term
        self.year = year
        self.vector = np.zeros(3)
        self.constraints: List = []
        self.time_stamp: Optional[float] = None
        self.risk_links: Dict = {}  # {related_term: risk_factor}
        self.decay_rate: float = 0.0
        self.last_updated: Optional[int] = None

    def set_vector(self, energy: float = 0.0, physical: float = 0.0,
                   resonance: float = 0.0):
        self.vector = np.array([energy, physical, resonance])
        self.last_updated = self.year

    @property
    def energy(self) -> float:
        return self.vector[0]

    @property
    def physical(self) -> float:
        return self.vector[1]

    @property
    def resonance(self) -> float:
        return self.vector[2]

    def add_constraint(self, constraint):
        """Add a constraint tuple, e.g. ("soil_health", 0.7, "min")."""
        self.constraints.append(constraint)

    def register_risk(self, related_term: 'VectorTerm', factor: float):
        self.risk_links[related_term] = factor

    def net_risk(self) -> float:
        return sum(self.risk_links.values())

    def resonance_distance(self, other: 'VectorTerm') -> float:
        """Euclidean distance in constraint space."""
        return float(np.linalg.norm(self.vector - other.vector))

    def apply_decay(self, years: float):
        """Model internal degradation over time even without external change."""
        self.vector = self.vector * (1 - self.decay_rate * years)

    def validate(self, tolerance: float = 0.1) -> bool:
        """Return True if current vector satisfies all registered constraints."""
        for constraint in self.constraints:
            if len(constraint) >= 3:
                dim_name, threshold, direction = constraint[0], constraint[1], constraint[2]
                dim_map = {"energy": 0, "physical": 1, "resonance": 2}
                if dim_name in dim_map:
                    idx = dim_map[dim_name]
                    if direction == "min" and self.vector[idx] < threshold - tolerance:
                        return False
                    if direction == "max" and self.vector[idx] > threshold + tolerance:
                        return False
        return True

    def historical_continuity(self, earlier: 'VectorTerm',
                              tolerance: float = 0.2) -> Tuple[bool, str]:
        """Can self legitimately claim continuity with earlier_term?"""
        missing = [c for c in earlier.constraints if c not in self.constraints]
        if missing:
            return False, f"Missing {len(missing)} constraints: {missing}"
        drift = self.resonance_distance(earlier)
        if drift > tolerance:
            return False, f"Vector drift {drift:.3f} exceeds tolerance {tolerance}"
        return True, "Continuity verified"


class TermConstraint:
    """
    Constraint profiling: measures how well-defined a term is
    across 4 axes. Score 0 = unconstrained, 1 = fully constrained.
    """

    def __init__(self, term: str, year: int):
        self.term = term
        self.year = year
        self.has_measurable_inputs: bool = False
        self.has_measurable_outputs: bool = False
        self.has_physical_invariant: bool = False
        self.has_bounded_antonym: bool = False
        self.missing_constraints: List[str] = []

    def score(self) -> float:
        return sum([
            self.has_measurable_inputs,
            self.has_measurable_outputs,
            self.has_physical_invariant,
            self.has_bounded_antonym,
        ]) / 4.0


class ConstraintVector:
    """
    Tracks a term's assumptions across years and computes drift
    as proportion of lost assumptions versus a baseline year.
    """

    def __init__(self, term: str):
        self.term = term
        self.energetic: float = 0.0
        self.physical: float = 0.0
        self.assumptions: Dict[int, List[str]] = {}
        self.drift: Dict[int, float] = {}

    def add_year(self, year: int, energetic: float, physical: float,
                 assumptions: List[str]):
        self.energetic = energetic
        self.physical = physical
        self.assumptions[year] = assumptions

    def compute_drift(self, baseline_year: int):
        """Drift = proportion of baseline assumptions missing in each year."""
        base = set(self.assumptions.get(baseline_year, []))
        for year, assumptions in self.assumptions.items():
            lost = base - set(assumptions)
            self.drift[year] = len(lost) / max(1, len(base))


class ConstraintRegistry:
    """Central registry for historical constraints by term and year."""

    def __init__(self):
        self.constraints: Dict[str, List[Tuple]] = {}

    def register(self, term: str, constraint: str, threshold: float,
                 year: int):
        self.constraints.setdefault(term, []).append(
            (constraint, threshold, year))

    def audit(self, term: str, current_vector: VectorTerm,
              year: int) -> List[str]:
        """Return constraints violated by current_vector up to year."""
        violations = []
        for c_name, threshold, c_year in self.constraints.get(term, []):
            if c_year <= year:
                # Simple check: if the constraint name matches a known
                # dimension, verify threshold
                dim_map = {"energy": 0, "physical": 1, "resonance": 2}
                if c_name in dim_map:
                    if current_vector.vector[dim_map[c_name]] < threshold:
                        violations.append(c_name)
        return violations


# ============================================================
# Analysis functions
# ============================================================

def align_terms_over_time(terms: List[VectorTerm]) -> List[Dict]:
    """
    Sort terms by time_stamp and compute vector drift between
    consecutive entries. Returns list of drift records.
    """
    terms_sorted = sorted(
        [t for t in terms if t.time_stamp is not None],
        key=lambda x: x.time_stamp,
    )
    drift_map = []
    for i in range(1, len(terms_sorted)):
        drift_vector = terms_sorted[i].vector - terms_sorted[i - 1].vector
        drift_map.append({
            "from": terms_sorted[i - 1].term,
            "to": terms_sorted[i].term,
            "year_from": terms_sorted[i - 1].year,
            "year_to": terms_sorted[i].year,
            "drift_vector": drift_vector,
            "drift_magnitude": float(np.linalg.norm(drift_vector)),
        })
    return drift_map


def propagate_risk(terms: List[VectorTerm],
                   threshold: float = 0.5) -> List[str]:
    """
    Cascade risk: if a term's risk * vector magnitude exceeds threshold,
    propagate to linked terms. Returns names of all affected terms.
    """
    affected: Set[str] = set()
    for t in terms:
        risk_score = t.net_risk() * float(np.linalg.norm(t.vector))
        if risk_score > threshold:
            affected.add(t.term)
            for linked, factor in t.risk_links.items():
                if factor * risk_score > threshold:
                    affected.add(linked.term)
    return sorted(affected)


def detect_drift(term: str, meaning_old: VectorTerm,
                 meaning_new: VectorTerm) -> Dict:
    """
    Measure constraint loss between two eras of the same term.
    Returns lost constraints and a net drift score (0=no loss, 1=total loss).
    """
    lost = [c for c in meaning_old.constraints
            if c not in meaning_new.constraints]
    gained = [c for c in meaning_new.constraints
              if c not in meaning_old.constraints]
    n_old = max(1, len(meaning_old.constraints))
    return {
        "term": term,
        "constraint_loss": lost,
        "constraint_gain": gained,
        "net_drift_score": len(lost) / n_old,
        "vector_shift": meaning_new.vector - meaning_old.vector,
    }


def bridge_constraints(term_old: VectorTerm, term_new: VectorTerm,
                       tolerance: float = 0.3) -> Tuple[bool, Dict]:
    """
    Can the new-era term legitimately claim continuity with the old-era term?
    Tests both vector drift and constraint overlap.
    """
    drift = term_old.resonance_distance(term_new)
    missing = [c for c in term_old.constraints
               if c not in term_new.constraints]
    is_continuous = (drift < tolerance) and (len(missing) == 0)
    return is_continuous, {
        "drift_magnitude": drift,
        "missing_constraints": missing,
        "vector_shift": term_new.vector - term_old.vector,
    }


def cascade_path(seed_term: VectorTerm, max_depth: int = 5) -> List[str]:
    """
    Trace chain of failure from a seed term through its risk links.
    Returns ordered list of affected term names.
    """
    visited: Set[str] = set()
    chain: List[str] = []

    def traverse(current: VectorTerm, depth: int):
        if depth > max_depth or current.term in visited:
            return
        visited.add(current.term)
        chain.append(current.term)
        for linked, factor in current.risk_links.items():
            if factor > 0.3:
                traverse(linked, depth + 1)

    traverse(seed_term, 0)
    return chain


def audit_dataset(dataset_name: str, terms: Dict[str, VectorTerm],
                  required: Dict[str, List]) -> Dict:
    """
    Quality-control gate: check if a dataset's terms include
    all required constraints.
    """
    report = {
        "dataset": dataset_name,
        "passed": True,
        "violations": [],
    }
    for term_name, reqs in required.items():
        if term_name in terms:
            for req in reqs:
                if req not in terms[term_name].constraints:
                    report["violations"].append(f"{term_name} missing {req}")
                    report["passed"] = False
    return report


# ============================================================
# Demo: "Sustainable Farming" 1985 vs 2024
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CONSTRAINT DRIFT DEMO: Sustainable Farming")
    print("=" * 60)

    # --- 1985 definition ---
    farm_1985 = VectorTerm("sustainable_farming", 1985)
    farm_1985.set_vector(energy=0.3, physical=0.9, resonance=0.8)
    farm_1985.time_stamp = 1985
    farm_1985.add_constraint(("soil_health", 0.7, "min"))
    farm_1985.add_constraint(("local_seed_saving", True, "required"))
    farm_1985.add_constraint(("community_continuity", True, "required"))
    farm_1985.add_constraint(("on_farm_pollination", True, "required"))
    farm_1985.add_constraint(("energy_self_sufficiency", 0.6, "min"))

    # --- 2024 definition ---
    farm_2024 = VectorTerm("sustainable_farming", 2024)
    farm_2024.set_vector(energy=0.8, physical=0.5, resonance=0.3)
    farm_2024.time_stamp = 2024
    farm_2024.add_constraint(("soil_health", 0.4, "min"))
    farm_2024.add_constraint(("purchased_pollination", True, "required"))
    # Note: 3 constraints from 1985 are missing

    # --- Drift detection ---
    drift = detect_drift("sustainable_farming", farm_1985, farm_2024)
    print(f"\nDrift score: {drift['net_drift_score']:.0%}")
    print(f"Lost constraints: {drift['constraint_loss']}")
    print(f"Vector shift: {drift['vector_shift']}")

    # --- Continuity test ---
    is_cont, report = bridge_constraints(farm_1985, farm_2024)
    print(f"\nCan 2024 claim continuity with 1985? {is_cont}")
    print(f"Drift magnitude: {report['drift_magnitude']:.3f}")
    print(f"Missing: {report['missing_constraints']}")

    # --- Constraint profiling ---
    print("\n--- Constraint Profiling ---")
    profile_2024 = TermConstraint("sustainable", 2024)
    profile_2024.has_measurable_inputs = True
    profile_2024.has_measurable_outputs = False
    profile_2024.has_physical_invariant = False
    profile_2024.has_bounded_antonym = False
    profile_2024.missing_constraints = [
        "regeneration_rate >= depletion_rate",
        "community_business_continuity",
    ]
    print(f"Constraint score: {profile_2024.score():.2f} (0=unconstrained, 1=fully)")
    print(f"Missing: {profile_2024.missing_constraints}")

    # --- Temporal drift via ConstraintVector ---
    print("\n--- Temporal Assumption Tracking ---")
    cv = ConstraintVector("sustainable")
    cv.add_year(1985, energetic=0.9, physical=0.95, assumptions=[
        "self-sufficient energy",
        "local soil health maintained",
        "no external pollination needed",
    ])
    cv.add_year(2024, energetic=0.8, physical=0.7, assumptions=[
        "external pollination purchased",
        "industrial soil amendments",
    ])
    cv.compute_drift(baseline_year=1985)
    print(f"Drift by year: {cv.drift}")

    # --- Risk cascade ---
    print("\n--- Risk Cascade ---")
    soil = VectorTerm("soil_health", 2024)
    soil.set_vector(energy=0.2, physical=0.4, resonance=0.3)

    pollinators = VectorTerm("pollinator_habitat", 2024)
    pollinators.set_vector(energy=0.1, physical=0.3, resonance=0.2)

    farm_2024.register_risk(soil, 0.8)
    farm_2024.register_risk(pollinators, 0.6)
    soil.register_risk(pollinators, 0.5)

    chain = cascade_path(farm_2024)
    print(f"Failure chain from sustainable_farming: {chain}")

    affected = propagate_risk([farm_2024, soil, pollinators], threshold=0.1)
    print(f"Affected terms: {affected}")

    print("\n" + "=" * 60)
    print("INTERPRETATION:")
    print("  A drift score of 0.80 means 80% of original constraints")
    print("  have been dropped. The 2024 term is using the same word")
    print("  but has lost most of its original meaning.")
    print("=" * 60)
