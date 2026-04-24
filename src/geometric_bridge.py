"""
Geometric Binary Bridge — Self-describing protocol for physical sensor I/O.

Any AI can read physical geometry (component health, electrical fields, magnetic
fields, spectra, polyhedral configs) as binary bitstrings, and write binary back
to actuators through the same 8 bridge targets.

Protocol features:
  - Self-describing header (magic 'GB', version, modality, length)
  - Gray coding for all continuous bands (adjacent values differ by 1 bit)
  - 7 modalities: hardware, electric, magnetic, gravitational, spectrum,
    polyhedral, GEIS
  - 8 bridge targets: thermal, electric, magnetic, light, sound, wave,
    pressure, chemical
  - Confidence grounding via noise power: C = 1/(1+N)
  - Drill depth escalation: pass → monitor → alert → quarantine

Usage:
    from src.geometric_bridge import (
        GeometricBridge, SensorDecoder, decode_hardware,
        component_health_score, ohms_law, coulomb_force,
    )

    # Decode a 39-bit hardware bitstring
    data = decode_hardware('010011110001010100110100001101011000101')

    # Full bridge: sense + act
    bridge = GeometricBridge()
    bridge.act("thermal", temperature_c=45.0, confidence=0.95)

Source: Geometric-to-Binary Computational Bridge ecosystem (CC0/MIT)
"""

from __future__ import annotations
import math
import struct
from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any


# ============================================================================
# Protocol constants
# ============================================================================

MAGIC_BYTES = b'GB'       # 0x47 0x42
PROTOCOL_VERSION = 1

class Modality(IntEnum):
    HARDWARE      = 0
    ELECTRIC      = 1
    MAGNETIC      = 2
    GRAVITATIONAL = 3
    SPECTRUM      = 4
    POLYHEDRAL    = 5
    GEIS          = 6

class BridgeTarget(IntEnum):
    THERMAL  = 0
    ELECTRIC = 1
    MAGNETIC = 2
    LIGHT    = 3
    SOUND    = 4
    WAVE     = 5
    PRESSURE = 6
    CHEMICAL = 7

class DrillDepth(IntEnum):
    PASS       = 0   # Gray 00
    MONITOR    = 1   # Gray 01
    QUARANTINE = 2   # Gray 10
    ALERT      = 3   # Gray 11


# ============================================================================
# Gray code utilities
# ============================================================================

def gray_to_binary(gray_bits: str) -> int:
    """Convert Gray-code bitstring to binary integer."""
    g = int(gray_bits, 2)
    mask = g >> 1
    while mask:
        g ^= mask
        mask >>= 1
    return g


def binary_to_gray(n: int, bits: int) -> str:
    """Convert binary integer to Gray-code bitstring of given width."""
    return format(n ^ (n >> 1), f'0{bits}b')


def gray_to_value(gray_bits: str, bands: List[float]) -> float:
    """Convert Gray-coded magnitude band back to representative value."""
    idx = gray_to_binary(gray_bits)
    return bands[idx] if idx < len(bands) else 0.0


def value_to_gray(value: float, bands: List[float]) -> str:
    """Convert a value to Gray-coded band bits."""
    idx = min(range(len(bands)), key=lambda i: abs(bands[i] - value))
    bits_needed = max(1, math.ceil(math.log2(max(len(bands), 2))))
    return binary_to_gray(idx, bits_needed)


# ============================================================================
# Band tables
# ============================================================================

