"""\nGEOMETRIC STATE ALGEBRA v1.0\nReplace flat integer states with the full octahedral symmetry group O_h.\n\nInstead of states 0-7 (integers that happen to be labeled geometrically),\nstates ARE symmetry operations: rotations and reflections of the octahedron.\nCancellation is group composition to identity. The algebraic structure is\nthe group ring Z[O_h] -- fundamentally richer than GF(2).\n\nKey insight: the octahedral group O_h has 48 elements (24 rotations x {I, -I}).\nThe current system collapses this to 8 states, losing 40 dimensions of\ngeometric information. This module restores them.\n\nCore types:\nOhElement      -- single symmetry operation (3x3 integer matrix)\nOhGroup        -- the full 48-element group with Cayley graph\nGroupRingElement -- formal sum in Z[O_h], the geometric superposition\nGeometricState -- cell state that IS a group element\nCayleyEnergy   -- coupling energy from Cayley graph distance\n\nDesign:\n- All matrices are exact integers (-1, 0, 1) -- no floating point\n- Group multiplication is matrix multiplication\n- Inverses are transposes (orthogonal group)\n- Cayley distance replaces |s_i - s_j|\n- Group ring replaces GF(2) for null space analysis\n"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional, Set, FrozenSet
from dataclasses import dataclass, field
from collections import defaultdict
import math

PHI = (1 + math.sqrt(5)) / 2


# ---------------------------------------------------------------------------
# OhElement: a single symmetry operation
# ---------------------------------------------------------------------------

class OhElement:
    """\nAn element of the octahedral symmetry group O_h.\n\nRepresented as a 3x3 integer matrix (all entries in {-1, 0, 1}).\nThese are exact -- no floating point, no approximation.\n\nThe octahedron has 6 vertices at (+-1,0,0), (0,+-1,0), (0,0,+-1).\nEach symmetry operation permutes these vertices, encoded as the\nmatrix that performs the permutation on R^3.\n"""

    __slots__ = ("_mat", "_hash")

    def __init__(self, matrix: Tuple[Tuple[int, ...], ...]):
        self._mat = tuple(tuple(int(x) for x in row) for row in matrix)
        self._hash = hash(self._mat)

    @property
    def matrix(self) -> Tuple[Tuple[int, ...], ...]:
        return self._mat

    def compose(self, other: OhElement) -> OhElement:
        """Group operation: matrix multiplication (exact integer)."""
        a, b = self._mat, other._mat
        result = []
        for i in range(3):
            row = []
            for j in range(3):
                s = 0
                for k in range(3):
                    s += a[i][k] * b[k][j]
                row.append(s)
            result.append(tuple(row))
        return OhElement(tuple(result))

    def inverse(self) -> OhElement:
        """Inverse = transpose (all elements of O_h are orthogonal)."""
        m = self._mat
        return OhElement((
            (m[0][0], m[1][0], m[2][0]),
            (m[0][1], m[1][1], m[2][1]),
            (m[0][2], m[1][2], m[2][2]),
        ))

    def is_identity(self) -> bool:
        return self._mat == ((1,0,0),(0,1,0),(0,0,1))

    def is_proper(self) -> bool:
        """True if this is a proper rotation (det = +1), not a reflection."""
        return self.determinant() == 1

    def determinant(self) -> int:
        m = self._mat
        return (m[0][0] * (m[1][1]*m[2][2] - m[1][2]*m[2][1])
              - m[0][1] * (m[1][0]*m[2][2] - m[1][2]*m[2][0])
              + m[0][2] * (m[1][0]*m[2][1] - m[1][1]*m[2][0]))

    def order(self) -> int:
        """Order of this element: smallest n such that g^n = identity."""
        current = self
        for n in range(1, 49):
            if current.is_identity():
                return n
            current = current.compose(self)
        return 48  # safety

    def trace(self) -> int:
        return self._mat[0][0] + self._mat[1][1] + self._mat[2][2]

    def conjugacy_signature(self) -> Tuple[int, int, int, int]:
        """(determinant, trace, order, fixed_vertices) -- identifies the conjugacy class."""
        fixed = sum(1 for v in OCTAHEDRAL_VERTICES if self.act_on_vertex(v) == v)
        return (self.determinant(), self.trace(), self.order(), fixed)

    def act_on_vertex(self, v: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Apply this symmetry to an octahedral vertex."""
        m = self._mat
        return (
            m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
            m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
            m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2],
        )

    def __mul__(self, other: OhElement) -> OhElement:
        return self.compose(other)

    def __eq__(self, other) -> bool:
        if isinstance(other, OhElement):
            return self._mat == other._mat
        return NotImplemented

    def __hash__(self) -> int:
        return self._hash

    def __repr__(self) -> str:
        det = self.determinant()
        tr = self.trace()
        kind = "rot" if det == 1 else "ref"
        return f"Oh({kind},tr={tr},ord={self.order()})"

    def __str__(self) -> str:
        rows = ["[" + ",".join(f"{x:+d}" for x in row) + "]" for row in self._mat]
        return "[" + "; ".join(rows) + "]"


# ---------------------------------------------------------------------------
# OhGroup: the full 48-element octahedral symmetry group
# ---------------------------------------------------------------------------

# The 6 vertices of the octahedron
OCTAHEDRAL_VERTICES = (
    ( 1,  0,  0),
    (-1,  0,  0),
    ( 0,  1,  0),
    ( 0, -1,  0),
    ( 0,  0,  1),
    ( 0,  0, -1),
)

