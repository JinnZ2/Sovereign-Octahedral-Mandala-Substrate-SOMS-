"""
Octahedral Immune System — Adaptive geometric security.

Security as immunity: learns valid states, remembers attacks, tightens
tolerances under threat, and evolves as the physics grows.

Biological analogy:
  DNA encodes self               <-> Tetrahedral parity encodes identity
  Mismatch repair detects mutation <-> Phi-spacing detects tampering
  Antibodies adapt to threats     <-> Bridge signatures update with use
  Memory cells recall infections  <-> Immune memory recalls attack patterns
  Autoimmune = self-attack        <-> Trace invariant prevents false rejection

Integrates with GeometricSecurity (6-layer static checks) and adds:
  - ImmuneMemory: remembers valid tensor/noise signatures + attack patterns
  - Adaptive tolerances: tighten after repeated attacks
  - Confidence scoring: partial-pass states trigger investigation, not rejection
  - Evolution rate: learning accelerates under sustained attack
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any, Optional

from src.geometric_security import (
    GeometricSecurity,
    verify_all_clusters,
    verify_phi_spacing,
    verify_trace_invariant,
    verify_noise_lock,
    verify_all_bridges,
    verify_temporal_handshake,
    PHI, OPTIMAL_NOISE,
)


# ============================================================================
# Immune Memory
# ============================================================================

@dataclass
class ImmuneMemory:
    """
    Memory of valid states and past attacks.

    Valid signatures: tensor eigenvalue hashes + noise levels that passed
    all six layers.  Used for fast recognition of known-good states.

    Attack patterns: failed layer sets + tensor/noise samples from rejected
    attempts.  Used to detect repeated attack vectors and tighten tolerances.
    """
    max_valid: int = 100
    max_attacks: int = 100
    valid_signatures: List[Dict] = field(default_factory=list)
    attack_patterns: List[Dict] = field(default_factory=list)

    def add_valid(self, eigenvalue_hash: int, noise: float):
        """Record a valid state in immune memory."""
        self.valid_signatures.append({
            "ev_hash": eigenvalue_hash,
            "noise": noise,
        })
        if len(self.valid_signatures) > self.max_valid:
            self.valid_signatures = self.valid_signatures[-self.max_valid:]

    def add_attack(self, failed_layers: List[str],
                   eigenvalue_hash: int, noise: float):
        """Record an attack pattern."""
        self.attack_patterns.append({
            "failed_layers": failed_layers,
            "ev_hash": eigenvalue_hash,
            "noise": noise,
        })
        if len(self.attack_patterns) > self.max_attacks:
            self.attack_patterns = self.attack_patterns[-self.max_attacks:]

    def is_known_valid(self, eigenvalue_hash: int, noise: float,
                       noise_tol: float = 0.30) -> bool:
        """Check if this state matches a previously validated signature."""
        for sig in self.valid_signatures:
            if sig["ev_hash"] == eigenvalue_hash:
                if abs(sig["noise"] - noise) < noise_tol:
                    return True
        return False

    @property
    def health_ratio(self) -> float:
        """Ratio of valid states to attacks.  High = healthy immune system."""
        n_attacks = len(self.attack_patterns)
        if n_attacks == 0:
            return float(len(self.valid_signatures)) if self.valid_signatures else 1.0
        return len(self.valid_signatures) / n_attacks


# ============================================================================
# Octahedral Immune System
# ============================================================================

class OctahedralImmuneSystem:
    """
    Adaptive immune system for octahedral crystalline computing.

    Wraps GeometricSecurity's six static layers with:
      - Immune memory (valid states + attack history)
      - Adaptive tolerances (tighten under repeated attack)
      - Confidence-based action routing (accept / investigate / quarantine)

    Parameters
    ----------
    r0              : float — base phi-spacing radius (default 0.8)
    optimal_noise   : float — stochastic resonance peak (default 0.62)
    parity_expected : int   — tetrahedral parity expectation (default 0, even)
    evolution_rate  : float — tolerance tightening rate per attack batch (default 0.01)
    """

    def __init__(self, r0: float = 0.8, optimal_noise: float = OPTIMAL_NOISE,
                 parity_expected: int = 0, evolution_rate: float = 0.01):
        self.security = GeometricSecurity(r0, optimal_noise, parity_expected)
        self.memory = ImmuneMemory()
        self.evolution_rate = evolution_rate

        # Adaptive tolerance overrides (start at defaults, can tighten)
        self.phi_tolerance = 0.05
        self.noise_tolerance = 0.15
        self.bridge_tolerance = 0.10

    def _eigenvalue_hash(self, eigenvalues: List[Tuple[float, float, float]]) -> int:
        """Deterministic hash of eigenvalue list for memory lookup."""
        return hash(tuple(tuple(round(v, 6) for v in ev) for ev in eigenvalues))

    def _tighten_tolerances(self):
        """Tighten tolerances after attack batch detected."""
        self.phi_tolerance *= (1.0 - self.evolution_rate)
        self.noise_tolerance *= (1.0 - self.evolution_rate)
        self.bridge_tolerance *= (1.0 - self.evolution_rate)
        # Floor: never tighten below 1% — avoid false positives
        self.phi_tolerance = max(self.phi_tolerance, 0.01)
        self.noise_tolerance = max(self.noise_tolerance, 0.03)
        self.bridge_tolerance = max(self.bridge_tolerance, 0.02)

    def immune_response(self,
                        clusters: List[List[int]],
                        radii: List[float],
                        eigenvalues: List[Tuple[float, float, float]],
                        noise_level: float,
                        bridges: List[Tuple[str, float, float]],
                        handshake_seed: int,
                        handshake_times: List[float]) -> Dict[str, Any]:
        """
        Full immune response: static checks + memory + adaptation.

        Returns
        -------
        dict with keys:
          passed      : bool  — all six layers passed
          confidence  : float — fraction of layers that passed [0, 1]
          action      : str   — 'accept' | 'investigate' | 'quarantine'
          layers      : dict  — per-layer pass/fail
          immune      : dict  — memory stats and health ratio
          tolerances  : dict  — current adaptive tolerance values
        """
        # Run static checks with current adaptive tolerances
        parity_r = verify_all_clusters(clusters, self.security.parity_expected)
        phi_r = verify_phi_spacing(radii, self.security.r0, self.phi_tolerance)

        trace_violations = []
        for i, ev in enumerate(eigenvalues):
            tr = verify_trace_invariant(ev)
            if not tr["passed"]:
                trace_violations.append({"index": i, **tr})
        trace_r = {"passed": len(trace_violations) == 0,
                   "violations": trace_violations}

        noise_r = verify_noise_lock(noise_level, self.security.optimal_noise,
                                    self.noise_tolerance)
        bridge_r = verify_all_bridges(bridges, self.bridge_tolerance)
        handshake_r = verify_temporal_handshake(handshake_times, handshake_seed)

        layers = {
            "tetrahedral_parity": parity_r["passed"],
            "phi_spacing": phi_r["passed"],
            "trace_invariant": trace_r["passed"],
            "noise_lock": noise_r["passed"],
            "bridge_auth": bridge_r["passed"],
            "temporal_handshake": handshake_r["passed"],
        }

        passed = all(layers.values())
        confidence = sum(layers.values()) / len(layers)
        ev_hash = self._eigenvalue_hash(eigenvalues)

        # Memory-informed action routing
        if passed:
            self.memory.add_valid(ev_hash, noise_level)
            action = "accept"
        else:
            failed = [k for k, v in layers.items() if not v]
            known = self.memory.is_known_valid(ev_hash, noise_level)

            if known:
                # Previously valid state now failing — investigate, don't reject
                action = "investigate"
            elif confidence >= 0.67:
                # Most layers pass — could be environmental drift
                action = "investigate"
            else:
                # Clear failure — quarantine and remember
                action = "quarantine"
                self.memory.add_attack(failed, ev_hash, noise_level)

                # Tighten tolerances after sustained attacks
                if len(self.memory.attack_patterns) > 10:
                    self._tighten_tolerances()

        return {
            "passed": passed,
            "confidence": confidence,
            "action": action,
            "layers": layers,
            "immune": {
                "valid_states": len(self.memory.valid_signatures),
                "attacks_remembered": len(self.memory.attack_patterns),
                "health_ratio": self.memory.health_ratio,
            },
            "tolerances": {
                "phi": self.phi_tolerance,
                "noise": self.noise_tolerance,
                "bridge": self.bridge_tolerance,
            },
        }

    def report(self, response: Dict[str, Any]) -> str:
        """Generate human-readable immune response report."""
        lines = [
            "=" * 55,
            "OCTAHEDRAL IMMUNE SYSTEM REPORT",
            "=" * 55,
        ]
        for layer, ok in response["layers"].items():
            status = "PASS" if ok else "FAIL"
            label = layer.replace("_", " ").title()
            lines.append(f"  [{status:4s}] {label}")

        lines.append("-" * 55)
        lines.append(f"  Action     : {response['action'].upper()}")
        lines.append(f"  Confidence : {response['confidence']:.0%}")
        lines.append(f"  Valid known: {response['immune']['valid_states']}")
        lines.append(f"  Attacks    : {response['immune']['attacks_remembered']}")
        lines.append(f"  Health     : {response['immune']['health_ratio']:.2f}")
        lines.append(f"  Tolerances : phi={response['tolerances']['phi']:.4f}"
                     f"  noise={response['tolerances']['noise']:.4f}"
                     f"  bridge={response['tolerances']['bridge']:.4f}")
        lines.append("=" * 55)
        return "\n".join(lines)