HEALTH_BANDS     = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]
VOLTAGE_BANDS    = [0.0, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 50.0]
CURRENT_BANDS    = [0.0, 1e-6, 1e-4, 1e-3, 0.01, 0.1, 1.0, 10.0]
TEMP_BANDS       = [-55.0, 25.0, 40.0, 60.0, 85.0, 100.0, 125.0, 175.0]
NOISE_BANDS      = [0.0, 0.01, 0.05, 0.1, 0.2, 0.4, 0.7, 1.0]
DRIFT_BANDS      = [0.0, 1.0, 10.0, 50.0]
LIFETIME_BANDS   = [0.0, 1.0, 10.0, 100.0, 500.0, 1000.0, 5000.0, 1e9]
EFFECT_BANDS     = [0.0, 2.5, 5.0, 7.5]
CHARGE_BANDS     = [0.0, 1e-12, 1e-9, 1e-6, 1e-3, 0.01, 0.1, 1.0]
FIELD_BANDS_T    = [0.0, 1e-9, 1e-6, 1e-3, 0.1, 1.0, 10.0, 100.0]
FREQ_BANDS       = [0.0, 1e3, 1e6, 1e9, 1e12, 1e15, 1e18, 1e21]
AMPLITUDE_BANDS  = [0.0, 0.001, 0.01, 0.1, 0.25, 0.5, 0.75, 1.0]

FAILURE_MODES    = ["none", "drift", "degradation", "partial_degradation",
                    "open_circuit", "short_circuit"]
REPURPOSE_CLASSES = ["none", "thermal", "conductor", "sensor",
                     "antenna", "noise_source", "mechanical", "filter"]
BRIDGE_TARGETS   = ["thermal", "electric", "magnetic", "light",
                    "sound", "wave", "pressure", "chemical"]


# ============================================================================
# Physics functions — pure Python, no external deps
# ============================================================================

def component_health_score(baseline: float, current: float,
                           failure_threshold: float) -> float:
    """H = max(0, 1 - |x - x0| / |x_fail - x0|)"""
    span = abs(failure_threshold - baseline)
    if span < 1e-30:
        return 1.0
    return max(0.0, 1.0 - abs(current - baseline) / span)


def drift_percent(baseline: float, current: float) -> float:
    """D = |x - x0| / |x0| * 100"""
    if abs(baseline) < 1e-30:
        return 0.0
    return abs(current - baseline) / abs(baseline) * 100.0


def lifetime_estimate_hours(health: float, drift_rate_per_hour: float) -> float:
    """L = H / max(drift_rate, eps)"""
    if drift_rate_per_hour <= 0.0:
        return 1e9
    return health / max(drift_rate_per_hour, 1e-12)


def noise_power(v_rms: float, resistance_ohm: float) -> float:
    """N = V_rms^2 / R"""
    if resistance_ohm <= 0.0:
        return 0.0
    return (v_rms ** 2) / resistance_ohm


def confidence_from_noise(n: float) -> float:
    """C = 1 / (1 + N)"""
    return 1.0 / (1.0 + n)


def ohms_law(V: float, I: float) -> float:
    """R = V / I"""
    return float("inf") if I == 0 else V / I


def power_dissipation(V: float, I: float) -> float:
    """P = V * I"""
    return V * I


def coulomb_force(q1: float, q2: float, r: float) -> float:
    """F = k * q1 * q2 / r^2"""
    K = 8.9875e9
    if r == 0:
        return 0.0
    return K * q1 * q2 / (r * r)


def electric_field_magnitude(q: float, r: float) -> float:
    """E = k * |q| / r^2"""
    K = 8.9875e9
    if r == 0:
        return 0.0
    return K * abs(q) / (r * r)


def skin_depth(frequency_hz: float, conductivity_S: float) -> float:
    """delta = sqrt(2 / (omega * mu0 * sigma))"""
    MU_0 = 4 * math.pi * 1e-7
    if frequency_hz == 0 or conductivity_S == 0:
        return float("inf")
    omega = 2.0 * math.pi * frequency_hz
    return math.sqrt(2.0 / (omega * MU_0 * conductivity_S))


# ============================================================================
# Decoded data structures
# ============================================================================

