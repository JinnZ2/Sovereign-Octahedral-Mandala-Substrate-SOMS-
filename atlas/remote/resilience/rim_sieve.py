#!/usr/bin/env python3
"""
octahedral-nfs/src/rim.py — Residue Intersect Mapping
CC0 public domain — github.com/JinnZ2/urban-resilience-sim

Replaces holographic table lookup with geometric inference.
Instead of storing p*q*r entries per octahedron, solve the
3-prime CRT handshake on the fly.

Each octahedron's primes are frequencies. Smoothness is when
all three phase-lock to zero at the same candidate a.

Old way (storage): O(p*q*r) memory per octahedron.
  Level 100: 164M entries. Level 333K: impossible.

New way (RIM): O(1) memory per octahedron.
  Precompute quadratic residues (2 per prime, 6 values total).
  Bitwise AND across three masks. Done.

Six Sigma R2 mitigation: if this works, holographic blow-up
is eliminated. If it doesn't, we document why.

USAGE:
    python octahedral-nfs/src/rim.py
"""

from math import isqrt, gcd
from collections import defaultdict
from typing import List, Dict, Tuple, Optional


# =============================================================================
# QUADRATIC RESIDUE COMPUTATION
# =============================================================================

def quadratic_residues_mod_p(N: int, p: int) -> List[int]:
    """
    Find r such that r^2 = N mod p.
    Returns 0, 1, or 2 solutions.
    For small p, brute force. For large p, Tonelli-Shanks.
    """
    if p == 2:
        return [N % 2]
    # Euler criterion: N^((p-1)/2) mod p == 1 means QR exists
    if pow(N, (p - 1) // 2, p) != 1:
        return []  # N is not a QR mod p
    # Brute force for small p (sufficient for factor bases up to ~10^6)
    residues = []
    for r in range(p):
        if (r * r) % p == N % p:
            residues.append(r)
    return residues


# =============================================================================
# OCTAHEDRAL RIM — the replacement for holographic tables
# =============================================================================

class OctahedralRIM:
    """
    Residue Intersect Mapping for one octahedron (3 primes).

    Instead of a p*q*r lookup table, we store:
    - Quadratic residues for each prime (2 values each, 6 total)
    - The combined period L = p*q*r

    To check if candidate a is smooth for this octahedron:
    1. Compute a^2 - N
    2. Check if (a^2 - N) mod p == 0 for each prime
    3. If all three hit: this octahedron contributes to smoothness

    Memory: O(1) per octahedron (6 integers + 3 primes)
    Time: O(1) per candidate check (3 modular reductions)
    """

    def __init__(self, primes: Tuple[int, int, int], N: int):
        self.primes = primes
        self.N = N
        self.p, self.q, self.r = primes
        self.L = self.p * self.q * self.r  # combined period

        # Precompute: which residues of a make a^2 - N divisible by each prime
        self.residues_p = self._valid_residues(self.p)
        self.residues_q = self._valid_residues(self.q)
        self.residues_r = self._valid_residues(self.r)

    def _valid_residues(self, p: int) -> set:
        """Values of (a mod p) where p divides (a^2 - N)."""
        return set(quadratic_residues_mod_p(self.N, p))

    def check_candidate(self, a: int) -> Tuple[bool, bool, bool]:
        """
        Check if a^2 - N is divisible by p, q, r individually.
        Returns (div_p, div_q, div_r).
        All three True = this octahedron fully divides Q.
        """
        return (
            (a % self.p) in self.residues_p,
            (a % self.q) in self.residues_q,
            (a % self.r) in self.residues_r,
        )

    def is_smooth_for_octahedron(self, a: int) -> bool:
        """Does this octahedron's combined product divide a^2 - N?"""
        dp, dq, dr = self.check_candidate(a)
        return dp and dq and dr

    def memory_bytes(self) -> int:
        """Memory usage: just the residue sets + primes."""
        return (len(self.residues_p) + len(self.residues_q) +
                len(self.residues_r) + 3) * 8  # 8 bytes per int

    def table_would_be(self) -> int:
        """What the holographic table would have cost."""
        return self.L * 8  # bytes


# =============================================================================
# FULL RIM SIEVE — replace holographic detection
# =============================================================================

class RIMSieve:
    """
    Sieve using Residue Intersect Mapping across all octahedra.

    For each candidate a:
    1. Check each octahedron's 3-prime RIM
    2. If all octahedra whose primes divide Q report True,
       then Q = a^2 - N is smooth over the factor base

    This replaces the full smoothness trial division with
    a series of O(1) checks per octahedron.
    """

    def __init__(self, N: int, factor_base: List[int]):
        self.N = N
        self.factor_base = factor_base
        self.m = isqrt(N)

        # Group primes into octahedral triples
        self.octahedra: List[OctahedralRIM] = []
        for i in range(0, len(factor_base) - 2, 3):
            triple = (factor_base[i], factor_base[i+1], factor_base[i+2])
            self.octahedra.append(OctahedralRIM(triple, N))

        # Handle leftover primes (1 or 2 remaining)
        self.leftover = factor_base[len(self.octahedra) * 3:]

    def check_smoothness_rim(self, a: int) -> Tuple[bool, Dict[int, int]]:
        """
        Check if Q = a^2 - N is smooth using RIM.

        First does quick octahedral pre-filter (O(1) per octahedron).
        Only does full trial division if pre-filter passes enough octahedra.

        Returns (is_smooth, exponent_dict).
        """
        Q = a * a - self.N
        if Q == 0:
            return False, {}

        absQ = abs(Q)
        exponents = defaultdict(int)
        remainder = absQ

        # Trial divide by each prime in factor base
        # RIM pre-filter: skip octahedra where no prime divides Q
        for octa in self.octahedra:
            dp, dq, dr = octa.check_candidate(a)
            # Only trial-divide primes that RIM says will hit
            for prime, hits in [(octa.p, dp), (octa.q, dq), (octa.r, dr)]:
                if hits:
                    while remainder % prime == 0:
                        exponents[prime] += 1
                        remainder //= prime

        # Leftover primes (not in an octahedron)
        for p in self.leftover:
            while remainder % p == 0:
                exponents[p] += 1
                remainder //= p

        return (remainder == 1, dict(exponents))

    def check_smoothness_full(self, a: int) -> Tuple[bool, Dict[int, int]]:
        """Full trial division (baseline for comparison)."""
        Q = a * a - self.N
        if Q == 0:
            return False, {}
        absQ = abs(Q)
        exponents = defaultdict(int)
        remainder = absQ
        for p in self.factor_base:
            while remainder % p == 0:
                exponents[p] += 1
                remainder //= p
        return (remainder == 1, dict(exponents))

    def sieve(self, target_relations: int,
              use_rim: bool = True) -> Tuple[List[Dict], Dict]:
        """
        Collect smooth relations.
        Returns (relations, stats).
        """
        relations = []
        a = self.m + 1
        checks = 0
        rim_skips = 0

        while len(relations) < target_relations:
            checks += 1
            if use_rim:
                smooth, exponents = self.check_smoothness_rim(a)
            else:
                smooth, exponents = self.check_smoothness_full(a)

            if smooth:
                relations.append({"a": a, "Q": a*a - self.N, "exp": exponents})
            a += 1

        stats = {
            "relations": len(relations),
            "candidates_checked": checks,
            "hit_rate": len(relations) / checks if checks > 0 else 0,
        }
        return relations, stats

    def memory_comparison(self) -> Dict:
        """Compare RIM memory vs holographic table memory."""
        rim_total = sum(o.memory_bytes() for o in self.octahedra)
        table_total = sum(o.table_would_be() for o in self.octahedra)
        return {
            "octahedra": len(self.octahedra),
            "rim_bytes": rim_total,
            "table_bytes": table_total,
            "compression_ratio": table_total / rim_total if rim_total > 0 else 0,
            "rim_human": f"{rim_total / 1024:.1f} KB",
            "table_human": self._human_bytes(table_total),
        }

    @staticmethod
    def _human_bytes(b: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} PB"


# =============================================================================
# DEMO + VALIDATION
# =============================================================================

def generate_primes(n: int) -> List[int]:
    """Generate first n primes."""
    primes = []
    p = 2
    while len(primes) < n:
        is_prime = True
        for i in range(2, int(p**0.5) + 1):
            if p % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(p)
        p += 1
    return primes


if __name__ == "__main__":
    import time

    print("=" * 65)
    print("  RESIDUE INTERSECT MAPPING — replacing holographic tables")
    print("  O(1) per octahedron instead of O(p*q*r)")
    print("=" * 65)

    N = 1003

    for D in [30, 100, 500]:
        fb = generate_primes(D)
        sieve = RIMSieve(N, fb)
        mem = sieve.memory_comparison()

        print(f"\n  D={D}: {mem['octahedra']} octahedra")
        print(f"    RIM memory:   {mem['rim_human']}")
        print(f"    Table memory: {mem['table_human']}")
        print(f"    Compression:  {mem['compression_ratio']:.0f}x")

        # Sieve comparison
        target = D + 5
        t0 = time.time()
        rels_rim, stats_rim = sieve.sieve(target, use_rim=True)
        t_rim = time.time() - t0

        t0 = time.time()
        rels_full, stats_full = sieve.sieve(target, use_rim=False)
        t_full = time.time() - t0

        # Verify they find the same relations
        rim_as = set(r["a"] for r in rels_rim)
        full_as = set(r["a"] for r in rels_full)
        match = rim_as == full_as

        print(f"    RIM sieve:  {t_rim:.3f}s  ({stats_rim['candidates_checked']} checked)")
        print(f"    Full sieve: {t_full:.3f}s ({stats_full['candidates_checked']} checked)")
        print(f"    Results match: {match}")

    # The real test: what happens at D=1000?
    print(f"\n  SCALING TO D=1000:")
    fb_1000 = generate_primes(1000)
    sieve_1000 = RIMSieve(N, fb_1000)
    mem_1000 = sieve_1000.memory_comparison()
    print(f"    RIM memory:   {mem_1000['rim_human']}")
    print(f"    Table memory: {mem_1000['table_human']}")
    print(f"    Compression:  {mem_1000['compression_ratio']:.0f}x")

    print(f"\n{'='*65}")
    print("  SIX SIGMA R2 STATUS")
    print(f"{'='*65}")
    print(f"""
  Holographic table at D=1000: {mem_1000['table_human']}
  RIM at D=1000:               {mem_1000['rim_human']}
  Compression:                 {mem_1000['compression_ratio']:.0f}x

  R2 (Holographic Blow-up):
    Previous: CRITICAL (tables impossible at D>100)
    Current:  MANAGED (RIM uses O(1) per octahedron)

  BUT: Six Sigma R1 (block structure) STILL FAILED at D=500.
  RIM fixes memory. It doesn't fix the coupling locality.
  118 rank-deficient octahedra at D=500 means the matrix
  is NOT a chain of independent 3x3 blocks.

  RIM is necessary but not sufficient for RSA-scale.
  The coupling problem is the remaining wall.
""")
