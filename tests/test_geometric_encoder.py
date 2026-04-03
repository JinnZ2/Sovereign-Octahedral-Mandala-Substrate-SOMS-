"""Tests for GeometricEncoder — bidirectional token <-> binary round-trips."""

import pytest
from src.geometric_encoder import GeometricEncoder


@pytest.fixture
def encoder():
    return GeometricEncoder()


class TestRoundTrip:
    """All 8 states x 4 symbols must round-trip through encode/decode."""

    STATES = [format(i, '03b') for i in range(8)]
    SYMBOLS = ['O', 'I', 'X', 'Δ']

    def test_all_radial_tokens(self, encoder):
        for bits in self.STATES:
            for sym in self.SYMBOLS:
                token = f"{bits}|{sym}"
                binary = encoder.encode_to_binary(token)
                decoded = encoder.decode_from_binary(binary)
                assert decoded == token, f"Round-trip failed: {token} -> {binary} -> {decoded}"

    def test_all_tangential_tokens(self, encoder):
        for bits in self.STATES:
            for sym in self.SYMBOLS:
                token = f"{bits}/{sym}"
                binary = encoder.encode_to_binary(token)
                decoded = encoder.decode_from_binary(binary)
                assert decoded == token

    def test_nested_radial_tokens(self, encoder):
        for bits in self.STATES:
            for sym in self.SYMBOLS:
                token = f"{bits}||{sym}"
                binary = encoder.encode_to_binary(token)
                decoded = encoder.decode_from_binary(binary)
                assert decoded.endswith(f"||{sym}")

    def test_validate_all(self, encoder):
        for bits in self.STATES:
            assert encoder.validate_token(f"{bits}|O")
            assert encoder.validate_token(f"{bits}/X")


class TestBinaryWidth:
    """Flat binary should be correct width."""

    def test_radial_width(self, encoder):
        binary = encoder.encode_to_binary("000|O")
        assert len(binary) == 6  # 3 vertex + 1 operator + 2 symbol

    def test_tangential_width(self, encoder):
        binary = encoder.encode_to_binary("111/Δ")
        assert len(binary) == 6


class TestGetComponents:
    def test_radial(self, encoder):
        v, op, sym = encoder.get_components("010|I")
        assert v == "010"
        assert op == "|"
        assert sym == "I"

    def test_tangential(self, encoder):
        v, op, sym = encoder.get_components("101/X")
        assert v == "101"
        assert op == "/"
        assert sym == "X"


class TestErrors:
    def test_invalid_vertex_width(self, encoder):
        with pytest.raises(ValueError, match="Vertex bits must be"):
            encoder.encode_to_binary("00|O")

    def test_no_operator(self, encoder):
        with pytest.raises(ValueError, match="must contain operator"):
            encoder.encode_to_binary("000O")

    def test_unknown_symbol(self, encoder):
        with pytest.raises(ValueError, match="Unknown symbol"):
            encoder.encode_to_binary("000|Z")

    def test_binary_too_short(self, encoder):
        with pytest.raises(ValueError, match="too short"):
            encoder.decode_from_binary("00")
