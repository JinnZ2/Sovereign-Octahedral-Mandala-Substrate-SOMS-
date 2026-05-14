"""
SenseChannel — one parallel modality of substrate awareness.
Heat, power, timing at v1. EM/magnetic/acoustic deferred.
"""

from dataclasses import dataclass, field
from collections import deque
from time import monotonic
from typing import Deque, Tuple


@dataclass
class SenseChannel:
    name:        str
    units:       str
    latency:     float                # native response time (s)
    field_type:  str   = "scalar"     # scalar | vector | phase
    buffer:      Deque[Tuple[float, float]] = field(
                     default_factory=lambda: deque(maxlen=4096))
    baseline:    float = 0.0
    noise_floor: float = 0.0

    def sample(self, value: float) -> None:
        self.buffer.append((monotonic(), value))

    def recent(self, n: int = 64) -> list:
        """Last n values, oldest first."""
        return [v for _, v in list(self.buffer)[-n:]]


def make_default_senses() -> dict:
    """Senses every node should have at v1."""
    return {
        "heat":   SenseChannel("heat",   "°C", latency=1.0),
        "power":  SenseChannel("power",  "mA", latency=0.001),
        "timing": SenseChannel("timing", "ns", latency=1e-9),
    }
