# ai/ — AI Agent Entry Point

This folder provides a safe, structured entry point for AI agents
working on the SOMS codebase.

## Quick Start

```bash
chmod +x ai/enter.sh
./ai/enter.sh          # full: validate env + run tests + orient
./ai/enter.sh --quick  # skip tests, just print orientation
./ai/enter.sh --check  # validate only, exit non-zero on failure
```

## What `enter.sh` Does

1. **Validates environment** — checks Python, numpy, scipy; installs if missing
2. **Runs test suite** — 291 tests must pass before you touch anything
3. **Runs physics validation** — confirms core claims are empirically correct
4. **Checks protected files** — warns if `.fieldlink.json` or GDSII data is missing
5. **Prints orientation** — key files, rules, inventory

## Safety Rules (Enforced by Convention)

These are not code-enforced locks — they're rules for AI agents:

| Rule | Why |
|------|-----|
| Run `pytest` before and after changes | Catch regressions immediately |
| Never claim "O(1)" or "optimal" for NP-hard problems | Physics violation |
| Use "heuristic" / "approximate" / "empirically" | Honest language |
| Don't modify `.fieldlink.json` schema | Breaks 6 sibling repos |
| Don't modify `data/GDSII_Coordinates.txt` | Fabrication data, read-only |
| New experiments need a hypothesis docstring | Testable claims only |

## For CI Integration

```yaml
# GitHub Actions example
- name: AI safety gate
  run: ./ai/enter.sh --check
```

## Files in This Folder

| File | Purpose |
|------|---------|
| `enter.sh` | Entry script — environment setup + validation + orientation |
| `README.md` | This file |
