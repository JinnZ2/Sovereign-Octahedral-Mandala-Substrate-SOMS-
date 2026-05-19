"""
Lightweight tests that catch terminology drift.
These are not deep correctness tests — they exist to prevent
the 'chief/leader/master' framing from sneaking back in during
future edits.

Run:  pip install -e . && python -m pytest tests/test_terminology.py -v
"""

import os
import re
import pytest


REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
SOURCE_DIRS = ["kitchi", "examples"]

# Words that indicate hierarchy creeping back in.
# Allowed in comments only if explicitly explaining the
# mistranslation (must mention 'sovereign' nearby).
HIERARCHY_WORDS = [
    r"\bthe chief\b",
    r"\bgreat chief\b",
    r"\bleader\b",
    r"\bmaster\b",
    r"\bking node\b",
    r"\bsubordinate\b",
    r"\belect a leader\b",
]


def _iter_source_files():
    for d in SOURCE_DIRS:
        full = os.path.join(REPO_ROOT, d)
        if not os.path.isdir(full):
            continue
        for root, _, files in os.walk(full):
            for f in files:
                if f.endswith(".py"):
                    yield os.path.join(root, f)


class TestTerminologyHygiene:

    @pytest.mark.parametrize("pattern", HIERARCHY_WORDS)
    def test_no_hierarchy_words_in_source(self, pattern):
        """
        Source files should not contain hierarchy framing.
        Allowed exception: lines that also reference 'sovereign'
        (i.e. lines that are explaining the mistranslation).
        """
        rx = re.compile(pattern, re.IGNORECASE)
        offenders = []
        for path in _iter_source_files():
            with open(path, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    if rx.search(line) and "sovereign" not in line.lower():
                        offenders.append(f"{path}:{lineno}: {line.strip()}")
        assert not offenders, (
            f"Hierarchy framing found for pattern {pattern!r}:\n"
            + "\n".join(offenders)
        )

    def test_sovereign_capacity_exists(self):
        from kitchi.node import SovereignCapacity
        assert SovereignCapacity is not None

    def test_chief_capacity_is_alias_only(self):
        """ChiefCapacity must remain importable but be the same
        class as SovereignCapacity (compatibility alias)."""
        from kitchi.node import ChiefCapacity, SovereignCapacity
        assert ChiefCapacity is SovereignCapacity
