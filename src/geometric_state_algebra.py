"""
Geometric State Algebra — Full O_h symmetry group as computational substrate.

Adapted from Mandala-Computing/geometric_state_algebra.py for direct use
inside SOMS.  States ARE symmetry operations (not flat integers labelled
geometrically).  Cancellation is group composition to identity.

Core types integrated here:
    OhElement           — single symmetry operation (3×3 integer matrix)
    OhGroup             — full 48-element group with Cayley graph & distances
    GroupRingElement     — formal sum in Z[O_h], geometric superposition
    GeometricState      — cell state that IS a group element
    CayleyEnergy        — coupling via Cayley graph distance (SOMS pathway C)

The 8 classical SOMS states (0-7) map to 8 geometrically maximal elements
of O_h.  All 48 elements remain available for richer computation.

Source: github.com/JinnZ2/Mandala-Computing  (CC0 / MIT)
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import math

from src.octahedral_lookup import PHI, POSITIONS

# ---------------------------------------------------------------------------
# OhElement: a single symmetry operation
# ---------------------------------------------------------------------------

OCTAHEDRAL_VERTICES = (
    ( 1,  0,  0),
    (-1,  0,  0),
    ( 0,  1,  0),
    ( 0, -1,  0),
    ( 0,  0,  1),
    ( 0,  0, -1),
)


class OhElement:
    """Element of the octahedral symmetry group O_h (3×3 integer matrix)."""

    __slots__ = ("_mat", "_hash")

    def __init__(self, matrix: Tuple[Tuple[int, ...], ...]):
        self._mat = tuple(tuple(int(x) for x in row) for row in matrix)
        self._hash = hash(self._mat)

    @property
    def matrix(self) -> Tuple[Tuple[int, ...], ...]:
        return self._mat

    def compose(self, other: OhElement) -> OhElement:
        a, b = self._mat, other._mat
        return OhElement(tuple(
            tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
            for i in range(3)
        ))

    def inverse(self) -> OhElement:
        m = self._mat
        return OhElement(((m[0][0], m[1][0], m[2][0]),
                          (m[0][1], m[1][1], m[2][1]),
                          (m[0][2], m[1][2], m[2][2])))

    def is_identity(self) -> bool:
        return self._mat == ((1, 0, 0), (0, 1, 0), (0, 0, 1))

    def determinant(self) -> int:
        m = self._mat
        return (m[0][0] * (m[1][1]*m[2][2] - m[1][2]*m[2][1])
              - m[0][1] * (m[1][0]*m[2][2] - m[1][2]*m[2][0])
              + m[0][2] * (m[1][0]*m[2][1] - m[1][1]*m[2][0]))

    def is_proper(self) -> bool:
        return self.determinant() == 1

    def order(self) -> int:
        current = self
        for n in range(1, 49):
            if current.is_identity():
                return n
            current = current.compose(self)
        return 48

    def trace(self) -> int:
        return self._mat[0][0] + self._mat[1][1] + self._mat[2][2]

    def act_on_vertex(self, v: Tuple[int, int, int]) -> Tuple[int, int, int]:
        m = self._mat
        return (m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
                m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
                m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2])

    def conjugacy_signature(self) -> Tuple[int, int, int]:
        return (self.determinant(), self.trace(), self.order())

    def __mul__(self, other: OhElement) -> OhElement:
        return self.compose(other)

    def __eq__(self, other) -> bool:
        return self._mat == other._mat if isinstance(other, OhElement) else NotImplemented

    def __hash__(self) -> int:
        return self._hash

    def __repr__(self) -> str:
        kind = "rot" if self.determinant() == 1 else "ref"
        return f"Oh({kind},tr={self.trace()},ord={self.order()})"


# Generators of O_h
GENERATOR_RZ90 = OhElement(((0, -1, 0), (1, 0, 0), (0, 0, 1)))
GENERATOR_RX90 = OhElement(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
GENERATOR_INV  = OhElement(((-1, 0, 0), (0, -1, 0), (0, 0, -1)))
IDENTITY       = OhElement(((1, 0, 0), (0, 1, 0), (0, 0, 1)))


# ---------------------------------------------------------------------------
# OhGroup: the full 48-element octahedral symmetry group
# ---------------------------------------------------------------------------

class OhGroup:
    """
    O_h with 48 elements, Cayley table, Cayley graph distances,
    and conjugacy class decomposition.  Constructed once, shared.
    """

    _singleton = None

    @classmethod
    def instance(cls) -> OhGroup:
        """Singleton — the group only needs building once."""
        if cls._singleton is None:
            cls._singleton = cls()
        return cls._singleton

    def __init__(self):
        self.elements: List[OhElement] = []
        self.element_index: Dict[OhElement, int] = {}
        self.generators = [GENERATOR_RZ90, GENERATOR_RX90, GENERATOR_INV]
        self._generate()
        self._build_cayley_table()
        self._build_cayley_graph()
        self._classify_conjugacy()

    def _generate(self):
        seen = {IDENTITY}
        queue = [IDENTITY]
        while queue:
            g = queue.pop(0)
            for gen in self.generators:
                for h in (g.compose(gen), gen.compose(g)):
                    if h not in seen:
                        seen.add(h)
                        queue.append(h)
        self.elements = sorted(seen, key=lambda e: e.conjugacy_signature())
        self.element_index = {e: i for i, e in enumerate(self.elements)}
        assert len(self.elements) == 48

    def _build_cayley_table(self):
        n = len(self.elements)
        self.cayley_table = [[0] * n for _ in range(n)]
        for i, g in enumerate(self.elements):
            for j, h in enumerate(self.elements):
                self.cayley_table[i][j] = self.element_index[g.compose(h)]

    def _build_cayley_graph(self):
        n = len(self.elements)
        self._distances = [[-1] * n for _ in range(n)]
        for start in range(n):
            dist = [-1] * n
            dist[start] = 0
            queue = [start]
            while queue:
                cur = queue.pop(0)
                g = self.elements[cur]
                for gen in self.generators:
                    for h in (g.compose(gen), g.compose(gen.inverse())):
                        j = self.element_index[h]
                        if dist[j] == -1:
                            dist[j] = dist[cur] + 1
                            queue.append(j)
            self._distances[start] = dist

    def _classify_conjugacy(self):
        self.conjugacy_classes: Dict[Tuple, List[int]] = defaultdict(list)
        for i, e in enumerate(self.elements):
            self.conjugacy_classes[e.conjugacy_signature()].append(i)

    # --- Accessors ---

    def index(self, element: OhElement) -> int:
        return self.element_index[element]

    def multiply(self, i: int, j: int) -> int:
        return self.cayley_table[i][j]

    def inverse_index(self, i: int) -> int:
        return self.element_index[self.elements[i].inverse()]

    def distance(self, i: int, j: int) -> int:
        return self._distances[i][j]

    def max_distance(self) -> int:
        return max(max(row) for row in self._distances)

    def proper_rotations(self) -> List[int]:
        return [i for i, e in enumerate(self.elements) if e.is_proper()]

    def elements_of_order(self, n: int) -> List[int]:
        return [i for i, e in enumerate(self.elements) if e.order() == n]

    def summary(self) -> str:
        lines = [
            f"O_h: {len(self.elements)} elements, "
            f"diameter={self.max_distance()}, "
            f"{len(self.conjugacy_classes)} conjugacy classes",
        ]
        for sig, members in sorted(self.conjugacy_classes.items()):
            det, tr, order = sig
            kind = "rot" if det == 1 else "ref"
            lines.append(f"  ({kind},tr={tr},ord={order}): {len(members)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# GroupRingElement: formal sums in Z[O_h]
# ---------------------------------------------------------------------------

class GroupRingElement:
    """
    Element of Z[O_h] — a formal sum of group elements with integer
    coefficients.  Replaces GF(2) vectors with incomparably richer
    algebraic structure.
    """

    def __init__(self, group: OhGroup, coefficients: Optional[Dict[int, int]] = None):
        self.group = group
        self.coeffs: Dict[int, int] = {k: v for k, v in (coefficients or {}).items() if v != 0}

    @classmethod
    def from_element(cls, group: OhGroup, idx: int, coeff: int = 1):
        return cls(group, {idx: coeff})

    @classmethod
    def from_identity(cls, group: OhGroup):
        return cls(group, {group.index(IDENTITY): 1})

    @classmethod
    def zero(cls, group: OhGroup):
        return cls(group)

    # --- Arithmetic ---

    def add(self, other: GroupRingElement) -> GroupRingElement:
        result = dict(self.coeffs)
        for idx, c in other.coeffs.items():
            result[idx] = result.get(idx, 0) + c
            if result[idx] == 0:
                del result[idx]
        return GroupRingElement(self.group, result)

    def multiply(self, other: GroupRingElement) -> GroupRingElement:
        result: Dict[int, int] = {}
        for i, a in self.coeffs.items():
            for j, b in other.coeffs.items():
                k = self.group.multiply(i, j)
                result[k] = result.get(k, 0) + a * b
        return GroupRingElement(self.group, {k: v for k, v in result.items() if v != 0})

    def involute(self) -> GroupRingElement:
        result = {}
        for idx, c in self.coeffs.items():
            inv = self.group.inverse_index(idx)
            result[inv] = result.get(inv, 0) + c
        return GroupRingElement(self.group, {k: v for k, v in result.items() if v != 0})

    def norm_squared(self) -> int:
        return sum(c * c for c in self.coeffs.values())

    def support_size(self) -> int:
        return len(self.coeffs)

    def is_zero(self) -> bool:
        return len(self.coeffs) == 0

    def is_identity(self) -> bool:
        e_idx = self.group.index(IDENTITY)
        return self.coeffs == {e_idx: 1}

    def cayley_spread(self) -> float:
        if not self.coeffs:
            return 0.0
        e_idx = self.group.index(IDENTITY)
        total_d = sum(abs(c) * self.group.distance(e_idx, i) for i, c in self.coeffs.items())
        total_w = sum(abs(c) for c in self.coeffs.values())
        return total_d / max(total_w, 1)

    def dominant_element(self) -> Optional[int]:
        if not self.coeffs:
            return None
        return max(self.coeffs, key=lambda k: abs(self.coeffs[k]))

    def __add__(self, other): return self.add(other)
    def __mul__(self, other):
        if isinstance(other, GroupRingElement):
            return self.multiply(other)
        if isinstance(other, int):
            return GroupRingElement(self.group, {k: v * other for k, v in self.coeffs.items()})
        return NotImplemented
    def __eq__(self, other):
        return self.coeffs == other.coeffs if isinstance(other, GroupRingElement) else NotImplemented
    def __repr__(self):
        if not self.coeffs:
            return "0"
        terms = [f"{c}*g{i}" for i, c in sorted(self.coeffs.items())]
        return " + ".join(terms)


# ---------------------------------------------------------------------------
# GeometricState: a cell state that IS a symmetry operation
# ---------------------------------------------------------------------------

def _classical_to_geometric_map(group: OhGroup) -> Dict[int, int]:
    """Map classical states 0-7 to 8 maximally-spread group element indices."""
    target_vertices = [
        ( 1,  0,  0), (-1,  0,  0),
        ( 0,  1,  0), ( 0, -1,  0),
        ( 0,  0,  1), ( 0,  0, -1),
    ]
    ref = (1, 0, 0)
    mapping: Dict[int, int] = {}

    for s, target in enumerate(target_vertices):
        for i, elem in enumerate(group.elements):
            if elem.act_on_vertex(ref) == target and elem.is_proper():
                mapping[s] = i
                break
        else:
            for i, elem in enumerate(group.elements):
                if elem.act_on_vertex(ref) == target:
                    mapping[s] = i
                    break

    mapping[6] = group.index(GENERATOR_INV)
    mapping[7] = group.index(GENERATOR_INV.compose(GENERATOR_RZ90))
    return mapping


# Module-level cache
_CLASSICAL_MAP_CACHE: Dict[int, Dict[int, int]] = {}


def _get_classical_map(group: OhGroup) -> Dict[int, int]:
    gid = id(group)
    if gid not in _CLASSICAL_MAP_CACHE:
        _CLASSICAL_MAP_CACHE[gid] = _classical_to_geometric_map(group)
    return _CLASSICAL_MAP_CACHE[gid]


class GeometricState:
    """
    A mandala cell state represented as a group ring element.

    Bridges the classical 8-state SOMS world with the full 48-element
    O_h group.  Use from_classical_state() for interop with SOMSEngine.
    """

    __slots__ = ("group", "ring_element")

    def __init__(self, group: OhGroup, ring_element: GroupRingElement):
        self.group = group
        self.ring_element = ring_element

    @classmethod
    def from_pure(cls, group: OhGroup, idx: int) -> GeometricState:
        return cls(group, GroupRingElement.from_element(group, idx))

    @classmethod
    def from_classical_state(cls, group: OhGroup, classical: int) -> GeometricState:
        return cls(group, GroupRingElement.from_element(group, _get_classical_map(group)[classical % 8]))

    def compose(self, other: GeometricState) -> GeometricState:
        return GeometricState(self.group, self.ring_element * other.ring_element)

    def geometric_inverse(self) -> GeometricState:
        return GeometricState(self.group, self.ring_element.involute())

    def cayley_distance_to(self, other: GeometricState) -> float:
        d1, d2 = self.ring_element.dominant_element(), other.ring_element.dominant_element()
        if d1 is None or d2 is None:
            return 0.0
        return float(self.group.distance(d1, d2))

    def energy(self) -> float:
        return self.ring_element.cayley_spread()

    def is_pure(self) -> bool:
        return self.ring_element.support_size() == 1

    def to_classical(self) -> int:
        vertex_map = _get_classical_map(self.group)
        dominant = self.ring_element.dominant_element()
        if dominant is None:
            return 0
        best_state, best_dist = 0, float("inf")
        for classical, geo_idx in vertex_map.items():
            d = self.group.distance(dominant, geo_idx)
            if d < best_dist:
                best_dist = d
                best_state = classical
        return best_state

    def __repr__(self):
        if self.is_pure():
            return f"GeoState(classical~{self.to_classical()})"
        return f"GeoState(support={self.ring_element.support_size()})"


# ---------------------------------------------------------------------------
# CayleyEnergy: coupling via Cayley graph distance — SOMS Pathway C
# ---------------------------------------------------------------------------

class CayleyEnergy:
    """
    Cayley-graph coupling energy for SOMS cells.

    Replaces |s_i - s_j| with the true geometric distance between
    symmetry operations in O_h.  Integrates as a third pathway
    alongside angular (A) and tensor (B).

    E_cayley = J * (φ · d_cayley / diameter)²
    """

    def __init__(self, group: OhGroup, coupling_strength: float = 1.0):
        self.group = group
        self.coupling_strength = coupling_strength
        self._diameter = group.max_distance()

    def pairwise_energy(self, state_a: GeometricState, state_b: GeometricState) -> float:
        d = state_a.cayley_distance_to(state_b)
        norm = d / max(self._diameter, 1)
        return self.coupling_strength * (PHI * norm) ** 2

    def composition_energy(self, state_a: GeometricState, state_b: GeometricState) -> float:
        return state_a.compose(state_b).energy()

    def cancellation_residual(self, state_a: GeometricState, state_b: GeometricState) -> float:
        product = state_a.ring_element.multiply(state_b.ring_element.involute())
        return 0.0 if product.is_identity() else product.cayley_spread()

    def total_energy(self, states: List[GeometricState],
                     neighbors: List[Tuple[int, int]]) -> float:
        total = sum(s.energy() for s in states)
        for i, j in neighbors:
            total += self.pairwise_energy(states[i], states[j])
        return total

    def cayley_distance_matrix(self, classical_states) -> List[List[int]]:
        """Build NxN Cayley distance matrix from classical state indices."""
        geo = [GeometricState.from_classical_state(self.group, int(s)) for s in classical_states]
        n = len(geo)
        mat = [[0] * n for _ in range(n)]
        for i in range(n):
            di = geo[i].ring_element.dominant_element()
            for j in range(i + 1, n):
                dj = geo[j].ring_element.dominant_element()
                d = self.group.distance(di, dj) if (di is not None and dj is not None) else 0
                mat[i][j] = mat[j][i] = d
        return mat