# Generators of O_h:
#   Rz90: 90-degree rotation about z-axis
#   Rx90: 90-degree rotation about x-axis
#   Inv:  spatial inversion (improper)
GENERATOR_RZ90 = OhElement(((0, -1, 0), (1, 0, 0), (0, 0, 1)))
GENERATOR_RX90 = OhElement(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
GENERATOR_INV  = OhElement(((-1, 0, 0), (0, -1, 0), (0, 0, -1)))
IDENTITY       = OhElement(((1, 0, 0), (0, 1, 0), (0, 0, 1)))


class OhGroup:
    """\nThe octahedral symmetry group O_h with 48 elements.\n\nGenerated from three generators: Rz90, Rx90, and inversion.\nProvides:\n- Complete element list with stable indexing\n- Multiplication (Cayley) table\n- Cayley graph with generator distances\n- Conjugacy class decomposition\n- Subgroup lattice (octahedral rotations O, tetra T_d, etc.)\n"""

    def __init__(self):
        self.elements: List[OhElement] = []
        self.element_index: Dict[OhElement, int] = {}
        self.generators = [GENERATOR_RZ90, GENERATOR_RX90, GENERATOR_INV]
        self.generator_names = ["Rz90", "Rx90", "Inv"]

        self._generate()
        self._build_cayley_table()
        self._build_cayley_graph()
        self._classify_conjugacy()

    def _generate(self):
        """Generate all 48 elements by closure under generators."""
        seen: Set[OhElement] = {IDENTITY}
        queue = [IDENTITY]

        while queue:
            g = queue.pop(0)
            for gen in self.generators:
                for h in [g.compose(gen), gen.compose(g)]:
                    if h not in seen:
                        seen.add(h)
                        queue.append(h)

        # Sort by (det, trace, order) for stable indexing
        self.elements = sorted(seen, key=lambda e: e.conjugacy_signature())
        self.element_index = {e: i for i, e in enumerate(self.elements)}

        assert len(self.elements) == 48, f"Expected 48, got {len(self.elements)}"

    def _build_cayley_table(self):
        """Precompute the full multiplication table."""
        n = len(self.elements)
        self.cayley_table = [[0] * n for _ in range(n)]
        for i, g in enumerate(self.elements):
            for j, h in enumerate(self.elements):
                product = g.compose(h)
                self.cayley_table[i][j] = self.element_index[product]

    def _build_cayley_graph(self):
        """\nBuild Cayley graph: nodes are group elements, edges connect\nelements that differ by one generator application.\n\nThe distance in this graph is the geometric notion of\n"how different" two symmetry operations are.\n"""
        n = len(self.elements)
        # BFS from identity to compute distances to all elements
        self._distances = [[-1] * n for _ in range(n)]

        # Distance from each element (BFS)
        gen_indices = []
        for gen in self.generators:
            gen_indices.append(self.element_index[gen])
            inv = gen.inverse()
            if inv != gen:
                gen_indices.append(self.element_index[inv])

        for start in range(n):
            dist = [-1] * n
            dist[start] = 0
            queue = [start]
            while queue:
                current = queue.pop(0)
                g = self.elements[current]
                for gen in self.generators:
                    for h in [g.compose(gen), g.compose(gen.inverse())]:
                        j = self.element_index[h]
                        if dist[j] == -1:
                            dist[j] = dist[current] + 1
                            queue.append(j)
            self._distances[start] = dist

    def _classify_conjugacy(self):
        """\nDecompose into conjugacy classes.\n\nO_h has 10 conjugacy classes:\nProper (det=+1): E, 6C4, 3C4^2, 8C3, 6C2\nImproper (det=-1): i, 6S4, 3sigma_h, 8S6, 6sigma_d\n"""
        self.conjugacy_classes: Dict[Tuple, List[int]] = defaultdict(list)
        for i, e in enumerate(self.elements):
            sig = e.conjugacy_signature()
            self.conjugacy_classes[sig].append(i)

    # --- Accessors ---

    def identity(self) -> OhElement:
        return IDENTITY

    def index(self, element: OhElement) -> int:
        return self.element_index[element]

    def multiply(self, i: int, j: int) -> int:
        """Multiply elements by index, return product index."""
        return self.cayley_table[i][j]

    def inverse_index(self, i: int) -> int:
        """Index of the inverse of element i."""
        inv = self.elements[i].inverse()
        return self.element_index[inv]

    def distance(self, i: int, j: int) -> int:
        """Cayley graph distance between elements i and j."""
        return self._distances[i][j]

    def max_distance(self) -> int:
        """Diameter of the Cayley graph."""
        return max(max(row) for row in self._distances)

    # --- Subgroups ---

    def proper_rotations(self) -> List[int]:
        """Indices of the 24 proper rotations (subgroup O)."""
        return [i for i, e in enumerate(self.elements) if e.is_proper()]

    def improper_elements(self) -> List[int]:
        """Indices of the 24 improper rotations (reflections, inversions)."""
        return [i for i, e in enumerate(self.elements) if not e.is_proper()]

    def elements_of_order(self, n: int) -> List[int]:
        """All elements with the given order."""
        return [i for i, e in enumerate(self.elements) if e.order() == n]

    # --- Vertex action ---

    def vertex_orbit(self, element_idx: int) -> Dict[Tuple, Tuple]:
        """How element_idx permutes the 6 octahedral vertices."""
        g = self.elements[element_idx]
        return {v: g.act_on_vertex(v) for v in OCTAHEDRAL_VERTICES}

    def stabilizer(self, vertex: Tuple[int,int,int]) -> List[int]:
        """Elements that fix a given vertex."""
        return [i for i, e in enumerate(self.elements)
                if e.act_on_vertex(vertex) == vertex]

    def summary(self) -> str:
        """Human-readable group summary."""
        lines = [
            f"Octahedral group O_h: {len(self.elements)} elements",
            f"  Generators: {', '.join(self.generator_names)}",
            f"  Proper rotations (O): {len(self.proper_rotations())}",
            f"  Improper elements: {len(self.improper_elements())}",
            f"  Cayley diameter: {self.max_distance()}",
            f"  Conjugacy classes: {len(self.conjugacy_classes)}",
        ]
        for sig, members in sorted(self.conjugacy_classes.items()):
            det, tr, order, fixed = sig
            kind = "rot" if det == 1 else "ref"
            lines.append(f"    ({kind}, tr={tr}, ord={order}, fix={fixed}): {len(members)} elements")
        return "\n".join(lines)



# ---------------------------------------------------------------------------
# GroupRingElement: formal sums in Z[O_h]
# ---------------------------------------------------------------------------

class GroupRingElement:
    """\nAn element of the group ring Z[O_h].\n\nThis is a formal sum: a_0*g_0 + a_1*g_1 + ... + a_47*g_47\nwhere a_i are integers and g_i are group elements.\n\nThis replaces GF(2) vectors. Instead of binary coefficients over\na 2-element field, we have integer coefficients over a 48-element group.\nThe algebraic structure is incomparably richer.\n\nOperations:\n- Addition: (sum a_i*g_i) + (sum b_i*g_i) = sum (a_i+b_i)*g_i\n- Multiplication (convolution):\n(sum a_g*g)(sum b_h*h) = sum a_g*b_h*(g*h)\n- This is non-commutative (group multiplication isn't commutative)\n"""

    def __init__(self, group: OhGroup, coefficients: Optional[Dict[int, int]] = None):
        self.group = group
        # Sparse representation: only store non-zero coefficients
        self.coeffs: Dict[int, int] = {}
        if coefficients:
            for idx, coeff in coefficients.items():
                if coeff != 0:
                    self.coeffs[idx] = coeff

    @classmethod
    def from_element(cls, group: OhGroup, element_idx: int, coeff: int = 1) -> GroupRingElement:
        """Create a ring element from a single group element."""
        return cls(group, {element_idx: coeff})

    @classmethod
    def from_identity(cls, group: OhGroup) -> GroupRingElement:
        """The identity of the group ring (1 * e)."""
        e_idx = group.index(IDENTITY)
        return cls(group, {e_idx: 1})

    @classmethod
    def zero(cls, group: OhGroup) -> GroupRingElement:
        """The zero element of the group ring."""
        return cls(group)

    @classmethod
    def from_conjugacy_class(cls, group: OhGroup, signature: Tuple) -> GroupRingElement:
        """Sum of all elements in a conjugacy class (central element)."""
        if signature in group.conjugacy_classes:
            coeffs = {idx: 1 for idx in group.conjugacy_classes[signature]}
            return cls(group, coeffs)
        return cls.zero(group)

    # --- Arithmetic ---

    def add(self, other: GroupRingElement) -> GroupRingElement:
        """Ring addition: pointwise sum of coefficients."""
        result = dict(self.coeffs)
        for idx, coeff in other.coeffs.items():
            result[idx] = result.get(idx, 0) + coeff
            if result[idx] == 0:
                del result[idx]
        return GroupRingElement(self.group, result)

    def subtract(self, other: GroupRingElement) -> GroupRingElement:
        """Ring subtraction."""
        result = dict(self.coeffs)
        for idx, coeff in other.coeffs.items():
            result[idx] = result.get(idx, 0) - coeff
            if result[idx] == 0:
                del result[idx]
        return GroupRingElement(self.group, result)

    def multiply(self, other: GroupRingElement) -> GroupRingElement:
        """\nRing multiplication (convolution).\n\n(sum a_g * g)(sum b_h * h) = sum_{g,h} a_g * b_h * (g*h)\n\nThis is the KEY operation that replaces XOR.\nWhen a*b = identity element of Z[O_h], we have geometric cancellation.\n"""
        result: Dict[int, int] = {}
        for i, a in self.coeffs.items():
            for j, b in other.coeffs.items():
                product_idx = self.group.multiply(i, j)
                result[product_idx] = result.get(product_idx, 0) + a * b
        # Clean zeros
        return GroupRingElement(self.group, {k: v for k, v in result.items() if v != 0})

    def scale(self, n: int) -> GroupRingElement:
        """Scalar multiplication by integer."""
        if n == 0:
            return GroupRingElement.zero(self.group)
        return GroupRingElement(self.group, {k: v * n for k, v in self.coeffs.items()})

    def involute(self) -> GroupRingElement:
        """\nInvolution: replace each g with g^{-1}.\nThis is the group ring analog of complex conjugation.\n"""
        result = {}
        for idx, coeff in self.coeffs.items():
            inv_idx = self.group.inverse_index(idx)
            result[inv_idx] = result.get(inv_idx, 0) + coeff
        return GroupRingElement(self.group, {k: v for k, v in result.items() if v != 0})

    def norm_squared(self) -> int:
        """\n||x||^2 = sum of squared coefficients.\nThe group ring analog of vector magnitude.\n"""
        return sum(c * c for c in self.coeffs.values())

    def support_size(self) -> int:
        """Number of non-zero coefficients."""
        return len(self.coeffs)

    def is_zero(self) -> bool:
        return len(self.coeffs) == 0

    def is_identity(self) -> bool:
        """Is this 1*e (the ring identity)?"""
        e_idx = self.group.index(IDENTITY)
        return self.coeffs == {e_idx: 1}

    def is_geometric_inverse_of(self, other: GroupRingElement) -> bool:
        """\nCheck if self * other = identity in the group ring.\n\nThis is the geometric replacement for XOR cancellation.\nTwo states cancel geometrically when their composition\nequals the identity element of Z[O_h].\n"""
        product = self.multiply(other)
        return product.is_identity()

    # --- Analysis ---

    def cayley_spread(self) -> float:
        """\nAverage Cayley distance of support elements from identity.\nMeasures how 'spread out' this element is in the group.\n"""
        if not self.coeffs:
            return 0.0
        e_idx = self.group.index(IDENTITY)
        total_dist = 0
        total_weight = 0
        for idx, coeff in self.coeffs.items():
            w = abs(coeff)
            total_dist += w * self.group.distance(e_idx, idx)
            total_weight += w
        return total_dist / max(total_weight, 1)

    def geometric_entropy(self) -> float:
        """\nShannon entropy of the coefficient distribution.\nMeasures how 'spread out' the element is across the group.\n0 = concentrated on one element, log(48) = uniform.\n"""
        total = sum(abs(c) for c in self.coeffs.values())
        if total == 0:
            return 0.0
        entropy = 0.0
        for c in self.coeffs.values():
            p = abs(c) / total
            if p > 0:
                entropy -= p * math.log(p)
        return entropy

    def dominant_element(self) -> Optional[int]:
        """Index of the group element with largest |coefficient|."""
        if not self.coeffs:
            return None
        return max(self.coeffs.keys(), key=lambda k: abs(self.coeffs[k]))

    # --- Operators ---

    def __add__(self, other: GroupRingElement) -> GroupRingElement:
        return self.add(other)

    def __sub__(self, other: GroupRingElement) -> GroupRingElement:
        return self.subtract(other)

    def __mul__(self, other):
        if isinstance(other, GroupRingElement):
            return self.multiply(other)
        if isinstance(other, int):
            return self.scale(other)
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, int):
            return self.scale(other)
        return NotImplemented

    def __eq__(self, other) -> bool:
        if isinstance(other, GroupRingElement):
            return self.coeffs == other.coeffs
        return NotImplemented

    def __repr__(self) -> str:
        if not self.coeffs:
            return "0"
        terms = []
        for idx in sorted(self.coeffs.keys()):
            c = self.coeffs[idx]
            e = self.group.elements[idx]
            if c == 1:
                terms.append(repr(e))
            elif c == -1:
                terms.append(f"-{repr(e)}")
            else:
                terms.append(f"{c}*{repr(e)}")
        return " + ".join(terms)



