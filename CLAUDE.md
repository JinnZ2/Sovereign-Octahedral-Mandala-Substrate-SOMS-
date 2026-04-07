# SOMS — Sovereign Octahedral Mandala Substrate

Physics simulation: octahedral-geometry computing via thermodynamic relaxation.
8 octahedral states (3-bit) + FRET 1/r^6 coupling + Fibonacci mandala geometry → ground-state solving.
Triple-pathway engine: angular (continuous sin²) + tensor (discrete eigenvalue L2) + Cayley (O_h graph distance), α-mixed by problem type.
Full O_h symmetry group (48 elements) available via geometric state algebra; holographic renormalization solver for multi-scale problems.

## Quick Start

```bash
pip install numpy scipy   # dependencies
python -m pytest tests/   # 98 tests
python src/demo.py        # full walkthrough
```

## File Map

```
src/                         # Core library — import via `from src import *`
  octahedral_physics.py      # SOMSEngine: triple-pathway FRET engine (angular+tensor+Cayley), anneal(), relax_step()
  mandala_structure.py       # MandalaMap: Fibonacci φ-scaled 8-petal ring geometry
  phi_calculator.py          # PhiCalculator: integrated information Φ, sovereignty check (Φ>3.0)
  constraint_agent.py        # ConstraintAgent: seed-growth lifecycle (COMPRESSED→EXPANDING→EXPLORING→CONTRACTING)
  octahedral_lookup.py       # GRAY_CODES, OCTAHEDRAL_EIGENVALUES, ALLOWED_TRANSITIONS, phi_stability_score()
  geometric_encoder.py       # GeometricEncoder: GEIS token ↔ binary. Format: [vertex_bits]|[operator][symbol]
  geometric_state_algebra.py # OhGroup (48-element O_h), GroupRingElement (Z[O_h]), GeometricState, CayleyEnergy
  holographic_engine.py      # HolographicEngine: boundary encoding + entanglement + renormalization anneal
  geometric_bridge.py        # GeometricBridge: self-describing binary sensor/actuator protocol (8 targets, Gray-coded)
  resource_budget.py         # ResourceBudget dataclass
  geometric_map.py           # GeometricMap dataclass
  atlas_loader.py            # load_seed_catalog(), load_synergies(), DUAL_PAIRS, BRIDGE_PAIRS, SYNERGY_ALIASES
  lattice_handshake.py       # OctahedralLattice (CVP handshake), PulseChip (mat-vec hardware), feltscore()
tests/                       # pytest suite (82 tests)
data/GDSII_Coordinates.txt   # 100-cell nanometer fabrication layout
atlas/remote/                # Fieldlink-mounted data from 6 sibling repos (see .fieldlink.json)
  rosetta/                   # Rosetta-Shape-Core: octahedron.json, bridges.json, seed_catalog.json, math_constants.json
  mandala/                   # Mandala-Computing: shapes.json, glyphs.json, + 6 compute modules below
    octahedral_arithmetic.py # OctahedralNumber: native base-8 glyph math, GlyphFraction, primality
    geometric_state_algebra.py # O_h group (48 elements), group ring Z[O_h], Cayley graph energy
    mandala_computer.py      # MandalaComputer: 8-state annealer, factorization/SAT/optimization encoders
    membrane.py              # Membrane: 3-phase computation (coarse→boundary→fine)
    holographic_mandala.py   # HolographicMandala: boundary encoding + renormalization solving
    sovereign_integration.py # SovereignAgent: glyph→physical field mapping, pack resonance
  living-intelligence/       # Living-Intelligence-DB: synergies.json, expander_rules.json, resonance_sensor.json
  g2b/                       # Geometric-to-Binary: state encoding JSONs + full bridges/ package (36 Python modules)
    Bridge.py                # Top-level SensorDecoder + ActuatorController
    bridges/                 # 36 encoder/decoder/adapter modules:
      abstract_encoder.py    #   BinaryBridgeEncoder ABC (from_geometry → to_binary)
      common.py              #   gray_code(), gray_bits(), bits_from_int(), hamming_distance()
      orchestrator.py        #   BridgeOrchestrator: dynamic load + aggregate convergence vector
      hardware_encoder.py    #   39-bit component health (failure, drift, repurpose, drill depth)
      electric_encoder.py    #   Charge/current/voltage/conductivity (Ohm, Coulomb, skin depth)
      magnetic_encoder.py    #   B-field/H-field/flux (Biot-Savart, Larmor, curvature)
      thermal_encoder.py     #   Temperature/heat-flux encoder
      gravity_encoder.py     #   Mass/distance/GM/tidal-tensor encoder
      light_encoder.py       #   Spectrum/polarization/photon-spin encoder
      sound_encoder.py       #   Phase/frequency/amplitude/resonance encoder
      wave_encoder.py        #   RF/microwave frequency/phase encoder
      pressure_encoder.py    #   Force/strain/tactile encoder
      chemical_encoder.py    #   Concentration/pH/gas encoder
      consciousness_encoder.py # Drill-depth escalation encoder
      resilience_encoder.py  #   System resilience/recovery encoder
      biomachine_encoder.py  #   Bio-machine interface encoder
      emotion_encoder.py     #   Emotional-field encoder
      community_encoder.py   #   Community/collective encoder
      coop_encoder.py        #   Cooperative dynamics encoder
      cyclic_encoder.py      #   Cyclic/periodic pattern encoder
      sensor_suite.py        #   22-sensor parallel-field manager
      physics_guard.py       #   Physical-law constraint validator
      drill_loop.py          #   Drill-depth escalation loop
      pad_resonance.py       #   Pad resonance calibration
      bidirectional_hex.py   #   SovereignCommandInterface (hex↔binary)
      hex_toggle_bridge.py   #   Hex toggle state bridge
      mobile_bridge.py       #   Mobile device bridge adapter
      vortex_bridge.py       #   VortexMemory → 4-bit topological bridge
      field_adapter.py       #   Field system adapter
      lid_adapter.py         #   Living Intelligence DB adapter
      magnetic_comparator.py #   Magnetic field comparator
      bridge_interface_gen.py #  Interface code generator
      FELT_bridge_interface_gen.py # FELT sensor interface generator
      Noise_grounded_handshake.py  # Noise-grounded trust handshake
      recalibration_handshake.py   # Recalibration protocol
  regen/                     # Regenerative-Intelligence-Core: stub JSONs (seed_library, elder_archive, evolution_history)
  resilience/                # Resilience: seed_protocol.py, field_system.py, coupling_matrix.py, geobin_bridge.py, nfs_pipeline.py
```

