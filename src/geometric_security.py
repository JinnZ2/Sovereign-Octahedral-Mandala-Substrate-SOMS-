"""
Geometric Security — Self-encoded integrity for octahedral crystalline computing.

Six verification layers grown from the geometry itself:

  Layer 1: Tetrahedral Parity      — every 4-node cluster sums to expected parity
  Layer 2: Phi-Spacing Constraint  — radii follow r_n = r0 * phi^n within tolerance
  Layer 3: Trace Invariant         — tensor eigenvalues sum to 1 (lambda_1+lambda_2+lambda_3=1)
  Layer 4: Stochastic Resonance    — noise level within optimal SR peak band
  Layer 5: Bridge Authentication   — bridge targets match impedance signatures
  Layer 6: Temporal Handshake      — phi-spaced timing sequence, changes per session

Security is not bolted on.  It emerges from the same octahedral geometry
that drives computation.  Tampering breaks the lattice, and broken lattice
= no valid computation.

Integrates with:
  - octahedral_lookup.py   (eigenvalue tables, phi-stability)
  - geometric_bridge.py    (bridge targets, noise_power, confidence)
  - lattice_handshake.py   (CVP handshake, feltscore)
  - atlas/remote/g2b/bridges/physics_guard.py  (phi-coherence)
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

from src.octahedral_lookup import OCTAHEDRAL_EIGENVALUES, PHI

# ============================================================================
# Constants
# ============================================================================

OPTIMAL_NOISE = 0.62        # stochastic resonance peak (from FELTSensor)
NOISE_TOLERANCE = 0.15      # +/- 15%
PHI_SPACING_TOL = 0.05      # 5% tolerance for growth imperfections
TRACE_TOL = 1e-6            # eigenvalue trace tolerance
BRIDGE_IMPEDANCE_TOL = 0.10 # 10% impedance match tolerance

# Bridge target impedance signatures: (resistance_ohm, inductance_henry)
BRIDGE_SIGNATURES: Dict[str, Tuple[float, float]] = {
    "thermal":  (100.0,   0.01),
    "electric": (50.0,    0.001),
    "magnetic": (200.0,   0.1),
    "light":    (1000.0,  1e-6),
    "sound":    (500.0,   0.05),
    "wave":     (75.0,    0.002),
    "pressure": (300.0,   0.02),
    "chemical": (10000.0, 1e-9),
}


# ============================================================================
# Layer 1: Tetrahedral Parity
# ============================================================================

def tetrahedral_parity(cluster_bits: List[int]) -> int:
    """Return parity of a tetrahedral cluster (0=even, 1=odd)."""
    return sum(cluster_bits) % 2


def verify_cluster_parity(cluster_bits: List[int],
                          expected: int = 0) -> bool:
    """Cluster is valid if parity matches expected (default: even)."""
    return tetrahedral_parity(cluster_bits) == expected


def verify_all_clusters(clusters: List[List[int]],
                        expected: int = 0) -> Dict:
    """Verify parity across all tetrahedral clusters."""
    violations = []
    for i, c in enumerate(clusters):
        if tetrahedral_parity(c) != expected:
            violations.append(i)
    return {"passed": len(violations) == 0, "violations": violations}


# ============================================================================
# Layer 2: Phi-Spacing Constraint
# ============================================================================

def expected_phi_radius(n: int, r0: float = 0.8) -> float:
    """Expected radius at shell n: r_n = r0 * phi^n."""
    return r0 * (PHI ** n)


def verify_phi_spacing(radii: List[float], r0: float = 0.8,
                       tolerance: float = PHI_SPACING_TOL) -> Dict:
    """
    Verify that radii follow phi-spacing within tolerance.

    Physical tampering that changes shell spacing breaks this check.
    """
    violations = []
    for n, r in enumerate(radii):
        expected = expected_phi_radius(n, r0)
        dev = abs(r - expected) / max(expected, 1e-12)
        if dev > tolerance:
            violations.append({
                "shell": n, "measured": r,
                "expected": expected, "deviation": dev,
            })
    return {"passed": len(violations) == 0, "violations": violations}


# ============================================================================
# Layer 3: Trace Invariant
# ============================================================================

def verify_trace_invariant(eigenvalues: Tuple[float, float, float],
                           tolerance: float = TRACE_TOL) -> Dict:
    """
    Verify lambda_1 + lambda_2 + lambda_3 = 1 within tolerance.

    The octahedral tensor state is defined by eigenvalues with trace = 1.
    This is a physical constraint from the geometry, not a convention.
    """
    trace = sum(eigenvalues)
    deviation = abs(trace - 1.0)
    return {
        "passed": deviation < tolerance,
        "trace": trace,
        "deviation": deviation,
    }


def verify_all_traces(states: List[int],
                      tolerance: float = TRACE_TOL) -> Dict:
    """Verify trace invariant for a list of octahedral states."""
    violations = []
    for state in states:
        ev = OCTAHEDRAL_EIGENVALUES.get(state)
        if ev is None:
            violations.append({"state": state, "reason": "unknown_state"})
            continue
        result = verify_trace_invariant(ev, tolerance)
        if not result["passed"]:
            violations.append({
                "state": state, "trace": result["trace"],
                "deviation": result["deviation"],
            })
    return {"passed": len(violations) == 0, "violations": violations}


# ============================================================================
# Layer 4: Stochastic Resonance Lock
# ============================================================================

def verify_noise_lock(noise_level: float,
                      optimal: float = OPTIMAL_NOISE,
                      tolerance: float = NOISE_TOLERANCE) -> Dict:
    """
    Verify noise is within the stochastic resonance peak.

    Too little noise: system stagnates.
    Too much noise: coherence collapses.
    The lock IS the noise level itself.
    """
    if optimal <= 0:
        passed = noise_level == 0
        deviation = noise_level
    else:
        deviation = abs(noise_level - optimal) / optimal
        passed = deviation < tolerance
    return {
        "passed": passed,
        "noise_level": noise_level,
        "optimal": optimal,
        "deviation": deviation,
    }


# ============================================================================
# Layer 5: Bridge Target Authentication
# ============================================================================

def verify_bridge_target(target: str, measured_r: float,
                         measured_l: float,
                         tolerance: float = BRIDGE_IMPEDANCE_TOL) -> Dict:
    """
    Verify bridge target matches expected impedance signature.

    Each bridge target has a unique (resistance, inductance) pair.
    Spoofed bridges fail authentication.
    """
    if target not in BRIDGE_SIGNATURES:
        return {"passed": False, "reason": "unknown_target", "target": target}
    exp_r, exp_l = BRIDGE_SIGNATURES[target]
    r_dev = abs(measured_r - exp_r) / max(exp_r, 1e-12)
    l_dev = abs(measured_l - exp_l) / max(exp_l, 1e-12)
    r_ok = r_dev < tolerance
    l_ok = l_dev < tolerance
    return {
        "passed": r_ok and l_ok,
        "target": target,
        "r_deviation": r_dev,
        "l_deviation": l_dev,
    }


def verify_all_bridges(bridges: List[Tuple[str, float, float]],
                       tolerance: float = BRIDGE_IMPEDANCE_TOL) -> Dict:
    """Verify impedance signatures for all bridge targets."""
    violations = []
    for target, r, l in bridges:
        result = verify_bridge_target(target, r, l, tolerance)
        if not result["passed"]:
            violations.append(result)
    return {"passed": len(violations) == 0, "violations": violations}


# ============================================================================
# Layer 6: Temporal Handshake
# ============================================================================

def generate_temporal_handshake(seed: int, length: int = 8) -> List[float]:
    """
    Generate a phi-spaced temporal handshake sequence.

    The pattern follows the rhythm of the geometry: delays scale by phi^k
    where k is drawn from the octahedral state space (0-7).
    Changes per session (seed-dependent).
    """
    rng = random.Random(seed)
    times = []
    t = 0.0
    for _ in range(length):
        delay = 0.05 * (PHI ** rng.randint(0, 7))
        t += delay
        times.append(t)
    return times


def verify_temporal_handshake(received_times: List[float],
                              expected_seed: int,
                              tolerance: float = 0.05) -> Dict:
    """
    Verify received handshake matches expected phi-spacing.

    Replay attacks fail because the temporal handshake changes per session.
    """
    expected = generate_temporal_handshake(expected_seed, len(received_times))
    if len(received_times) != len(expected):
        return {"passed": False, "reason": "length_mismatch"}
    violations = []
    for i, (rt, et) in enumerate(zip(received_times, expected)):
        dev = abs(rt - et) / max(et, 1e-12)
        if dev > tolerance:
            violations.append({"index": i, "received": rt,
                               "expected": et, "deviation": dev})
    return {"passed": len(violations) == 0, "violations": violations}


# ============================================================================
# GeometricSecurity — aggregate verifier
# ============================================================================

class GeometricSecurity:
    """
    Self-enforcing security through geometric integrity.

    All six layers derive from octahedral geometry and phi-spacing.
    No passwords, no external keys — the shape IS the lock.

    Parameters
    ----------
    r0             : float — base radius for phi-spacing (default 0.8)
    optimal_noise  : float — stochastic resonance peak (default 0.62)
    parity_expected: int   — expected tetrahedral parity, 0=even (default 0)
    """

    def __init__(self, r0: float = 0.8, optimal_noise: float = OPTIMAL_NOISE,
                 parity_expected: int = 0):
        self.r0 = r0
        self.optimal_noise = optimal_noise
        self.parity_expected = parity_expected

    def full_check(self,
                   clusters: List[List[int]],
                   radii: List[float],
                   eigenvalues: List[Tuple[float, float, float]],
                   noise_level: float,
                   bridges: List[Tuple[str, float, float]],
                   handshake_seed: int,
                   handshake_times: List[float]) -> Dict:
        """
        Run all six security layers.

        Returns dict with per-layer results and overall pass/fail.
        """
        results = {}

        # Layer 1: Tetrahedral Parity
        results["tetrahedral_parity"] = verify_all_clusters(
            clusters, self.parity_expected)

        # Layer 2: Phi-Spacing
        results["phi_spacing"] = verify_phi_spacing(radii, self.r0)

        # Layer 3: Trace Invariant
        trace_violations = []
        for i, ev in enumerate(eigenvalues):
            tr = verify_trace_invariant(ev)
            if not tr["passed"]:
                trace_violations.append({"index": i, **tr})
        results["trace_invariant"] = {
            "passed": len(trace_violations) == 0,
            "violations": trace_violations,
        }

        # Layer 4: Stochastic Resonance Lock
        results["noise_lock"] = verify_noise_lock(
            noise_level, self.optimal_noise)

        # Layer 5: Bridge Authentication
        results["bridge_auth"] = verify_all_bridges(bridges)

        # Layer 6: Temporal Handshake
        results["temporal_handshake"] = verify_temporal_handshake(
            handshake_times, handshake_seed)

        # Overall
        results["all_pass"] = all(
            results[k]["passed"] for k in
            ["tetrahedral_parity", "phi_spacing", "trace_invariant",
             "noise_lock", "bridge_auth", "temporal_handshake"]
        )
        return results

    def report(self, results: Dict) -> str:
        """Generate human-readable security report."""
        lines = ["=" * 50, "GEOMETRIC SECURITY REPORT", "=" * 50]
        layer_names = [
            "tetrahedral_parity", "phi_spacing", "trace_invariant",
            "noise_lock", "bridge_auth", "temporal_handshake",
        ]
        for layer in layer_names:
            r = results.get(layer, {})
            status = "PASS" if r.get("passed") else "FAIL"
            label = layer.replace("_", " ").title()
            lines.append(f"  [{status:4s}] {label}")
        lines.append("-" * 50)
        overall = "SECURE" if results.get("all_pass") else "COMPROMISED"
        lines.append(f"  Overall: {overall}")
        lines.append("=" * 50)
        return "\n".join(lines)