# ---------------------------------------------------------------------------
# GeometricState: a cell state that IS a symmetry operation
# ---------------------------------------------------------------------------

class GeometricState:
    """\nA mandala cell state represented as a group ring element.\n\nInstead of state = 3 (an integer), a state is now a specific\nrotation/reflection of the octahedron, or a superposition of several.\n\nThis is the fundamental upgrade: states carry geometric structure.\n"""

    def __init__(self, group: OhGroup, ring_element: GroupRingElement):
        self.group = group
        self.ring_element = ring_element

    @classmethod
    def from_pure_rotation(cls, group: OhGroup, element_idx: int) -> GeometricState:
        """A state that is a single definite symmetry operation."""
        return cls(group, GroupRingElement.from_element(group, element_idx))

    @classmethod
    def from_superposition(cls, group: OhGroup, weights: Dict[int, int]) -> GeometricState:
        """A state that is a weighted sum of symmetry operations."""
        return cls(group, GroupRingElement(group, weights))

    @classmethod
    def from_classical_state(cls, group: OhGroup, classical_state: int) -> GeometricState:
        """\nBridge: convert a classical state (0-7) to a geometric state.\n\nMaps the 8 classical states to the 8 vertices of the octahedron,\nthen to the rotation that carries the +x vertex to that vertex.\n\nClassical state -> Octahedral vertex -> Stabilizing rotation\n0 -> (+1,0,0) -> identity\n1 -> (-1,0,0) -> 180 deg rotation about y\n2 -> (0,+1,0) -> 90 deg rotation about z\n3 -> (0,-1,0) -> -90 deg rotation about z\n4 -> (0,0,+1) -> -90 deg rotation about y (then conceptual map)\n5 -> (0,0,-1) -> 90 deg rotation about y\n6 -> inversion\n7 -> inversion composed with Rz90\n"""
        # Map classical states to specific group elements
        # We pick 8 elements that span different conjugacy classes
        vertex_map = _classical_to_geometric_map(group)
        idx = vertex_map[classical_state % 8]
        return cls(group, GroupRingElement.from_element(group, idx))

    def compose(self, other: GeometricState) -> GeometricState:
        """\nGeometric composition of two states.\nThis replaces XOR and all binary operations.\n"""
        return GeometricState(self.group, self.ring_element * other.ring_element)

    def geometric_inverse(self) -> GeometricState:
        """The state that cancels this one (composition = identity)."""
        return GeometricState(self.group, self.ring_element.involute())

    def cancels_with(self, other: GeometricState) -> bool:
        """\nTrue if composing self with other yields identity.\nThis is the geometric replacement for state_a ^ state_b == 0.\n"""
        return self.ring_element.is_geometric_inverse_of(other.ring_element)

    def cayley_distance_to(self, other: GeometricState) -> float:
        """\nDistance between two states in the Cayley graph.\n\nReplaces |s_i - s_j| with a geometrically meaningful metric.\nTwo states that are many generators apart are truly different;\ntwo that differ by one generator are geometrically adjacent.\n"""
        d1 = self.ring_element.dominant_element()
        d2 = other.ring_element.dominant_element()
        if d1 is None or d2 is None:
            return 0.0
        return float(self.group.distance(d1, d2))

    def energy(self) -> float:
        """\nSelf-energy based on distance from identity.\nPure identity = 0 energy (ground state).\nFurther from identity = higher energy.\n"""
        return self.ring_element.cayley_spread()

    def is_pure(self) -> bool:
        """True if this state is a single group element, not a superposition."""
        return self.ring_element.support_size() == 1

    def to_classical(self) -> int:
        """\nProject back to classical state (0-7) by finding the nearest\nof the 8 mapped elements.\n"""
        vertex_map = _classical_to_geometric_map(self.group)
        dominant = self.ring_element.dominant_element()
        if dominant is None:
            return 0

        # Find which classical state this element is closest to
        best_state = 0
        best_dist = float("inf")
        for classical, geo_idx in vertex_map.items():
            d = self.group.distance(dominant, geo_idx)
            if d < best_dist:
                best_dist = d
                best_state = classical
        return best_state

    def __repr__(self) -> str:
        if self.is_pure():
            dominant = self.ring_element.dominant_element()
            return f"GeoState({self.group.elements[dominant]}; classical~{self.to_classical()})"
        return f"GeoState(support={self.ring_element.support_size()}, entropy={self.ring_element.geometric_entropy():.2f})"


