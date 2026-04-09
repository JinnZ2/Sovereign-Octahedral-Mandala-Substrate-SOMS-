"""
Thermodynamic Accountability Framework
=======================================
Treats every economic activity as a thermodynamic process and audits
whether it creates or destroys systemic value — not by money, but by
exergy accounting.

Core idea: Money is a low-fidelity signal. A corporation that generates
$100M while destroying soil, water tables, and volunteer networks is
thermodynamically net-negative. This framework detects those "heat leaks"
by weighting impacts according to systemic irreplaceability.

Components:
  ThermodynamicHierarchy — weighted impact scoring (Magnetic Core=1.0, Money=0.01)
  EnvironmentalAuditor   — exergy-based extraction vs. baseline comparison
  SovereignAuditor       — maps work contributions regardless of money signal
  InvariantAuditor       — knowledge base of hidden prerequisites
  DeepAncestryAuditor    — recursive dependency tracing to physical foundation
  find_heat_leaks()      — graph-based detection of unaccounted costs
  invariant_audit()      — automated hidden-variable check

Physics basis:
  - Transformity (Odum): each layer represents accumulated work from prior layers
  - Trophic efficiency (Lindeman): energy is lost at every transfer level
  - Exergy accounting: not all joules are equal — structured energy > waste heat

Extracted from: Notes.md lines 4610-4924
"""

from typing import Dict, List, Optional, Set

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


# ============================================================
# Thermodynamic Hierarchy
# ============================================================