@dataclass
class HardwareData:
    """Decoded 39-bit hardware sensor reading."""
    failure_mode: str
    health_score: float
    is_critical: bool
    confidence_hi: bool
    has_synergy: bool
    voltage_v: float
    current_a: float
    temperature_c: float
    noise_level: float
    repurpose_class: str
    effectiveness: float
    bridge_target: str
    drift_pct: float
    salvageable: bool
    fallback_ready: bool
    lifetime_hours: float
    drill_depth: str
    is_semiconductor: bool
    confidence: float = 0.0

    def __post_init__(self):
        if self.confidence == 0.0:
            self.confidence = confidence_from_noise(self.noise_level)


@dataclass
class ElectricData:
    """Decoded electric sensor data."""
    charges: List[float]
    currents: List[float]
    voltages: List[float]
    conductivities: List[float]
    mean_power_w: float = 0.0
    mean_impedance_ohm: float = 0.0
    dissipative: bool = False


# ============================================================================
# Protocol header
# ============================================================================

@dataclass
class BridgeHeader:
    """
    Self-describing Geometric Binary Bridge header (5 bytes / 40 bits).

    Byte 0-1: magic 'GB' (0x47 0x42)
    Byte 2:   version (hi nibble) | modality (lo nibble)
    Byte 3-4: payload length in bytes (big-endian uint16)
    """
    magic: bytes
    version: int
    modality: Modality
    payload_length_bytes: int

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[BridgeHeader, bytes]:
        if len(data) < 5:
            raise ValueError(f"Header requires 5 bytes, got {len(data)}")
        magic = data[0:2]
        if magic != MAGIC_BYTES:
            raise ValueError(f"Bad magic: {magic!r} (expected b'GB')")
        vm = data[2]
        version = (vm >> 4) & 0x0F
        modality = Modality(vm & 0x0F)
        payload_len = struct.unpack('>H', data[3:5])[0]
        return cls(magic, version, modality, payload_len), data[5:5 + payload_len]

    def to_bytes(self, payload: bytes) -> bytes:
        vm = ((self.version & 0x0F) << 4) | (self.modality & 0x0F)
        return MAGIC_BYTES + bytes([vm]) + struct.pack('>H', len(payload)) + payload


# ============================================================================
# Decoders
# ============================================================================

def decode_hardware(bits: str) -> HardwareData:
    """
    Decode a 39-bit hardware bitstring.

    Layout:
      A (9b): failure_mode[3] health_band[3] is_critical[1] confidence_hi[1] has_synergy[1]
      B (12b): voltage_band[3] current_band[3] temp_band[3] noise_band[3]
      C (12b): repurpose_class[3] effectiveness[2] bridge_target[3] drift_band[2] salvageable[1] fallback_ready[1]
      D (6b): lifetime_band[3] drill_depth[2] semiconductor[1]
    """
    if len(bits) < 39:
        raise ValueError(f"Hardware payload needs 39 bits, got {len(bits)}")

    p = 0
    def take(n):
        nonlocal p; s = bits[p:p + n]; p += n; return s

    # Section A
    failure_mode = FAILURE_MODES[gray_to_binary(take(3)) % len(FAILURE_MODES)]
    health_score = gray_to_value(take(3), HEALTH_BANDS)
    is_critical = take(1) == '1'
    confidence_hi = take(1) == '1'
    has_synergy = take(1) == '1'

    # Section B
    voltage_v = gray_to_value(take(3), VOLTAGE_BANDS)
    current_a = gray_to_value(take(3), CURRENT_BANDS)
    temperature_c = gray_to_value(take(3), TEMP_BANDS)
    noise_level = gray_to_value(take(3), NOISE_BANDS)

    # Section C
    repurpose_class = REPURPOSE_CLASSES[gray_to_binary(take(3)) % len(REPURPOSE_CLASSES)]
    effectiveness = gray_to_value(take(2), EFFECT_BANDS)
    bridge_target = BRIDGE_TARGETS[gray_to_binary(take(3)) % len(BRIDGE_TARGETS)]
    drift_pct = gray_to_value(take(2), DRIFT_BANDS)
    salvageable = take(1) == '1'
    fallback_ready = take(1) == '1'

    # Section D
    lifetime_hours = gray_to_value(take(3), LIFETIME_BANDS)
    drill_depth = ["pass", "monitor", "quarantine", "alert"][gray_to_binary(take(2)) % 4]
    is_semiconductor = (take(1) == '1') if p <= len(bits) else False

    return HardwareData(
        failure_mode=failure_mode, health_score=health_score,
        is_critical=is_critical, confidence_hi=confidence_hi,
        has_synergy=has_synergy, voltage_v=voltage_v,
        current_a=current_a, temperature_c=temperature_c,
        noise_level=noise_level, repurpose_class=repurpose_class,
        effectiveness=effectiveness, bridge_target=bridge_target,
        drift_pct=drift_pct, salvageable=salvageable,
        fallback_ready=fallback_ready, lifetime_hours=lifetime_hours,
        drill_depth=drill_depth, is_semiconductor=is_semiconductor,
    )


