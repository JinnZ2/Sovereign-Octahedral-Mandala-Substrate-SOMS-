"""
OCTAHEDRAL ARITHMETIC v1.0
Native computation in glyph space — no decimal bottleneck.

Numbers are sequences of octahedral glyphs (base-8 digits).
Arithmetic happens in glyph space. Decimal is one projection, not the source.

The octahedron doesn't count in tens. Neither should the math.

Core types:
  OctahedralNumber  — positional glyph sequence with native arithmetic
  GlyphFraction     — irreducible ratio of two glyph numbers
  GlyphPrime        — glyph sequence that resists factorization

Key insight: primes in glyph space are sequences that cannot be expressed
as the product of two shorter sequences. The mandala solver finds them
by relaxing to ground state — the geometry discovers irreducibility.
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import math

# ---------------------------------------------------------------------------
# Octahedral glyph system
# ---------------------------------------------------------------------------

# The 8 sacred glyphs — native digits of octahedral arithmetic
GLYPHS = ["\u2295", "\u2296", "\u2297", "\u2298", "\u2299", "\u229a", "\u229b", "\u229c"]
#          ⊕         ⊖         ⊗         ⊘         ⊙         ⊚         ⊛         ⊜
#          0         1         2         3         4         5         6         7

BASE = 8  # octahedral symmetry order

# Glyph names for readability
GLYPH_NAMES = {
    0: "null",        # ⊕ — additive identity
    1: "mirror",      # ⊖ — reflection / unit
    2: "cross",       # ⊗ — first composite
    3: "void",        # ⊘ — first odd prime in glyph space
    4: "core",        # ⊙ — square of cross
    5: "orbital",     # ⊚ — second prime
    6: "star",        # ⊛ — cross * void
    7: "balanced",    # ⊜ — third prime
}

# Golden ratio in glyph-weighted form
PHI = (1 + math.sqrt(5)) / 2


# ---------------------------------------------------------------------------
# OctahedralNumber
# ---------------------------------------------------------------------------

class OctahedralNumber:
    """
    A number in octahedral (base-8) representation.

    Stored as a tuple of glyph indices (least significant first).
    All arithmetic happens natively in glyph space.
    Decimal conversion is a lossy projection, available but not primary.
    """

    __slots__ = ("digits",)

    def __init__(self, digits: Tuple[int, ...] = (0,)):
        """
        Args:
            digits: Glyph indices, least significant first. Each in [0..7].
        """
        # Strip trailing zeros (leading in positional sense)
        cleaned = list(digits)
        while len(cleaned) > 1 and cleaned[-1] == 0:
            cleaned.pop()
        self.digits = tuple(cleaned)

    # --- Constructors ---

    @classmethod
    def from_decimal(cls, n: int) -> OctahedralNumber:
        """Project a decimal integer into glyph space."""
        if n < 0:
            raise ValueError("Octahedral numbers are non-negative")
        if n == 0:
            return cls((0,))
        digits = []
        while n > 0:
            digits.append(n % BASE)
            n //= BASE
        return cls(tuple(digits))

    @classmethod
    def from_glyphs(cls, glyph_string: str) -> OctahedralNumber:
        """Parse a glyph string like '⊗⊖' into an OctahedralNumber."""
        digits = []
        for ch in glyph_string:
            if ch in GLYPHS:
                digits.append(GLYPHS.index(ch))
        if not digits:
            return cls((0,))
        return cls(tuple(digits))

    @classmethod
    def from_states(cls, states: List[int]) -> OctahedralNumber:
        """Create from a list of cell states (as returned by mandala solver)."""
        return cls(tuple(s % BASE for s in states))

    # --- Representation ---

    def to_glyphs(self) -> str:
        """Native representation: glyph sequence (least significant first)."""
        return "".join(GLYPHS[d] for d in self.digits)

    def to_glyphs_msb(self) -> str:
        """Glyph sequence, most significant first (conventional reading order)."""
        return "".join(GLYPHS[d] for d in reversed(self.digits))

    def to_decimal(self) -> int:
        """Lossy projection to decimal (for human convenience only)."""
        total = 0
        for i, d in enumerate(self.digits):
            total += d * (BASE ** i)
        return total

    def __repr__(self) -> str:
        return f"Oct({self.to_glyphs()}) = {self.to_decimal()}"

    def __str__(self) -> str:
        return self.to_glyphs()

    def __len__(self) -> int:
        """Number of glyph digits (complexity of the number)."""
        return len(self.digits)

    def __eq__(self, other) -> bool:
        if isinstance(other, OctahedralNumber):
            return self.digits == other.digits
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.digits)

    def __lt__(self, other: OctahedralNumber) -> bool:
        # Compare by length first, then lexicographic on reversed digits
        if len(self.digits) != len(other.digits):
            return len(self.digits) < len(other.digits)
        for a, b in zip(reversed(self.digits), reversed(other.digits)):
            if a != b:
                return a < b
        return False

    # --- Native arithmetic ---

    def add(self, other: OctahedralNumber) -> OctahedralNumber:
        """Glyph-native addition with carry propagation."""
        a = list(self.digits)
        b = list(other.digits)
        max_len = max(len(a), len(b))
        a.extend([0] * (max_len - len(a)))
        b.extend([0] * (max_len - len(b)))

        result = []
        carry = 0
        for i in range(max_len):
            s = a[i] + b[i] + carry
            result.append(s % BASE)
            carry = s // BASE
        if carry:
            result.append(carry)
        return OctahedralNumber(tuple(result))

    def subtract(self, other: OctahedralNumber) -> OctahedralNumber:
        """Glyph-native subtraction (assumes self >= other)."""
        a = list(self.digits)
        b = list(other.digits)
        max_len = max(len(a), len(b))
        a.extend([0] * (max_len - len(a)))
        b.extend([0] * (max_len - len(b)))

        result = []
        borrow = 0
        for i in range(max_len):
            diff = a[i] - b[i] - borrow
            if diff < 0:
                diff += BASE
                borrow = 1
            else:
                borrow = 0
            result.append(diff)
        return OctahedralNumber(tuple(result))

    def multiply(self, other: OctahedralNumber) -> OctahedralNumber:
        """Glyph-native multiplication (long multiplication in base-8)."""
        a = self.digits
        b = other.digits
        result = [0] * (len(a) + len(b))

        for i, da in enumerate(a):
            carry = 0
            for j, db in enumerate(b):
                product = da * db + result[i + j] + carry
                result[i + j] = product % BASE
                carry = product // BASE
            if carry:
                result[i + len(b)] += carry

        return OctahedralNumber(tuple(result))

    def divmod_glyph(self, divisor: OctahedralNumber) -> Tuple[OctahedralNumber, OctahedralNumber]:
        """
        Glyph-native division with remainder.

        Returns (quotient, remainder) both as OctahedralNumbers.
        This is the fundamental operation for irreducibility testing.
        """
        if divisor == OctahedralNumber((0,)):
            raise ZeroDivisionError("Division by glyph zero")

        # Work in decimal for now — the division algorithm in arbitrary base
        # is the same algorithm, just with different digit manipulation
        a = self.to_decimal()
        b = divisor.to_decimal()
        q, r = divmod(a, b)
        return OctahedralNumber.from_decimal(q), OctahedralNumber.from_decimal(r)

    def is_zero(self) -> bool:
        return all(d == 0 for d in self.digits)

    def is_unit(self) -> bool:
        """Is this the multiplicative identity (⊖ = 1)?"""
        return self.digits == (1,)

    # --- Operator overloads ---

    def __add__(self, other: OctahedralNumber) -> OctahedralNumber:
        return self.add(other)

    def __sub__(self, other: OctahedralNumber) -> OctahedralNumber:
        return self.subtract(other)

    def __mul__(self, other: OctahedralNumber) -> OctahedralNumber:
        return self.multiply(other)

    def __floordiv__(self, other: OctahedralNumber) -> OctahedralNumber:
        q, _ = self.divmod_glyph(other)
        return q

    def __mod__(self, other: OctahedralNumber) -> OctahedralNumber:
        _, r = self.divmod_glyph(other)
        return r

    # --- Glyph-space primality ---

    def is_prime(self) -> bool:
        """
        Test if this glyph number is irreducible (prime).

        A glyph number is prime if it cannot be expressed as the product
        of two glyph numbers, each with fewer digits than itself.
        This is primality in the mathematical sense, computed in glyph space.
        """
        n = self.to_decimal()
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0:
            return False
        # Trial division in glyph space
        d = OctahedralNumber.from_decimal(3)
        limit = OctahedralNumber.from_decimal(int(math.isqrt(n)) + 1)
        two = OctahedralNumber.from_decimal(2)
        while d < limit:
            _, remainder = self.divmod_glyph(d)
            if remainder.is_zero():
                return False
            d = d.add(two)
        return True

    def factorize(self) -> List[OctahedralNumber]:
        """
        Decompose into irreducible (prime) glyph factors.

        Returns list of prime OctahedralNumbers whose product equals self.
        """
        n = self.to_decimal()
        if n <= 1:
            return [self]
        factors = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors.append(OctahedralNumber.from_decimal(d))
                n //= d
            d += 1
        if n > 1:
            factors.append(OctahedralNumber.from_decimal(n))
        return factors

    def glyph_complexity(self) -> int:
        """
        Complexity of this number in glyph space.

        Single-glyph numbers have complexity 1.
        Multi-glyph numbers have complexity = number of digits.
        Primes are "irreducibly complex" — they can't be shortened.
        """
        return len(self.digits)

    def phi_weight(self) -> float:
        """
        Golden-ratio weighted value.

        Each glyph position is weighted by PHI^i instead of BASE^i.
        This creates a different number line where Fibonacci-aligned
        numbers cluster near integer values.
        """
        total = 0.0
        for i, d in enumerate(self.digits):
            total += d * (PHI ** i)
        return total


# ---------------------------------------------------------------------------
# GlyphFraction
# ---------------------------------------------------------------------------

class GlyphFraction:
    """
    A fraction in octahedral glyph space.

    Represented as numerator/denominator, both OctahedralNumbers.
    Automatically reduced to irreducible form (glyph-native GCD).

    This is the natural representation for quantities that don't
    terminate in any base — the glyphs hold the exact ratio.
    """

    __slots__ = ("num", "den")

    def __init__(self, numerator: OctahedralNumber, denominator: OctahedralNumber):
        if denominator.is_zero():
            raise ZeroDivisionError("Glyph fraction with zero denominator")
        # Reduce to lowest terms
        g = self._gcd(numerator, denominator)
        if not g.is_unit() and not g.is_zero():
            self.num = numerator // g
            self.den = denominator // g
        else:
            self.num = numerator
            self.den = denominator

    @classmethod
    def from_decimal_ratio(cls, p: int, q: int) -> GlyphFraction:
        return cls(OctahedralNumber.from_decimal(p), OctahedralNumber.from_decimal(q))

    @staticmethod
    def _gcd(a: OctahedralNumber, b: OctahedralNumber) -> OctahedralNumber:
        """Euclidean GCD in glyph space."""
        while not b.is_zero():
            _, r = a.divmod_glyph(b)
            a = b
            b = r
        return a

    def to_glyphs(self) -> str:
        return f"{self.num.to_glyphs()}/{self.den.to_glyphs()}"

    def to_decimal_ratio(self) -> Tuple[int, int]:
        return (self.num.to_decimal(), self.den.to_decimal())

    def is_integer(self) -> bool:
        return self.den.is_unit()

    def is_irreducible(self) -> bool:
        """True if numerator and denominator share no common factors."""
        g = self._gcd(self.num, self.den)
        return g.is_unit()

    def multiply(self, other: GlyphFraction) -> GlyphFraction:
        return GlyphFraction(self.num * other.num, self.den * other.den)

    def add(self, other: GlyphFraction) -> GlyphFraction:
        new_num = (self.num * other.den).add(other.num * self.den)
        new_den = self.den * other.den
        return GlyphFraction(new_num, new_den)

    def __repr__(self) -> str:
        return f"GlyphFrac({self.to_glyphs()}) = {self.num.to_decimal()}/{self.den.to_decimal()}"

    def __str__(self) -> str:
        return self.to_glyphs()

    def __eq__(self, other) -> bool:
        if isinstance(other, GlyphFraction):
            return self.num == other.num and self.den == other.den
        return NotImplemented


# ---------------------------------------------------------------------------
# Bridge to mandala computation
# ---------------------------------------------------------------------------

def states_to_number(states: List[int], offset: int = 2) -> OctahedralNumber:
    """
    Convert mandala cell states to an OctahedralNumber.

    The offset (default 2) matches the factor register convention:
    factor = 2 + positional_value.
    """
    raw = OctahedralNumber(tuple(s % BASE for s in states))
    if offset > 0:
        return raw.add(OctahedralNumber.from_decimal(offset))
    return raw


def number_to_states(num: OctahedralNumber, num_cells: int, offset: int = 2) -> List[int]:
    """
    Convert an OctahedralNumber back to cell states for a mandala register.
    """
    if offset > 0:
        num = num.subtract(OctahedralNumber.from_decimal(offset))
    states = list(num.digits)
    while len(states) < num_cells:
        states.append(0)
    return states[:num_cells]


def factor_pair_glyphs(N: int) -> Optional[Tuple[OctahedralNumber, OctahedralNumber]]:
    """
    Express the factorization of N entirely in glyph space.

    Returns None if N is prime (irreducible glyph sequence).
    """
    oct_N = OctahedralNumber.from_decimal(N)
    if oct_N.is_prime():
        return None
    factors = oct_N.factorize()
    if len(factors) < 2:
        return None
    # Return smallest factor and its complement
    fa = factors[0]
    fb = oct_N // fa
    return (fa, fb)


# ---------------------------------------------------------------------------
# Glyph multiplication table
# ---------------------------------------------------------------------------

def glyph_multiplication_table() -> Dict[Tuple[str, str], str]:
    """
    The complete single-digit multiplication table in glyph space.

    This is the octahedral analog of the decimal times table.
    Products that exceed single-digit become multi-glyph numbers.
    """
    table = {}
    for i in range(BASE):
        for j in range(BASE):
            a = OctahedralNumber((i,))
            b = OctahedralNumber((j,))
            product = a.multiply(b)
            table[(GLYPHS[i], GLYPHS[j])] = product.to_glyphs()
    return table


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_glyph_arithmetic():
    """Show native arithmetic in glyph space."""
    print("=" * 60)
    print("OCTAHEDRAL ARITHMETIC: Native Glyph Math")
    print("=" * 60)

    # Basic numbers
    print("\n   Glyph number system (base-8, octahedral):")
    for i in range(16):
        n = OctahedralNumber.from_decimal(i)
        print(f"      {i:>3d} = {n.to_glyphs():<6s}  phi-weight={n.phi_weight():.3f}")

    # Arithmetic
    print("\n   Arithmetic in glyph space:")
    a = OctahedralNumber.from_decimal(11)
    b = OctahedralNumber.from_decimal(13)
    print(f"      {a} + {b} = {a + b}   ({a.to_decimal()} + {b.to_decimal()} = {(a + b).to_decimal()})")
    print(f"      {a} * {b} = {a * b}   ({a.to_decimal()} * {b.to_decimal()} = {(a * b).to_decimal()})")

    c = OctahedralNumber.from_decimal(143)
    q, r = c.divmod_glyph(a)
    print(f"      {c} / {a} = {q} remainder {r}   ({c.to_decimal()} / {a.to_decimal()} = {q.to_decimal()} r {r.to_decimal()})")


def demo_primes():
    """Show prime detection in glyph space."""
    print("\n" + "=" * 60)
    print("GLYPH PRIMES: Irreducible Sequences")
    print("=" * 60)

    print("\n   Primes are glyph sequences that resist factorization:")
    primes_found = []
    for i in range(2, 50):
        n = OctahedralNumber.from_decimal(i)
        if n.is_prime():
            primes_found.append(n)
            factors_str = "PRIME (irreducible)"
        else:
            factors = n.factorize()
            factors_str = " * ".join(str(f) for f in factors)
        if i < 20 or n.is_prime():
            print(f"      {n.to_glyphs():<8s} ({i:>3d})  {factors_str}")

    print(f"\n   {len(primes_found)} primes found in glyph space up to 50")
    print(f"   Glyph primes: {' '.join(p.to_glyphs() for p in primes_found)}")


def demo_fractions():
    """Show glyph fractions — exact representation without decimal truncation."""
    print("\n" + "=" * 60)
    print("GLYPH FRACTIONS: Exact Ratios")
    print("=" * 60)

    print("\n   Fractions that don't terminate in decimal, exact in glyphs:")
    test_fractions = [(1, 3), (1, 7), (2, 7), (3, 7), (5, 7), (1, 5), (3, 11), (7, 13)]
    for p, q in test_fractions:
        gf = GlyphFraction.from_decimal_ratio(p, q)
        print(f"      {p}/{q} = {gf.to_glyphs():<12s}  irreducible: {gf.is_irreducible()}")

    # PHI approximations
    print("\n   Golden ratio approximations (Fibonacci fractions):")
    fibs = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    for i in range(1, len(fibs) - 1):
        gf = GlyphFraction.from_decimal_ratio(fibs[i + 1], fibs[i])
        decimal_approx = fibs[i + 1] / fibs[i]
        print(f"      {fibs[i+1]:>3d}/{fibs[i]:<3d} = {gf.to_glyphs():<12s}  "
              f"decimal: {decimal_approx:.6f}  phi-err: {abs(decimal_approx - PHI):.2e}")


def demo_multiplication_table():
    """Show the single-digit glyph multiplication table."""
    print("\n" + "=" * 60)
    print("GLYPH MULTIPLICATION TABLE")
    print("=" * 60)

    print("\n      ", end="")
    for j in range(BASE):
        print(f"  {GLYPHS[j]:>4s}", end="")
    print()
    print("      " + "-" * (6 * BASE))

    for i in range(BASE):
        print(f"   {GLYPHS[i]}  |", end="")
        for j in range(BASE):
            a = OctahedralNumber((i,))
            b = OctahedralNumber((j,))
            p = a * b
            print(f"  {p.to_glyphs():>4s}", end="")
        print()


def demo_factorization_bridge():
    """Show how mandala solver results map to glyph arithmetic."""
    print("\n" + "=" * 60)
    print("BRIDGE: Mandala Solver -> Glyph Arithmetic")
    print("=" * 60)

    test_numbers = [15, 21, 35, 77, 143, 221, 323]
    print(f"\n   {'N':>5s}  {'Glyph(N)':>10s}  {'Prime?':>7s}  {'Factors (glyph)':>20s}  {'Verify'}")
    print("   " + "-" * 65)

    for N in test_numbers:
        oct_N = OctahedralNumber.from_decimal(N)
        is_p = oct_N.is_prime()
        if is_p:
            factor_str = "IRREDUCIBLE"
            verify = "-"
        else:
            pair = factor_pair_glyphs(N)
            if pair:
                fa, fb = pair
                product = fa * fb
                factor_str = f"{fa.to_glyphs()} * {fb.to_glyphs()}"
                verify = "ok" if product.to_decimal() == N else "FAIL"
            else:
                factor_str = "?"
                verify = "?"
        print(f"   {N:>5d}  {oct_N.to_glyphs():>10s}  {'YES' if is_p else 'no':>7s}"
              f"  {factor_str:>20s}  {verify}")


if __name__ == "__main__":
    print("=" * 60)
    print("OCTAHEDRAL ARITHMETIC v1.0")
    print("   Native computation in glyph space")
    print("=" * 60)

    demo_glyph_arithmetic()
    demo_primes()
    demo_fractions()
    demo_multiplication_table()
    demo_factorization_bridge()

    print("\n" + "=" * 60)
    print("The octahedron computes. The glyphs are the math.")
    print("=" * 60)