def _classical_to_geometric_map(group: OhGroup) -> Dict[int, int]:
    """\nMap classical states 0-7 to group element indices.\n\nStrategy: pick 8 elements that maximally span the group,\none from each distinct conjugacy class type where possible.\nThis ensures the 8 states are geometrically distinct.\n"""
    # Use vertex permutations: each classical state maps to the rotation
    # that sends vertex (+1,0,0) to the corresponding octahedral vertex.
    target_vertices = [
        ( 1,  0,  0),  # state 0: identity
        (-1,  0,  0),  # state 1: inversion of x
        ( 0,  1,  0),  # state 2: rotate to +y
        ( 0, -1,  0),  # state 3: rotate to -y
        ( 0,  0,  1),  # state 4: rotate to +z
        ( 0,  0, -1),  # state 5: rotate to -z
    ]

    ref_vertex = (1, 0, 0)
    mapping = {}

    for state_idx, target in enumerate(target_vertices):
        # Find the group element that maps ref_vertex -> target
        for i, elem in enumerate(group.elements):
            if elem.act_on_vertex(ref_vertex) == target and elem.is_proper():
                mapping[state_idx] = i
                break
        else:
            # Fallback: accept improper too
            for i, elem in enumerate(group.elements):
                if elem.act_on_vertex(ref_vertex) == target:
                    mapping[state_idx] = i
                    break

    # States 6,7: use inversion and one more improper element
    inv_idx = group.index(GENERATOR_INV)
    mapping[6] = inv_idx

    # State 7: inversion composed with Rz90
    inv_rz = GENERATOR_INV.compose(GENERATOR_RZ90)
    mapping[7] = group.index(inv_rz)

    return mapping