def decode_electric(bits: str) -> ElectricData:
    """
    Decode variable-length electric payload.

    Each value: 1b sign + 3b Gray magnitude.
    Trailer: mean_power[3] + mean_impedance[3] + dissipative[1] = 7 bits.
    """
    if len(bits) < 7:
        return ElectricData([], [], [], [])

    trailer = bits[-7:]
    payload = bits[:-7]

    # Count values per field: payload length / 4 / 4 fields
    n_per_field = len(payload) // 16 if len(payload) >= 16 else 0
    p = 0

    def take_signed(bands):
        nonlocal p
        if p + 4 > len(payload):
            return 0.0
        sign = -1.0 if payload[p] == '1' else 1.0
        mag = gray_to_value(payload[p + 1:p + 4], bands)
        p += 4
        return sign * mag

    charges = [take_signed(CHARGE_BANDS) for _ in range(n_per_field)]
    currents = [take_signed(CURRENT_BANDS) for _ in range(n_per_field)]
    voltages = [take_signed(VOLTAGE_BANDS) for _ in range(n_per_field)]
    conductivities = [take_signed(CHARGE_BANDS) for _ in range(n_per_field)]

    mean_power = gray_to_value(trailer[0:3], [0.0, 1e-4, 1e-2, 0.1, 1.0, 10.0, 100.0, 1000.0])
    mean_impedance = gray_to_value(trailer[3:6], [0.0, 0.01, 0.1, 1.0, 10.0, 100.0, 1e4, 1e6])
    dissipative = trailer[6] == '1'

    return ElectricData(
        charges=charges, currents=currents, voltages=voltages,
        conductivities=conductivities, mean_power_w=mean_power,
        mean_impedance_ohm=mean_impedance, dissipative=dissipative,
    )


# ============================================================================
# Sensor decoder (universal dispatcher)
# ============================================================================

class SensorDecoder:
    """Decode any Geometric Binary Bridge stream."""

    _decoders = {
        Modality.HARDWARE: decode_hardware,
        Modality.ELECTRIC: decode_electric,
    }

    def decode_raw(self, modality: str, bits: str) -> Any:
        """Decode raw bitstring given modality name."""
        mod = Modality[modality.upper()]
        decoder = self._decoders.get(mod)
        if decoder is None:
            raise ValueError(f"No decoder for {modality}")
        return decoder(bits)

    def decode_framed(self, data: bytes) -> Dict[str, Any]:
        """Decode bytes with self-describing GB header."""
        header, payload_bytes = BridgeHeader.from_bytes(data)
        bits = ''.join(f'{b:08b}' for b in payload_bytes)
        decoder = self._decoders.get(header.modality)
        if decoder is None:
            return {"modality": header.modality.name, "error": "no decoder"}
        decoded = decoder(bits)
        confidence = getattr(decoded, 'confidence', 1.0)
        return {
            "modality": header.modality.name,
            "version": header.version,
            "data": decoded,
            "confidence": confidence,
        }


# ============================================================================
# Actuator controller
# ============================================================================