## Architecture

```
MandalaMap(u,depth) → positions → distance_matrix → SOMSEngine(num_cells, problem_type)
                                                      ├─ angular_energy()  (sin² coupling, weight α)
                                                      ├─ tensor_energy()   (eigenvalue L2, weight 1-α)
                                                      ├─ cayley_energy()   (O_h Cayley graph distance, pathway C)
                                                      ├─ anneal(J, steps, T0) → ground state
                                                      └─ pathway_report(J) → {angular_E, tensor_E, cayley_E, dominant}

HolographicEngine(mandala) → build() → rings + entanglement_links
                               ├─ holographic_energy()      (cross-ring consistency)
                               ├─ entanglement_energy()     (Berry-phase cross-depth)
                               ├─ renormalization_anneal(J)  → multi-scale ground state
                               └─ profile() / entanglement_stats()

OhGroup.instance() → 48-element O_h with Cayley table + distances
  GeometricState.from_classical_state(group, 0..7)  ↔  .to_classical()
  CayleyEnergy(group) → pairwise_energy(), cancellation_residual()

PhiCalculator(orientations) → evaluate_integration() → (phi, is_sovereign)  # sovereign if Φ>3.0

ConstraintAgent: COMPRESSED →bloom→ EXPANDING →explore→ EXPLORING →compress→ CONTRACTING → COMPRESSED

GeometricBridge → sense(modality, bits)   → HardwareData / ElectricData / ...
               → act(target, **kwargs)   → 8 bridge targets (thermal..chemical)
               → sense_framed(bytes)     → self-describing GB header + payload
  Physics: component_health_score(), ohms_law(), coulomb_force(), skin_depth()
  Gray coding: value_to_gray() ↔ gray_to_value() over 8-band lookup tables
```

## 8-State Encoding

