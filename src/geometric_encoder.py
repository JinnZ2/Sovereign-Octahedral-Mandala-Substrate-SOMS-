"""
GeometricEncoder — Bidirectional encoding between geometric tokens and binary.

Ported from Geometric-to-Binary-Computational-Bridge/GEIS/geometric_encoder.py.

Handles conversion between:
- Dense mode:    Full geometric tokens (e.g., '001|O')
- Collapse mode: Flat binary strings   (e.g., '001100')

Token format: [vertex_bits][operator][symbol]
  vertex_bits : 3-bit octahedral state (000–111)
  operator    : | (radial), / (tangential), || (nested radial)
  symbol      : O (Octahedral), I (Inversion), X (Exchange), Δ (Delta)
"""

from typing import Tuple


class GeometricEncoder:
    """Bidirectional encoder between geometric and binary representations."""

    SYMBOL_MAP = {
        'O': '00',  # Octahedral
        'I': '01',  # Inversion
        'X': '10',  # Exchange
        'Δ': '11',  # Delta
    }

    REVERSE_SYMBOL_MAP = {v: k for k, v in SYMBOL_MAP.items()}

    OPERATOR_MAP = {
        '|': '1',   # Radial (toward center)
        '/': '0',   # Tangential
        ':': '0',   # Colon (alias for tangential)
    }

    REVERSE_OPERATOR_MAP = {'1': '|', '0': '/'}

    def __init__(self, vertex_width: int = 3):
        self.vertex_width = vertex_width

    def encode_to_binary(self, token: str) -> str:
        """
        Convert geometric token to flat binary.

        Example: '001|O' -> '001100'
        """
        if '||' in token:
            parts = token.split('||', 1)
            vertex_bits = parts[0]
            symbol = parts[1][0] if len(parts[1]) > 0 else 'O'
            operator_bits = '11'
        else:
            operator_found = None
            for op in ['|', '/', ':']:
                if op in token:
                    operator_found = op
                    break

            if operator_found is None:
                raise ValueError("Token must contain operator ('|', '/', or ':')")

            parts = token.split(operator_found, 1)
            vertex_bits = parts[0]
            symbol = parts[1][0] if len(parts[1]) > 0 else 'O'
            operator_bits = self.OPERATOR_MAP[operator_found]

        if len(vertex_bits) != self.vertex_width:
            raise ValueError(f"Vertex bits must be {self.vertex_width} wide, got {len(vertex_bits)}")

        try:
            int(vertex_bits, 2)
        except ValueError:
            raise ValueError(f"Vertex bits must be valid binary: {vertex_bits}")

        if symbol not in self.SYMBOL_MAP:
            raise ValueError(f"Unknown symbol '{symbol}'. Valid: {list(self.SYMBOL_MAP.keys())}")
        symbol_bits = self.SYMBOL_MAP[symbol]

        return vertex_bits + operator_bits + symbol_bits

    def decode_from_binary(self, binary_string: str) -> str:
        """
        Convert flat binary back to geometric token.

        Example: '001100' -> '001|O'
        """
        min_length = self.vertex_width + 3
        if len(binary_string) < min_length:
            raise ValueError(f"Binary string too short (need {min_length} bits)")

        vertex_bits = binary_string[:self.vertex_width]

        operator_start = self.vertex_width
        if (len(binary_string) >= self.vertex_width + 4 and
                binary_string[operator_start:operator_start + 2] == '11'):
            operator = '||'
            symbol_bits = binary_string[operator_start + 2:operator_start + 4]
        else:
            operator_bit = binary_string[operator_start]
            operator = self.REVERSE_OPERATOR_MAP.get(operator_bit, '|')
            symbol_bits = binary_string[operator_start + 1:operator_start + 3]

        symbol = self.REVERSE_SYMBOL_MAP.get(symbol_bits, 'O')
        return f"{vertex_bits}{operator}{symbol}"

    def validate_token(self, token: str) -> bool:
        """Verify token is valid and round-trips correctly."""
        try:
            binary = self.encode_to_binary(token)
            decoded = self.decode_from_binary(binary)
            return decoded == token
        except Exception:
            return False

    def get_components(self, token: str) -> Tuple[str, str, str]:
        """Extract (vertex_bits, operator, symbol) from token."""
        for op in ['||', '|', '/']:
            if op in token:
                parts = token.split(op, 1)
                vertex_bits = parts[0]
                symbol = parts[1][0] if len(parts[1]) > 0 else 'O'
                return vertex_bits, op, symbol
        raise ValueError("Invalid token format")