class ThermodynamicHierarchy:
    """
    Weights activities by the irreplaceability of the systems they affect.

    The hierarchy (from Odum's transformity concept):
      Magnetic Core  (1.00) — lose this, lose the atmosphere
      Sunlight       (0.95) — primary energy input
      Earth/Rock     (0.90) — mineral substrate
      Photosynthesis (0.85) — primary exergy converter
      Microbiome     (0.80) — soil integrity maintenance
      Community Labor(0.70) — system maintenance (volunteers, etc.)
      Money/Currency (0.01) — high-entropy proxy signal

    An activity that shows +100 in Money but -10 in Photosynthesis
    scores: 0.01*100 + 0.85*(-10) = 1.0 - 8.5 = -7.5 (net destruction).
    """

    DEFAULT_WEIGHTS = {
        "Magnetic Core": 1.00,
        "Sunlight": 0.95,
        "Earth/Rock": 0.90,
        "Photosynthesis": 0.85,
        "Microbiome": 0.80,
        "Community Labor": 0.70,
        "Mentorship": 0.60,
        "Money/Currency": 0.01,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def calculate_true_value(self, activity_map: Dict[str, float]) -> Dict:
        """
        activity_map: {layer_name: impact_factor}
          +N = maintenance/creation, -N = extraction/destruction

        Returns dict with net_value, breakdown, and verdict.
        """
        breakdown = {}
        net_value = 0.0
        for layer, impact in activity_map.items():
            weight = self.weights.get(layer, 0.0)
            weighted = weight * impact
            breakdown[layer] = {
                "raw_impact": impact,
                "weight": weight,
                "weighted_impact": weighted,
            }
            net_value += weighted

        verdict = ("SYSTEMIC DEBT: Extracting from the foundation."
                   if net_value < 0
                   else f"Net Sovereign Value: {net_value:.2f}")

        return {
            "net_value": net_value,
            "breakdown": breakdown,
            "verdict": verdict,
        }


# ============================================================
# Environmental Auditor
# ============================================================

class EnvironmentalAuditor:
    """
    Exergy-based audit: compares an activity's extraction against
    a baseline ecosystem state.
    """

    def __init__(self, location: str = "default",
                 baseline_exergy: float = 1000.0,
                 stored_emergy: Optional[Dict[str, float]] = None):
        self.location = location
        self.baseline_exergy = baseline_exergy
        self.stored_emergy = stored_emergy or {
            "soil": 500.0,
            "water": 300.0,
            "biodiversity": 200.0,
        }

    def simulate_extraction(self, activity: str,
                            heat_leak: float = 150.0,
                            soil_drain_pct: float = 0.2) -> Dict:
        """
        Simulate an extraction activity and return net thermodynamic yield.
        """
        resource_drain = self.stored_emergy["soil"] * soil_drain_pct
        current_utility = (self.baseline_exergy - heat_leak) - resource_drain

        return {
            "activity": activity,
            "baseline_exergy": self.baseline_exergy,
            "heat_leak": heat_leak,
            "resource_drain": resource_drain,
            "net_utility": current_utility,
            "verdict": ("PARASITIC LOAD: Entropy increasing"
                        if current_utility < 0
                        else "Within sustainable envelope"),
        }


# ============================================================
# Sovereign Auditor
# ============================================================

class SovereignAuditor:
    """
    Maps work contributions regardless of money signal.
    Uses a directed graph to track who provides what exergy.
    """

    def __init__(self):
        if not HAS_NETWORKX:
            self._nodes: Dict[str, Dict] = {}
        else:
            self.system_map = nx.DiGraph()

    def map_work_contribution(self, entity: str, work_type: str,
                              exergy_output: float):
        if HAS_NETWORKX:
            self.system_map.add_node(
                entity, type=work_type, output=exergy_output)
        else:
            self._nodes[entity] = {
                "type": work_type, "output": exergy_output}

    def identify_unaccounted_inputs(self, entity: str,
                                    prerequisites: Optional[List[str]] = None
                                    ) -> Dict:
        """
        Check what 'invisible workers' an entity depends on but
        doesn't account for.
        """
        prereqs = prerequisites or [
            "Old Growth Forest",
            "Volunteer Fire Dept",
            "Soil Microbiome",
            "Clean Water",
        ]
        total_unpaid = 0.0

        if HAS_NETWORKX:
            registered = set(self.system_map.nodes())
        else:
            registered = set(self._nodes.keys())

        unaccounted = [p for p in prereqs if p not in registered]
        total_unpaid = len(unaccounted) * 100.0  # symbolic exergy units

        return {
            "entity": entity,
            "unaccounted_inputs": unaccounted,
            "unpaid_exergy_units": total_unpaid,
        }


# ============================================================
# Invariant Auditor
# ============================================================

class InvariantAuditor:
    """
    Knowledge base of hidden prerequisites. Given a claimed action,
    traces back to find which foundational inputs are unaccounted.
    """

    DEFAULT_KB = {
        "Infrastructure": [
            "Volunteer Fire", "Road Maintenance", "Stable Soil"],
        "Biological Survival": [
            "Clean Water", "Photosynthesis (Trees)", "Microbiome"],
        "Social Cohesion": [
            "Unpaid Care Work", "Elder Care", "Mentorship"],
    }

    def __init__(self, knowledge_base: Optional[Dict] = None):
        self.kb = knowledge_base or self.DEFAULT_KB.copy()

    def trace_ancestry(self, claim: str) -> List[str]:
        """Find all hidden prerequisites the claim depends on."""
        found = []
        for category, prereqs in self.kb.items():
            found.extend(prereqs)
        return found

    def audit(self, action_data: Dict) -> str:
        """
        Check if an action accounts for foundational inputs.
        action_data must have 'accounted_inputs' key.
        """
        foundation = [
            "Magnetic Core", "Sunlight", "Rock", "Water", "Insects"]
        accounted = action_data.get("accounted_inputs", [])

        for layer in foundation:
            if layer not in accounted:
                return (f"HEAT LEAK: Action ignores '{layer}'. "
                        f"Net value claim is incomplete.")
        return "Sovereign Value Verified."


# ============================================================
# Deep Ancestry Auditor
# ============================================================

class DeepAncestryAuditor:
    """
    Recursive dependency tracing. Given a project's impacts,
    traces all the way down to foundational physical layers
    to reveal total systemic exposure.
    """

    DEFAULT_STACK = {
        "Human Project": ["Community Resilience", "Animals"],
        "Community Resilience": ["Water", "Air", "Food"],
        "Animals": ["Insects", "Plants", "Water"],
        "Insects": ["Soil Microbiome", "Plants"],
        "Plants": ["Sunlight", "Water", "Soil Microbiome"],
        "Soil Microbiome": ["Rock", "Water"],
        "Water": ["Atmosphere", "Magnetic Core"],
    }

    def __init__(self, stack: Optional[Dict] = None):
        self.stack = stack or self.DEFAULT_STACK.copy()

    def _trace_to_foundation(self, layer: str,
                             visited: Optional[Set] = None) -> List[str]:
        if visited is None:
            visited = set()
        if layer in visited:
            return []
        visited.add(layer)
        ancestors = [layer]
        if layer in self.stack:
            for parent in self.stack[layer]:
                ancestors.extend(self._trace_to_foundation(parent, visited))
        return ancestors

    def run_root_cause_analysis(self, project_name: str,
                                impacts: List[str]) -> Dict:
        """
        impacts: list of layers the project disrupts.
        Returns all foundational layers affected.
        """
        destroyed = set()
        for item in impacts:
            path = self._trace_to_foundation(item)
            destroyed.update(path)

        return {
            "project": project_name,
            "direct_impacts": impacts,
            "total_layers_affected": len(destroyed),
            "affected_layers": sorted(destroyed),
        }


# ============================================================
# Graph-based heat leak detection
# ============================================================

def find_heat_leaks(required_ancestors: List[str],
                    actual_ancestors: List[str],
                    hidden_vars: Optional[List[str]] = None) -> List[str]:
    """
    Find foundational inputs that a system depends on but doesn't credit.
    """
    hidden = hidden_vars or [
        "Clean Water", "Volunteer Labor", "Soil Integrity",
        "Pollinator Habitat", "Atmospheric Stability",
    ]
    actual_set = set(actual_ancestors)
    return [v for v in hidden if v not in actual_set]


# ============================================================
# Demo
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("THERMODYNAMIC AUDIT DEMO")
    print("=" * 60)

    # --- Hierarchy audit ---
    print("\n--- ThermodynamicHierarchy ---")
    hierarchy = ThermodynamicHierarchy()

    retreat_impact = {
        "Money/Currency": 100,
        "Earth/Rock": -10,
        "Photosynthesis": -15,
        "Community Labor": -5,
    }
    result = hierarchy.calculate_true_value(retreat_impact)
    print(f"Activity: Luxury Development")
    print(f"  Money signal: +100")
    print(f"  Thermodynamic value: {result['net_value']:.2f}")
    print(f"  Verdict: {result['verdict']}")

    # Show why: money is almost worthless in the weighting
    print("\n  Breakdown:")
    for layer, detail in result["breakdown"].items():
        print(f"    {layer}: {detail['raw_impact']:+.0f} "
              f"x {detail['weight']:.2f} = {detail['weighted_impact']:+.2f}")

    # --- Environmental audit ---
    print("\n--- EnvironmentalAuditor ---")
    env = EnvironmentalAuditor(location="Northern MN")
    extraction = env.simulate_extraction("Hunting Retreat",
                                         heat_leak=150, soil_drain_pct=0.3)
    print(f"  Net utility: {extraction['net_utility']:.1f}")
    print(f"  Verdict: {extraction['verdict']}")

    # --- Deep ancestry ---
    print("\n--- DeepAncestryAuditor ---")
    deep = DeepAncestryAuditor()
    analysis = deep.run_root_cause_analysis(
        "Luxury Hunting Retreat",
        impacts=["Plants", "Insects"],
    )
    print(f"  Direct impacts: {analysis['direct_impacts']}")
    print(f"  Total layers affected: {analysis['total_layers_affected']}")
    print(f"  Full chain: {analysis['affected_layers']}")

    # --- Invariant audit ---
    print("\n--- InvariantAuditor ---")
    inv = InvariantAuditor()
    # A project that only accounts for money
    check = inv.audit({"accounted_inputs": ["Money", "Jobs"]})
    print(f"  Audit (money-only project): {check}")
    # A project that accounts for everything
    check2 = inv.audit({"accounted_inputs": [
        "Magnetic Core", "Sunlight", "Rock", "Water", "Insects",
        "Community Labor"]})
    print(f"  Audit (full accounting):    {check2}")

    # --- Heat leak detection ---
    print("\n--- Heat Leak Detection ---")
    leaks = find_heat_leaks(
        required_ancestors=["Sunlight", "Water", "Soil"],
        actual_ancestors=["Money", "Jobs", "Tax Revenue"],
    )
    print(f"  Unaccounted inputs: {leaks}")

    print("\n" + "=" * 60)
    print("INTERPRETATION:")
    print("  When thermodynamic weights replace money-as-proxy,")
    print("  activities that look profitable become visibly")
    print("  destructive. The framework makes entropy export")
    print("  measurable, not just intuitive.")
    print("=" * 60)