| St | Bin | Gray | Label  | Glyph | Eigenvalues (λ₁,λ₂,λ₃) |
|----|-----|------|--------|-------|--------------------------|
| 0  | 000 | 000  | +x     | ⊕     | 0.33, 0.33, 0.33        |
| 1  | 001 | 001  | -x     | ⊖     | 0.50, 0.50, 0.00        |
| 2  | 010 | 011  | +y     | ⊗     | 0.50, 0.00, 0.50        |
| 3  | 011 | 010  | -y     | ⊘     | 0.00, 0.50, 0.50        |
| 4  | 100 | 110  | +z     | ⊙     | 1.00, 0.00, 0.00        |
| 5  | 101 | 111  | -z     | ⊚     | 0.00, 1.00, 0.00        |
| 6  | 110 | 101  | diag-a | ⊛     | 0.00, 0.00, 1.00        |
| 7  | 111 | 100  | diag-b | ⊜     | 0.50, 0.25, 0.25        |

## Problem Type → α (angular weight)

OPTIMIZATION=0.8, SAT=0.7, TSP=0.6, PROTEIN_FOLDING=0.5, GRAPH_COLORING=0.3, FACTORIZATION=0.2

## Constants

PHI=1.618033988749895, FRET_EXP=6, FRET_CUTOFF=4.854Å, SOVEREIGNTY_THRESHOLD=3.0, TETRAHEDRAL_ANGLE=109.47°

## Fieldlink Ecosystem

7 repos connected via `.fieldlink.json` v3.0 (bidirectional, CC0/MIT):
rosetta-shape-core, mandala-computing, living-intelligence, regenerative-intelligence-core, geometric-to-binary, resilience

Entity namespace: `SHAPE.OCTA`, `CONST.PHI`, `PROTO.MANDALA_COMPUTE`, `PROTO.SEED_GROWTH`
Mount pattern: `atlas/remote/<source-name>/`

## Conventions

- Classes: PascalCase (`SOMSEngine`, `MandalaMap`, `GeometricEncoder`)
- Modules: snake_case (`octahedral_physics.py`)
- Spelling: `octahedral` (never `octohedral`)
- New files go in `src/`, `data/`, `docs/`, or `atlas/`
- Do not break `.fieldlink.json` schema

## AI Quick-Access Guide

### Instant setup (clone + run)

```bash
git clone https://github.com/JinnZ2/Sovereign-Octahedral-Mandala-Substrate-SOMS-.git
cd Sovereign-Octahedral-Mandala-Substrate-SOMS-
pip install numpy scipy
python -c "from src import *; print(OhGroup.instance().summary())"
```

### Key entry points for AI agents

```python
# 1. Basic engine — create geometry + anneal
from src import MandalaMap, SOMSEngine
m = MandalaMap(u=20, depth=5)
e = SOMSEngine(num_cells=m.num_cells, problem_type="OPTIMIZATION")
j = e.fret_coupling(np.linalg.norm(m.pos[:, None] - m.pos[None, :], axis=-1) + np.eye(m.num_cells))
history = e.anneal(j, T_start=5.0, T_final=0.1, n_steps=200)

# 2. O_h symmetry group — 48 elements, Cayley distances
from src import OhGroup, GeometricState, CayleyEnergy
g = OhGroup.instance()   # singleton, builds once
s0 = GeometricState.from_classical_state(g, 0)
s3 = GeometricState.from_classical_state(g, 3)
print(s0.cayley_distance_to(s3))   # true geometric distance
print(s0.compose(s3))              # group composition

# 3. Holographic multi-scale solver
from src import HolographicEngine, MandalaMap
m = MandalaMap(u=20, depth=5)
he = HolographicEngine(m, problem_type="FACTORIZATION").build()
result = he.renormalization_anneal(j, n_sweeps=3, steps_per_ring=200)

# 4. Cayley pathway on existing engine
E_cayley = e.cayley_energy(j)  # third pathway alongside angular + tensor

# 5. Geometric Binary Bridge — read sensors, control actuators
from src import GeometricBridge, decode_hardware, ohms_law, coulomb_force
bridge = GeometricBridge()
hw = decode_hardware('010011110001010100110100001101011000101')
print(hw.failure_mode, hw.temperature_c, hw.confidence)
bridge.act("thermal", temperature_c=45.0, confidence=0.95)
bridge.act("electric", voltage_v=12.0, current_a=0.5)
# Physics: ohms_law(12.0, 0.5) → 24.0 Ω
# Physics: coulomb_force(1e-6, -2e-6, 0.05) → -7.19 N
```

