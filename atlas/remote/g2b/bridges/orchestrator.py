"""
Bridge Orchestrator
===================
Dynamically loads any domain encoder and merges their outputs
into a unified cross-domain convergence vector.
"""

import importlib
import hashlib
from atlas.remote.g2b.bridges.abstract_encoder import BinaryBridgeEncoder


class BridgeOrchestrator:
    """
    Central manager for all domain bridge encoders.

    Handles:
      - dynamic registration and loading of encoders
      - unified bitstream aggregation
      - per-domain metadata and global checksum tracking
    """

    def __init__(self):
        self.registry: dict = {}
        self.results: dict = {}
        self.master_bitstring: str = ""

    def register_encoder(self, name: str, module_path: str, class_name: str):
        """Register an encoder by Python import path and class name."""
        self.registry[name] = {"module": module_path, "class": class_name}

    def load_encoder(self, name: str) -> BinaryBridgeEncoder:
        """Dynamically import and instantiate an encoder class."""
        if name not in self.registry:
            raise ValueError(f"Encoder '{name}' not registered.")
        entry = self.registry[name]
        module = importlib.import_module(entry["module"])
        return getattr(module, entry["class"])()

    def run_encoder(self, name: str, geometry_data: dict) -> str:
        """Run one domain encoder and store its output."""
        encoder = self.load_encoder(name)
        encoder.from_geometry(geometry_data)
        bitstring = encoder.to_binary()
        self.results[name] = {
            "bits": bitstring,
            "checksum": encoder.checksum(bitstring),
            "length": len(bitstring),
        }
        return bitstring

    def aggregate(self) -> str:
        """Concatenate all domain bitstrings into a single convergence vector."""
        self.master_bitstring = "".join(r["bits"] for r in self.results.values())
        return self.master_bitstring

    def global_checksum(self) -> str:
        """SHA256 of the merged convergence vector."""
        return hashlib.sha256(self.master_bitstring.encode("utf-8")).hexdigest()

    def report(self) -> dict:
        """Full orchestration report."""
        return {
            "domains": list(self.results.keys()),
            "individual": self.results,
            "total_bits": len(self.master_bitstring),
            "global_checksum": self.global_checksum() if self.master_bitstring else None,
        }