class ActuatorController:
    """
    Control physical actuators through the 8 bridge targets.

    In simulation mode (no endpoint), prints commands.
    With an endpoint, encodes Gray-coded commands to binary.
    """

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint
        self.last_commands: Dict[str, Dict] = {}

    def set_thermal(self, temperature_c: float, confidence: float = 1.0):
        self._send("thermal", temperature_c=temperature_c, confidence=confidence)

    def set_electric(self, voltage_v: float, current_a: float, confidence: float = 1.0):
        self._send("electric", voltage_v=voltage_v, current_a=current_a, confidence=confidence)

    def set_magnetic(self, field_t: float, confidence: float = 1.0):
        self._send("magnetic", field_t=field_t, confidence=confidence)

    def set_light(self, intensity: float, wavelength_nm: float, confidence: float = 1.0):
        self._send("light", intensity=intensity, wavelength_nm=wavelength_nm, confidence=confidence)

    def set_sound(self, pressure_pa: float, frequency_hz: float, confidence: float = 1.0):
        self._send("sound", pressure_pa=pressure_pa, frequency_hz=frequency_hz, confidence=confidence)

    def set_wave(self, frequency_hz: float, amplitude: float, confidence: float = 1.0):
        self._send("wave", frequency_hz=frequency_hz, amplitude=amplitude, confidence=confidence)

    def set_pressure(self, force_n: float, confidence: float = 1.0):
        self._send("pressure", force_n=force_n, confidence=confidence)

    def set_chemical(self, concentration_ppm: float, confidence: float = 1.0):
        self._send("chemical", concentration_ppm=concentration_ppm, confidence=confidence)

    def _send(self, target: str, **kwargs):
        self.last_commands[target] = kwargs


# ============================================================================
# Unified bridge interface
# ============================================================================

class GeometricBridge:
    """
    Complete Geometric Binary Bridge — sense + act.

    Any AI imports this, calls sense() to read sensors,
    calls act() to control actuators.

    Extended bridges from the G2B ecosystem are auto-discovered
    via BridgeRegistry. Use available_bridges() to see what's loaded.
    """

    def __init__(self, endpoint: Optional[str] = None):
        self.decoder = SensorDecoder()
        self.actuator = ActuatorController(endpoint)
        self._registry = None

    @property
    def registry(self):
        """Lazy-load the bridge registry (avoids import cost if unused)."""
        if self._registry is None:
            from src.bridge_registry import BridgeRegistry
            self._registry = BridgeRegistry.instance()
        return self._registry

    def sense(self, modality: str, bits: str) -> Any:
        """Decode raw sensor bitstring."""
        return self.decoder.decode_raw(modality, bits)

    def sense_framed(self, data: bytes) -> Dict[str, Any]:
        """Decode self-describing GB-framed bytes."""
        return self.decoder.decode_framed(data)

    def act(self, target: str, **kwargs):
        """Send actuator command to a bridge target."""
        method = getattr(self.actuator, f"set_{target}", None)
        if method is None:
            raise ValueError(f"Unknown bridge target: {target}")
        method(**kwargs)

    def encode_header(self, modality: str, payload: bytes) -> bytes:
        """Wrap payload with self-describing GB header."""
        mod = Modality[modality.upper()]
        hdr = BridgeHeader(MAGIC_BYTES, PROTOCOL_VERSION, mod, len(payload))
        return hdr.to_bytes(payload)

    def available_bridges(self) -> List[str]:
        """List all available bridge domains (core + extended)."""
        core = list(BRIDGE_TARGETS)
        extended = [b for b in self.registry.available() if b not in core]
        return core + extended

    def bridge_info(self, name: str) -> Optional[Dict]:
        """Get metadata for a bridge domain from the contract manifest."""
        return self.registry.info(name)

    def get_encoder(self, name: str) -> Optional[Any]:
        """Get an encoder class from the extended bridge registry."""
        return self.registry.get(name)