# ---------------------------------------------------------------------------
# CayleyEnergy: coupling energy from Cayley graph distance
# ---------------------------------------------------------------------------

class CayleyEnergy:
    """\nEnergy model using Cayley graph distance instead of |s_i - s_j|.\n\nThe Cayley graph of O_h encodes the true geometric distance between\nsymmetry operations. States that are one generator apart are adjacent;\nstates that require many generators are distant.\n\nThis replaces:\nE_coupling = J * sin(|s_i - s_j| * pi/4)^2\n\nWith:\nE_coupling = J * f(cayley_distance(g_i, g_j))\n\nwhere f is a monotone function of the Cayley distance.\n"""

    def __init__(self, group: OhGroup, coupling_strength: float = 1.0):
        self.group = group
        self.coupling_strength = coupling_strength
        self._diameter = group.max_distance()

    def coupling_energy(self, state_a: GeometricState, state_b: GeometricState) -> float:
        """\nCoupling energy between two geometric states.\n\nUses normalized Cayley distance with phi-weighted scaling.\nStates that are far apart in the Cayley graph contribute\nmore coupling energy.\n"""
        d = state_a.cayley_distance_to(state_b)
        normalized = d / max(self._diameter, 1)
        # Phi-weighted coupling: energy rises as golden ratio power of distance
        return self.coupling_strength * (PHI * normalized) ** 2

    def composition_energy(self, state_a: GeometricState, state_b: GeometricState) -> float:
        """\nEnergy of the composition state_a * state_b.\n\nMeasures how far the composition is from identity.\nIf the composition IS identity, energy is zero (cancellation).\n"""
        composed = state_a.compose(state_b)
        return composed.energy()

    def cancellation_residual(self, state_a: GeometricState, state_b: GeometricState) -> float:
        """\nHow close are these states to mutual cancellation?\n\n0.0 = perfect cancellation (a*b = identity)\nHigher = further from cancellation\n\nThis replaces checking state_a ^ state_b == 0.\n"""
        product = state_a.ring_element.multiply(state_b.ring_element.involute())
        if product.is_identity():
            return 0.0
        # Distance of product from identity
        return product.cayley_spread()

    def factorization_energy(self, states_a: List[GeometricState],
                             states_b: List[GeometricState],
                             N: int) -> float:
        """\nEnergy for factorization in geometric state space.\n\nFactor registers are lists of geometric states.\nEach state is projected to a classical digit (0-7),\nthen assembled positionally in base-8.\n\nThe energy is (fa*fb - N)^2, but now factors live in\nthe full geometric space and only project to integers\nat the measurement step.\n"""
        # Project to classical for factor computation
        fa = 2
        for i, s in enumerate(states_a):
            fa += s.to_classical() * (8 ** i)

        fb = 2
        for i, s in enumerate(states_b):
            fb += s.to_classical() * (8 ** i)

        return float((fa * fb - N) ** 2)

    def total_energy(self, states: List[GeometricState],
                     neighbors: List[Tuple[int, int]]) -> float:
        """\nTotal energy of a geometric configuration.\n\nE = sum(self_energy) + sum(coupling_energy over neighbor pairs)\n"""
        total = 0.0
        # Self-energy: distance from identity
        for s in states:
            total += s.energy()
        # Coupling energy: Cayley distance between neighbors
        for i, j in neighbors:
            total += self.coupling_energy(states[i], states[j])
        return total


# ---------------------------------------------------------------------------
# PrimeVertex: primes inhabit octahedral vertices natively
# ---------------------------------------------------------------------------

class PrimeVertex:
    """\nMap primes to octahedral symmetry operations.\n\nInstead of primes getting flat integer indices (2->0, 3->1, 5->2, ...),\nprimes are assigned to specific rotations/reflections based on their\ngeometric character.\n\nSmall primes map to vertices (order-2 rotations):\n2 -> 180 deg rotation about x (simplest nontrivial symmetry)\n3 -> 120 deg rotation about body diagonal (first odd prime = 3-fold)\n5 -> 72 deg-like operation (5-fold connection to phi)\n7 -> 360/7... mapped to highest-order proper rotation available\n\nThe assignment respects:\n- Prime 2 -> involutions (order 2 elements)\n- Prime 3 -> order 3 elements\n- Prime p -> elements whose order resonates with p\n"""

    def __init__(self, group: OhGroup):
        self.group = group
        self._prime_map: Dict[int, int] = {}
        self._build_prime_map()

    def _build_prime_map(self):
        """Assign primes to group elements by order resonance."""
        orders = {}
        for i, e in enumerate(self.group.elements):
            o = e.order()
            if o not in orders:
                orders[o] = []
            orders[o].append(i)

        # Prime 2 -> order-2 elements (involutions)
        if 2 in orders and orders[2]:
            self._prime_map[2] = orders[2][0]

        # Prime 3 -> order-3 elements (3-fold rotations)
        if 3 in orders and orders[3]:
            self._prime_map[3] = orders[3][0]

        # Prime 5 -> no order-5 in O_h, use order-4 (closest resonance via phi)
        if 4 in orders and orders[4]:
            self._prime_map[5] = orders[4][0]

        # Prime 7 -> order-6 elements (if available, else order-4)
        if 6 in orders and orders[6]:
            self._prime_map[7] = orders[6][0]
        elif 4 in orders and len(orders[4]) > 1:
            self._prime_map[7] = orders[4][1]

        # For larger primes, cycle through available elements
        available = [i for i in range(len(self.group.elements))
                     if i not in self._prime_map.values()
                     and not self.group.elements[i].is_identity()]

        prime_idx = 0
        p = 11
        while prime_idx < len(available) and p < 200:
            if self._is_prime(p):
                self._prime_map[p] = available[prime_idx]
                prime_idx += 1
            p += 2

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2: return False
        if n < 4: return True
        if n % 2 == 0: return False
        d = 3
        while d * d <= n:
            if n % d == 0: return False
            d += 2
        return True

    def prime_to_element(self, p: int) -> Optional[int]:
        """Get the group element index for a prime."""
        return self._prime_map.get(p)

    def prime_to_state(self, p: int) -> Optional[GeometricState]:
        """Get the geometric state for a prime."""
        idx = self.prime_to_element(p)
        if idx is not None:
            return GeometricState.from_pure_rotation(self.group, idx)
        return None

    def factor_pair_geometric(self, N: int) -> Optional[Tuple[GeometricState, GeometricState]]:
        """\nExpress N = p * q as a pair of geometric states.\n\nThe factorization is geometric: two symmetry operations\nwhose composition encodes the number.\n"""
        # Trial division
        for p in range(2, int(math.isqrt(N)) + 1):
            if N % p == 0:
                q = N // p
                ps = self.prime_to_state(p)
                qs = self.prime_to_state(q)
                if ps and qs:
                    return (ps, qs)
        return None

    def summary(self) -> str:
        lines = ["Prime -> Octahedral Vertex Map:"]
        for p in sorted(self._prime_map.keys()):
            idx = self._prime_map[p]
            elem = self.group.elements[idx]
            lines.append(f"  {p:>3d} -> element {idx:>2d}: {elem} (order {elem.order()}, {'proper' if elem.is_proper() else 'improper'})")
        return "\n".join(lines)



