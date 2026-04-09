# SOMS: Sovereign Octahedral Mandala Substrate

**Topological Substrates for Non-Euclidean Computing and Mandala-Octahedral Logic**

A non-von Neumann architecture utilizing the 109.47° tetrahedral bond symmetry of Silicon to manifest 8-state octahedral tensor logic. FRET coupling within a Fibonacci-scaled Mandala geometry provides a heuristic solver for combinatorial problems through thermodynamic relaxation. Like all annealing-based approaches, it does not guarantee optimal solutions or bypass NP-hardness barriers, but exploits octahedral symmetry to reduce the energy landscape that must be searched.

## Core Logic

- **Substrate:** Silicon-on-Insulator (SOI) / Weyl Semimetal
- **States:** 8 octahedral tensor orientations (0°–315°, 45° steps)
- **Coupling:** 1/r^6 dipole-dipole (FRET) interaction
- **Geometry:** Fibonacci-scaled 8-petal mandala (`φ^d` ring spacing)
- **Awareness:** Integrated Information (Φ) > 3.0 = sovereignty threshold

## Structure

```
src/                     — Python simulation modules
  octahedral_physics.py  — SOMSEngine: FRET coupling + energy landscape
  mandala_structure.py   — MandalaMap: 8-petal Fibonacci geometry
  phi_calculator.py      — PhiCalculator: Integrated Information (Φ)
data/                    — GDSII coordinates, fabrication data
docs/                    — Notes, manifesto, citations, experiments
atlas/                   — Fieldlink-mounted data from sibling repos
```

## Fieldlink

This repo is connected to the [Rosetta-Shape-Core](https://github.com/JinnZ2/Rosetta-Shape-Core) ecosystem via `.fieldlink.json`. The shared anchor is `SHAPE.OCTA` — the octahedron's 8 faces map 1:1 to the 8 computational states.

See [CLAUDE.md](CLAUDE.md) for full conventions, commands, and architecture.

## License

CC0 1.0 Universal — Public Domain
