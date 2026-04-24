"""
Bridge Registry — Dynamic discovery and dispatch for all available bridges.

Auto-discovers bridge encoders from the G2B fieldlink mount (atlas/remote/g2b/)
and exposes them through a unified API. Falls back gracefully when bridges
are unavailable.

Usage:
    from src.bridge_registry import BridgeRegistry

    reg = BridgeRegistry()
    print(reg.available())          # ['sound', 'electric', 'gravity', ...]
    print(reg.layers())             # {'physical': [...], 'topological': [...], ...}

    # Get an encoder class (or None if not available)
    enc_cls = reg.get("sound")
    if enc_cls:
        encoder = enc_cls()

    # Get metadata from the contract manifest
    info = reg.info("gravity")
    print(info["payload_bits"])     # 39
    print(info["notes"])            # "Couples to gravitational potential..."

    # List alternative computing extensions
    print(reg.alternatives())       # ['electric', 'gravity', 'sound', 'community', 'sovereign']
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type


PARADIGM_MATRIX = {
    "ternary":      {"electric": True,  "gravity": True,  "magnetic": True,  "sound": True,  "thermal": True},
    "quantum":      {"electric": True,  "gravity": True,  "magnetic": False, "sound": True,  "thermal": False},
    "stochastic":   {"electric": True,  "gravity": True,  "magnetic": False, "sound": True,  "thermal": True},
    "neuromorphic": {"electric": True,  "gravity": False, "magnetic": False, "sound": True,  "thermal": False},
    "reservoir":    {"electric": True,  "gravity": True,  "magnetic": True,  "sound": True,  "thermal": True},
    "memristive":   {"electric": True,  "gravity": False, "magnetic": False, "sound": False, "thermal": False},
    "approximate":  {"electric": True,  "gravity": True,  "magnetic": False, "sound": False, "thermal": True},
}

ALL_PARADIGMS = list(PARADIGM_MATRIX.keys())


@dataclass
class BridgeInfo:
    """Metadata for one bridge domain."""
    name: str
    layer: str
    payload_bits: Any  # int or str ("dynamic: ...")
    encoder_path: str
    silicon_entry: str
    hardware_related: bool
    notes: str
    encoder_class: Optional[Type] = None
    available: bool = False
    alternative_compute: Optional[str] = None
    paradigms: List[str] = field(default_factory=list)


class BridgeRegistry:
    """
    Dynamic bridge discovery from the G2B fieldlink mount.

    Reads bridge_contract_manifest.json for the canonical registry,
    then attempts to import each encoder. Bridges that import
    successfully are marked available; others are listed but not usable.
    """

    G2B_ROOT = Path(__file__).parent.parent / "atlas" / "remote" / "g2b"
    MANIFEST_PATH = G2B_ROOT / "bridge_contract_manifest.json"

    # Alternative computing extension files (domain → filename)
    ALT_COMPUTE_MAP = {
        "electric": "electric_alternative_compute.py",
        "gravity": "gravity_alternative_compute.py",
        "sound": "sound_alternative_compute.py",
        "community": "community_alternative_compute.py",
        "sovereign": "sovereign_alternative_compute.py",
    }

    # Advanced pattern bridges (not in the manifest but importable)
    ADVANCED_BRIDGES = {
        "memristive": "bridges.memristive_bridge",
        "neuromorphic": "bridges.neuromorphic_bridge",
        "reservoir": "bridges.reservoir_bridge",
    }

    def __init__(self, auto_discover: bool = True):
        self._bridges: Dict[str, BridgeInfo] = {}
        self._manifest_loaded = False
        self._g2b_on_path = False

        if auto_discover:
            self._load_manifest()
            self._discover_bridges()
            self._discover_alternatives()

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def available(self) -> List[str]:
        """Names of bridges that imported successfully."""
        return sorted(n for n, b in self._bridges.items() if b.available)

    def all_bridges(self) -> List[str]:
        """All bridge names (available or not)."""
        return sorted(self._bridges.keys())

    def layers(self) -> Dict[str, List[str]]:
        """Group available bridges by layer."""
        result: Dict[str, List[str]] = {}
        for name, info in self._bridges.items():
            if info.available:
                result.setdefault(info.layer, []).append(name)
        return result

    def get(self, name: str) -> Optional[Type]:
        """Return encoder class for a bridge, or None if unavailable."""
        info = self._bridges.get(name.lower())
        return info.encoder_class if info and info.available else None

    def info(self, name: str) -> Optional[Dict]:
        """Return metadata dict for a bridge domain."""
        info = self._bridges.get(name.lower())
        if not info:
            return None
        return {
            "name": info.name,
            "layer": info.layer,
            "payload_bits": info.payload_bits,
            "encoder_path": info.encoder_path,
            "hardware_related": info.hardware_related,
            "notes": info.notes,
            "available": info.available,
            "has_alternative_compute": info.alternative_compute is not None,
            "paradigms": info.paradigms,
        }

    def alternatives(self) -> List[str]:
        """Bridge domains that have alternative computing extensions."""
        return sorted(
            n for n, b in self._bridges.items()
            if b.alternative_compute is not None or b.paradigms
        )

    def paradigms_for(self, bridge_name: str) -> List[str]:
        """List alternative paradigms available for a bridge domain."""
        info = self._bridges.get(bridge_name.lower())
        return info.paradigms if info else []

    def bridges_for_paradigm(self, paradigm: str) -> List[str]:
        """List bridge domains that support a given paradigm."""
        return sorted(
            n for n, b in self._bridges.items()
            if paradigm.lower() in b.paradigms
        )

    def paradigm_matrix(self) -> Dict[str, Dict[str, bool]]:
        """Return the full paradigm x bridge support matrix."""
        matrix: Dict[str, Dict[str, bool]] = {}
        for paradigm in ALL_PARADIGMS:
            matrix[paradigm] = {}
            for name, info in self._bridges.items():
                matrix[paradigm][name] = paradigm in info.paradigms
        return matrix

    def summary(self) -> str:
        """Human-readable summary of the registry."""
        avail = self.available()
        total = len(self._bridges)
        by_layer = self.layers()
        alts = self.alternatives()

        lines = [
            f"Bridge Registry: {len(avail)}/{total} bridges available",
            "",
        ]
        for layer, names in sorted(by_layer.items()):
            lines.append(f"  {layer}: {', '.join(names)}")
        if alts:
            lines.append(f"\n  Alternative computing: {', '.join(alts)}")
        not_avail = sorted(set(self.all_bridges()) - set(avail))
        if not_avail:
            lines.append(f"\n  Not importable: {', '.join(not_avail)}")

        # Paradigm matrix
        domains_with_paradigms = sorted(
            n for n in avail if self._bridges[n].paradigms
        )
        if domains_with_paradigms:
            lines.append("")
            lines.append("  Paradigm matrix:")
            hdr = f"    {'paradigm':<15}"
            for d in domains_with_paradigms:
                hdr += f"{d:<12}"
            lines.append(hdr)
            for p in ALL_PARADIGMS:
                row = f"    {p:<15}"
                for d in domains_with_paradigms:
                    row += f"{'yes':<12}" if p in self._bridges[d].paradigms else f"{'.':<12}"
                lines.append(row)

        return "\n".join(lines)

    # ----------------------------------------------------------------
    # Discovery internals
    # ----------------------------------------------------------------

    def _ensure_g2b_path(self):
        """Add G2B root to sys.path if not already there."""
        if self._g2b_on_path:
            return
        g2b_str = str(self.G2B_ROOT)
        if g2b_str not in sys.path:
            sys.path.insert(0, g2b_str)
        self._g2b_on_path = True

    def _load_manifest(self):
        """Load bridge_contract_manifest.json if present."""
        if not self.MANIFEST_PATH.exists():
            return
        try:
            with open(self.MANIFEST_PATH) as f:
                manifest = json.load(f)
            for entry in manifest.get("bridge_domains", []):
                name = entry["name"]
                self._bridges[name] = BridgeInfo(
                    name=name,
                    layer=entry.get("layer", "unknown"),
                    payload_bits=entry.get("payload_bits", 0),
                    encoder_path=entry.get("top_level_encoder", ""),
                    silicon_entry=entry.get("silicon_entry_point", ""),
                    hardware_related=entry.get("hardware_related", False),
                    notes=entry.get("notes", ""),
                )
            self._manifest_loaded = True
        except (json.JSONDecodeError, KeyError):
            pass

    def _try_import(self, module_path: str) -> Optional[Type]:
        """
        Try to import a class from a dotted module path.
        E.g. "bridges.sound_encoder.SoundBridgeEncoder" → class
        """
        parts = module_path.rsplit(".", 1)
        if len(parts) != 2:
            return None
        mod_name, cls_name = parts
        try:
            mod = importlib.import_module(mod_name)
            return getattr(mod, cls_name, None)
        except (ImportError, ModuleNotFoundError, AttributeError):
            return None

    def _discover_bridges(self):
        """Try to import each bridge encoder."""
        self._ensure_g2b_path()

        for name, info in self._bridges.items():
            # Try top-level encoder first, then silicon entry point
            for path in [info.encoder_path, info.silicon_entry]:
                if not path:
                    continue
                cls = self._try_import(path)
                if cls is not None:
                    info.encoder_class = cls
                    info.available = True
                    break

        # Also try advanced pattern bridges not in manifest
        for name, mod_path in self.ADVANCED_BRIDGES.items():
            if name not in self._bridges:
                cls = self._try_import(mod_path)
                if cls is not None:
                    self._bridges[name] = BridgeInfo(
                        name=name,
                        layer="advanced",
                        payload_bits="variable",
                        encoder_path=mod_path,
                        silicon_entry="",
                        hardware_related=False,
                        notes=f"Advanced pattern bridge: {name}",
                        encoder_class=cls,
                        available=True,
                    )

    def _discover_alternatives(self):
        """Check which bridge domains have alternative computing extensions."""
        bridges_dir = self.G2B_ROOT / "bridges"
        for domain, filename in self.ALT_COMPUTE_MAP.items():
            if (bridges_dir / filename).exists():
                if domain in self._bridges:
                    self._bridges[domain].alternative_compute = filename

        # Populate paradigm support from the matrix
        for paradigm, domain_map in PARADIGM_MATRIX.items():
            for domain, supported in domain_map.items():
                if supported and domain in self._bridges:
                    self._bridges[domain].paradigms.append(paradigm)

    # ----------------------------------------------------------------
    # Singleton convenience
    # ----------------------------------------------------------------

    _instance: Optional[BridgeRegistry] = None

    @classmethod
    def instance(cls) -> BridgeRegistry:
        """Return a shared registry instance (built once)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# ============================================================
# Quick test when run directly
# ============================================================

if __name__ == "__main__":
    reg = BridgeRegistry()
    print(reg.summary())