# ---------------------------------------------------------------------------
# GeometricNullSpace: replaces GF(2) null space with group ring kernel
# ---------------------------------------------------------------------------

class GeometricNullSpace:
    """\nThe group ring analog of the GF(2) null space.\n\nIn the binary framework, we look for vectors v such that M*v = 0 over GF(2).\nIn the geometric framework, we look for group ring elements x such that\nA*x = identity in Z[O_h], where A encodes the constraint matrix.\n\nThe null space of a group ring homomorphism is a Z[O_h]-module,\nwhich has far richer structure than a GF(2) vector space.\n"""

    def __init__(self, group: OhGroup):
        self.group = group
        self.constraints: List[GroupRingElement] = []
        self.kernel: List[GroupRingElement] = []

    def add_constraint(self, constraint: GroupRingElement):
        """Add a constraint that solutions must satisfy."""
        self.constraints.append(constraint)

    def find_kernel_elements(self, max_search: int = 100) -> List[GroupRingElement]:
        """\nFind elements x such that c * x = identity for each constraint c.\n\nFor single group elements, the kernel element is simply the inverse.\nFor superpositions, we search for approximate inverses.\n"""
        self.kernel = []

        for constraint in self.constraints:
            if constraint.support_size() == 1:
                # Pure element: inverse is exact
                inv = constraint.involute()
                self.kernel.append(inv)
            else:
                # Superposition: search for best approximate inverse
                best = None
                best_residual = float("inf")

                # Try all single elements
                for i in range(len(self.group.elements)):
                    candidate = GroupRingElement.from_element(self.group, i)
                    product = constraint.multiply(candidate)

                    # How close is product to identity?
                    e_idx = self.group.index(IDENTITY)
                    if product.coeffs.get(e_idx, 0) > 0:
                        # Has identity component -- measure residual
                        residual = sum(abs(c) for idx, c in product.coeffs.items()
                                      if idx != e_idx)
                        if residual < best_residual:
                            best_residual = residual
                            best = candidate

                if best is not None:
                    self.kernel.append(best)

        return self.kernel

    def null_space_dimension(self) -> int:
        """\nDimension of the null space.\n\nIn GF(2), this is a simple integer.\nIn Z[O_h], the dimension is a rank over Z[O_h] as a module.\nWe approximate by counting independent kernel elements.\n"""
        return len(self.kernel)

    def summary(self) -> str:
        lines = [f"Geometric Null Space: {len(self.constraints)} constraints"]
        lines.append(f"  Kernel dimension: {len(self.kernel)}")
        for i, k in enumerate(self.kernel):
            lines.append(f"  Kernel element {i}: support={k.support_size()}, ")
            lines.append(f"    spread={k.cayley_spread():.2f}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# ScentTrail: energy gradients on the octahedral lattice
# ---------------------------------------------------------------------------

class ScentTrail:
    """\nNavigate the octahedral lattice via energy gradients.\n\nInstead of searching in binary, follow energy gradients\non the Cayley graph. Each step moves to an adjacent group\nelement that lowers energy most.\n\nThis is the geometric analog of steepest descent,\nbut the descent happens on the group manifold.\n"""

    def __init__(self, group: OhGroup, energy_fn):
        """\nArgs:\ngroup: the octahedral group\nenergy_fn: callable(GeometricState) -> float\n"""
        self.group = group
        self.energy_fn = energy_fn
        self.trail: List[Tuple[int, float]] = []  # (element_idx, energy)

    def descend(self, start: GeometricState, max_steps: int = 100,
                temperature: float = 0.0) -> GeometricState:
        """\nGeometric gradient descent on the Cayley graph.\n\nAt each step, evaluate energy at all generator-adjacent states.\nMove to the lowest-energy neighbor (or accept higher energy\nwith Boltzmann probability if temperature > 0).\n"""
        current_idx = start.ring_element.dominant_element()
        if current_idx is None:
            return start

        current_energy = self.energy_fn(start)
        self.trail = [(current_idx, current_energy)]

        import random

        for _ in range(max_steps):
            # Enumerate generator-adjacent elements
            neighbors = []
            g = self.group.elements[current_idx]
            for gen in self.group.generators:
                for h in [g.compose(gen), g.compose(gen.inverse()),
                          gen.compose(g), gen.inverse().compose(g)]:
                    j = self.group.index(h)
                    if j != current_idx:
                        state_j = GeometricState.from_pure_rotation(self.group, j)
                        e_j = self.energy_fn(state_j)
                        neighbors.append((j, e_j))

            if not neighbors:
                break

            # Find best neighbor
            best_idx, best_energy = min(neighbors, key=lambda x: x[1])

            dE = best_energy - current_energy
            if dE < 0:
                # Accept: lower energy
                current_idx = best_idx
                current_energy = best_energy
            elif temperature > 0 and random.random() < math.exp(-dE / temperature):
                # Accept with Boltzmann probability
                current_idx = best_idx
                current_energy = best_energy
            else:
                # Stuck at local minimum
                break

            self.trail.append((current_idx, current_energy))

            if current_energy == 0.0:
                break  # ground state found

        return GeometricState.from_pure_rotation(self.group, current_idx)

    def trail_summary(self) -> str:
        lines = [f"Scent trail: {len(self.trail)} steps"]
        if self.trail:
            lines.append(f"  Start energy: {self.trail[0][1]:.4f}")
            lines.append(f"  Final energy: {self.trail[-1][1]:.4f}")
            lines.append(f"  Reduction: {self.trail[0][1] - self.trail[-1][1]:.4f}")
        return "\n".join(lines)



# ---------------------------------------------------------------------------
# Bridge to existing mandala_computer: GeometricMandalaAdapter
# ---------------------------------------------------------------------------

class GeometricMandalaAdapter:
    """\nAdapter to use geometric states with the existing MandalaComputer.\n\nWraps a list of GeometricStates and provides the interface that\nMandalaComputer expects (integer states 0-7), while maintaining\nthe full geometric algebra underneath.\n\nThis allows incremental adoption: existing code keeps working,\nbut the internal state is geometrically rich.\n"""

    def __init__(self, group: OhGroup, num_cells: int):
        self.group = group
        self.num_cells = num_cells
        self.states: List[GeometricState] = []
        self.energy_model = CayleyEnergy(group)
        self.prime_map = PrimeVertex(group)

        # Initialize all cells to identity
        e_idx = group.index(IDENTITY)
        for _ in range(num_cells):
            self.states.append(GeometricState.from_pure_rotation(group, e_idx))

    def set_classical_states(self, classical_states: List[int]):
        """Set states from classical integer representation."""
        self.states = []
        for s in classical_states:
            self.states.append(GeometricState.from_classical_state(self.group, s))

    def get_classical_states(self) -> List[int]:
        """Project geometric states back to classical integers."""
        return [s.to_classical() for s in self.states]

    def geometric_energy(self, neighbors: List[Tuple[int, int]]) -> float:
        """Compute total energy using Cayley metric."""
        return self.energy_model.total_energy(self.states, neighbors)

    def propose_geometric_move(self, cell_idx: int) -> GeometricState:
        """\nPropose a new state for a cell using geometric neighbors.\n\nInstead of random integer in [0,7], we move to an adjacent\nelement in the Cayley graph. This respects the geometric\nstructure of the state space.\n"""
        import random
        current = self.states[cell_idx]
        dominant = current.ring_element.dominant_element()
        if dominant is None:
            dominant = self.group.index(IDENTITY)

        # Move to a generator-adjacent element
        g = self.group.elements[dominant]
        gen = random.choice(self.group.generators)
        if random.random() < 0.5:
            new_g = g.compose(gen)
        else:
            new_g = g.compose(gen.inverse())

        new_idx = self.group.index(new_g)
        return GeometricState.from_pure_rotation(self.group, new_idx)

    def geometric_relax(self, neighbors: List[Tuple[int, int]],
                        steps: int = 100, temperature: float = 1.0) -> List[float]:
        """\nMetropolis-Hastings relaxation using Cayley graph moves.\n\nReturns energy history.\n"""
        import random
        history = []
        current_energy = self.geometric_energy(neighbors)
        history.append(current_energy)

        T = temperature
        cooling = (0.01 / max(temperature, 0.01)) ** (1.0 / max(steps - 1, 1))

        for step in range(steps):
            cell_idx = random.randrange(self.num_cells)
            old_state = self.states[cell_idx]

            # Propose geometric move
            new_state = self.propose_geometric_move(cell_idx)
            self.states[cell_idx] = new_state
            new_energy = self.geometric_energy(neighbors)

            dE = new_energy - current_energy
            if dE < 0 or (T > 0 and random.random() < math.exp(-dE / max(T, 1e-12))):
                current_energy = new_energy
            else:
                self.states[cell_idx] = old_state

            history.append(current_energy)
            T *= cooling

        return history


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_group_structure():
    """Show the octahedral group structure."""
    print("=" * 60)
    print("GEOMETRIC STATE ALGEBRA v1.0")
    print("The octahedral group O_h as computational substrate")
    print("=" * 60)

    group = OhGroup()
    print("\n" + group.summary())


    # Show vertex action
    print("\nVertex permutations (first 6 elements):")
    for i in range(min(6, len(group.elements))):
        e = group.elements[i]
        ref = (1, 0, 0)
        image = e.act_on_vertex(ref)
        print(f"    g{i}: {ref} -> {image}  ({e})")

    return group


def demo_group_ring():
    """Show group ring arithmetic replacing GF(2)."""
    print("\n" + "=" * 60)

    print("GROUP RING Z[O_h]: Replacing GF(2)")
    print("=" * 60)

    group = OhGroup()

    # Create some ring elements
    e = GroupRingElement.from_identity(group)
    g1 = GroupRingElement.from_element(group, 1)
    g2 = GroupRingElement.from_element(group, 2)

    print(f"\nIdentity: {e}")
    print(f"  g1: {g1}")
    print(f"  g2: {g2}")

    # Addition
    s = g1 + g2
    print(f"\ng1 + g2 = {s}  (support: {s.support_size()})")

    # Multiplication (convolution)
    p = g1 * g2
    print(f"  g1 * g2 = {p}")

    # Inverse check
    g1_inv = g1.involute()
    check = g1 * g1_inv
    print(f"\ng1 * g1^-1 = {check}")
    print(f"  Is identity? {check.is_identity()}")

    # Compare with XOR: in GF(2), a XOR a = 0
    # In Z[O_h], g * g^{-1} = identity
    print("\n--- GF(2) vs Z[O_h] cancellation ---")
    print("  GF(2):   a ^ a = 0            (binary collapse)")
    print("  Z[O_h]:  g * g^{-1} = e       (geometric identity)")
    print("  Key difference: Z[O_h] preserves which rotation cancelled,")
    print("  not just that something cancelled.")

    return group


def demo_geometric_states():
    """Show states as group elements."""
    print("\n" + "=" * 60)

    print("GEOMETRIC STATES: States ARE Symmetries")
    print("=" * 60)

    group = OhGroup()

    print("\nClassical -> Geometric state mapping:")
    for classical in range(8):
        gs = GeometricState.from_classical_state(group, classical)
        elem_idx = gs.ring_element.dominant_element()
        elem = group.elements[elem_idx]
        ref = (1, 0, 0)
        image = elem.act_on_vertex(ref)
        print(f"    state {classical} -> {elem}  ")
        print(f"           vertex action: {ref} -> {image}")
        print(f"           order={elem.order()}, {'proper' if elem.is_proper() else 'improper'}")

    # Geometric cancellation
    print("\n--- Geometric Cancellation ---")
    s0 = GeometricState.from_classical_state(group, 0)
    s2 = GeometricState.from_classical_state(group, 2)
    s2_inv = s2.geometric_inverse()

    composed = s2.compose(s2_inv)
    print(f"  state_2 composed with state_2_inverse: {composed}")
    print(f"  Is identity? {composed.ring_element.is_identity()}")

    # Cayley distances
    print("\n--- Cayley Distances (geometric metric) ---")
    for i in range(8):
        dists = []
        si = GeometricState.from_classical_state(group, i)
        for j in range(8):
            sj = GeometricState.from_classical_state(group, j)
            dists.append(f"{si.cayley_distance_to(sj):.0f}")
        print(f"    state {i}: [{', '.join(dists)}]")

    return group


def demo_prime_vertices():
    """Show primes mapped to octahedral vertices."""
    print("\n" + "=" * 60)

    print("PRIME VERTICES: Primes Inhabit the Octahedron")
    print("=" * 60)

    group = OhGroup()
    pv = PrimeVertex(group)
    print("\n" + pv.summary())


    # Factor 15 = 3 * 5 geometrically
    print("\n--- Geometric Factorization ---")
    for N in [15, 21, 35]:
        result = pv.factor_pair_geometric(N)
        if result:
            a, b = result
            print(f"  {N} = {a} composed with {b}")
            composed = a.compose(b)
            print(f"       composition: {composed}")
        else:
            print(f"  {N}: no geometric factorization found")

    return group


def demo_scent_trail():
    """Show energy descent on the Cayley graph."""
    print("\n" + "=" * 60)

    print("SCENT TRAIL: Energy Descent on Octahedral Lattice")
    print("=" * 60)

    group = OhGroup()

    # Target: find the identity (energy = distance from identity)
    e_idx = group.index(IDENTITY)

    def energy_fn(state):
        dominant = state.ring_element.dominant_element()
        if dominant is None:
            return float("inf")
        return float(group.distance(e_idx, dominant))

    trail = ScentTrail(group, energy_fn)

    # Start from element maximally distant from identity
    e_idx_val = group.index(IDENTITY)
    start_idx = max(range(len(group.elements)),
                    key=lambda i: group.distance(e_idx_val, i))
    start = GeometricState.from_pure_rotation(group, start_idx)
    start_energy = energy_fn(start)
    print(f"\nStart: element {start_idx} ({group.elements[start_idx]})")
    print(f"  Start energy (distance from identity): {start_energy}")

    result = trail.descend(start, max_steps=20, temperature=0.1)
    print(f"\n{trail.trail_summary()}")
    print(f"  Final state: {result}")
    print(f"  Reached identity? {result.ring_element.is_identity()}")

    return group


def demo_geometric_relaxation():
    """Show full geometric Metropolis-Hastings relaxation."""
    print("\n" + "=" * 60)

    print("GEOMETRIC RELAXATION: Cayley Graph Annealing")
    print("=" * 60)

    group = OhGroup()
    adapter = GeometricMandalaAdapter(group, num_cells=4)

    # Set up a simple ring topology
    neighbors = [(0, 1), (1, 2), (2, 3), (3, 0)]

    # Random initial states
    import random
    random.seed(42)
    for i in range(4):
        idx = random.randrange(len(group.elements))
        adapter.states[i] = GeometricState.from_pure_rotation(group, idx)

    classical_before = adapter.get_classical_states()
    energy_before = adapter.geometric_energy(neighbors)

    print(f"\nInitial classical states: {classical_before}")
    print(f"  Initial energy: {energy_before:.4f}")

    # Relax
    history = adapter.geometric_relax(neighbors, steps=200, temperature=2.0)

    classical_after = adapter.get_classical_states()
    energy_after = adapter.geometric_energy(neighbors)

    print(f"  Final classical states: {classical_after}")
    print(f"  Final energy: {energy_after:.4f}")
    print(f"  Energy reduction: {energy_before - energy_after:.4f}")
    print(f"  Steps taken: {len(history)}")

    return group


def demo_null_space():
    """Show geometric null space replacing GF(2) null space."""
    print("\n" + "=" * 60)

    print("GEOMETRIC NULL SPACE: Z[O_h] Module Structure")
    print("=" * 60)

    group = OhGroup()
    ns = GeometricNullSpace(group)

    # Add some constraints
    c1 = GroupRingElement.from_element(group, 5)
    c2 = GroupRingElement.from_element(group, 10)
    c3 = GroupRingElement.from_element(group, 5) + GroupRingElement.from_element(group, 10)

    ns.add_constraint(c1)
    ns.add_constraint(c2)
    ns.add_constraint(c3)

    kernel = ns.find_kernel_elements()
    print("\n" + ns.summary())


    # Verify: constraint * kernel_element should be close to identity
    for i, (c, k) in enumerate(zip(ns.constraints, kernel)):
        product = c * k
        is_id = product.is_identity()
        print(f"\nConstraint {i} * Kernel {i}:")
        print(f"    Product is identity: {is_id}")
        print(f"    Product support: {product.support_size()}")

    print("\n--- Comparison ---")
    print("  GF(2):   null space = {v : Mv = 0 mod 2}")
    print("  Z[O_h]:  kernel = {x : A*x = e in group ring}")
    print("  Z[O_h] kernel elements carry geometric information")
    print("  about HOW the constraint is satisfied, not just THAT it is.")

    return group


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GEOMETRIC STATE ALGEBRA v1.0")
    print("   States are symmetries. Cancellation is composition.")
    print("   The group ring Z[O_h] replaces GF(2).")
    print("=" * 60)

    group = demo_group_structure()
    demo_group_ring()
    demo_geometric_states()
    demo_prime_vertices()
    demo_scent_trail()
    demo_geometric_relaxation()
    demo_null_space()

    print("\n" + "=" * 60)

    print("The octahedron doesn't encode into binary.")
    print("It IS the computation.")
    print("=" * 60)