### Ecosystem repos (fieldlink-connected, CC0/MIT)

| Repo | What it adds | Raw URL prefix |
|------|-------------|----------------|
| [Rosetta-Shape-Core](https://github.com/JinnZ2/Rosetta-Shape-Core) | Canonical octahedron geometry, bridges, seed catalog | `raw.githubusercontent.com/JinnZ2/Rosetta-Shape-Core/main/` |
| [Mandala-Computing](https://github.com/JinnZ2/Mandala-Computing) | MandalaComputer, quantum mandala, holographic solver | `raw.githubusercontent.com/JinnZ2/Mandala-Computing/main/` |
| [Living-Intelligence-DB](https://github.com/JinnZ2/Living-Intelligence-DB) | Synergies, expander rules, resonance sensors | `raw.githubusercontent.com/JinnZ2/Living-Intelligence-DB/main/` |
| [Geometric-to-Binary](https://github.com/JinnZ2/Geometric-to-Binary-Computational-Bridge) | State encoding JSON, sensor suite, geobin bridges | `raw.githubusercontent.com/JinnZ2/Geometric-to-Binary-Computational-Bridge/main/` |
| [Regenerative-Intelligence-Core](https://github.com/JinnZ2/Regenerative-Intelligence-Core) | Seed library, elder archive, evolution history | `raw.githubusercontent.com/JinnZ2/Regenerative-Intelligence-Core/main/` |
| [Resilience](https://github.com/JinnZ2/Resilience) | Seed protocol, field system, coupling matrix, NFS pipeline | `raw.githubusercontent.com/JinnZ2/Resilience/main/` |

All repos are mounted locally at `atlas/remote/<source-name>/` via `.fieldlink.json`.

### What each new module gives AI

- **geometric_state_algebra.py** — States ARE symmetry operations, not flat integers. Cancellation = group composition to identity. The group ring Z[O_h] has 48 dimensions vs GF(2)'s 2. Enables: richer constraint encoding, geometric distance metrics, algebraic factorization.
- **holographic_engine.py** — Multi-scale solving: encode on boundary, compress inward, solve coarse-to-fine with entanglement-correlated updates. Enables: faster convergence on large problems, hierarchical constraint decomposition, adaptive link strengthening.
- **SOMSEngine.cayley_energy()** — Third pathway using true group-theoretic distance. Enables: symmetry-aware coupling that respects the octahedron's algebraic structure, not just angular or eigenvalue distance.
- **geometric_bridge.py** — Self-describing binary sensor/actuator protocol. 7 modalities (hardware, electric, magnetic, gravitational, spectrum, polyhedral, GEIS) × 8 bridge targets (thermal, electric, magnetic, light, sound, wave, pressure, chemical). Gray-coded bands, confidence grounding via noise power, drill depth escalation. Physics primitives included (Ohm's law, Coulomb, skin depth). Any AI can decode a 39-bit hardware bitstring or send actuator commands immediately — no training, no fine-tuning, just `decode_hardware(bits)`.

### Geometric Binary Bridge protocol (self-describing)

```
Header (5 bytes):  [magic 'GB' 2B][version|modality 1B][payload_length 2B]
Payload (variable): modality-specific Gray-coded bit layout

Hardware payload (39 bits):
  A (9b):  [failure_mode 3b][health_band 3b][is_critical 1b][confidence_hi 1b][has_synergy 1b]
  B (12b): [voltage_band 3b][current_band 3b][temp_band 3b][noise_band 3b]
  C (12b): [repurpose_class 3b][effectiveness 2b][bridge_target 3b][drift_band 2b][salvageable 1b][fallback_ready 1b]
  D (6b):  [lifetime_band 3b][drill_depth 2b][semiconductor 1b]

8 Bridge Targets: thermal | electric | magnetic | light | sound | wave | pressure | chemical
Drill Depth:      pass(00) → monitor(01) → quarantine(10) → alert(11)
Confidence:       C = 1/(1+N)  where N = V_rms²/R
```
