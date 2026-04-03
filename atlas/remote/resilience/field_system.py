#!/usr/bin/env python3
"""
Field System — Minimal Portable Rule-Field Engine for Regenerative System Tracking

Models agricultural/ecological systems as thermodynamic entities with
constraint layers, drift detection, and ecological coupling amplification.

Core concepts:
  - Regeneration Capacity (rc): proxy for system self-renewal, derived from
    soil trend, water retention, and disturbance levels
  - Constraint Layer: invariant rules that must hold for system health —
    soil non-degradation, water retention, no overextraction, energy ratio
  - Drift Detection: identifies when the system violates constraints
  - Ecological Coupling: the amplification factor g(k) = 1 + α·k where
    wild/ecological area feeds back into production yield
  - Effective Yield: adjusted for waste, nutrient density, and coupling —
    H_total = Y_eff × production_area
  - Thermal Limit: prediction error (model/reality dissonance) and thermal
    load detection — flags when the system is "redlining"

The "Sovereign Steward" vs "Big Ag-Bot" comparison demonstrates that
30 acres with high coupling (k=0.9) can produce 2.55x more true
nourishment than 200 acres of monocrop with zero coupling.

References:
  - Prigogine (1967): dissipative structures — open system self-organization
  - Odum (1971): energy systems language — emergy and energy hierarchy
  - Holling (1973): resilience and stability of ecological systems
  - Altieri (1995): agroecology — the science of sustainable agriculture
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict


# ---------------------------------------------------------------------------
# Defaults / Baselines
# ---------------------------------------------------------------------------

DEFAULTS: Dict[str, float] = {
    "soil_trend": 0.0,              # change per unit time
    "water_retention": 0.5,         # 0–1 proxy
    "input_energy": 1.0,            # arbitrary units
    "output_yield": 1.0,            # arbitrary units
    "disturbance": 0.0,             # 0–1 proxy
    "waste_factor": 0.4,            # 0–1
    "nutrient_density": 0.8,        # 0–1
    "production_area": 30,          # acres
    "ecological_area": 170,         # acres
    "coupling_strength": 1.0,       # 0–1
    "ecological_amplification": 2.0,  # max factor g(k) = 1 + alpha * k
}

BASELINES: Dict[str, float] = {
    "water_retention_min": 0.4,
    "energy_ratio_min": 1.0,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fill_state(state: Dict[str, Any]) -> Dict[str, float]:
    """Fill missing values with defaults."""
    return {k: float(state.get(k, DEFAULTS[k])) for k in DEFAULTS}


def regen_capacity(state: Dict[str, float]) -> float:
    """Proxy regeneration capacity.

    rc = base × (1 + soil_trend) × water_retention × (1 - disturbance)

    A healthy system has rc ≥ 1.0. Degrading soil, poor water retention,
    or high disturbance drive rc below 1.0, meaning the system cannot
    sustain its current extraction rate.
    """
    base = 1.0
    soil_factor = 1.0 + state["soil_trend"]
    water_factor = state["water_retention"]
    disturbance_penalty = 1.0 - state["disturbance"]
    return base * soil_factor * water_factor * disturbance_penalty


# ---------------------------------------------------------------------------
# Constraint Layer (Invariant)
# ---------------------------------------------------------------------------

def constraints(state: Dict[str, float]) -> Dict[str, bool]:
    """Evaluate system health constraints. All must be True for sustainability."""
    rc = regen_capacity(state)
    return {
        "soil_positive": state["soil_trend"] >= 0,
        "water_non_degrading": state["water_retention"] >= BASELINES["water_retention_min"],
        "no_overextraction": state["output_yield"] <= rc,
        "energy_ratio": (
            state["output_yield"] / state["input_energy"]
            if state["input_energy"] > 0 else 0
        ) >= BASELINES["energy_ratio_min"],
    }


# ---------------------------------------------------------------------------
# Drift Detection
# ---------------------------------------------------------------------------

def drift(state: Dict[str, float]) -> Dict[str, bool]:
    """Detect constraint violations (drift = True means that constraint is violated)."""
    c = constraints(state)
    return {k: not v for k, v in c.items()}


# ---------------------------------------------------------------------------
# Adaptive Suggestions
# ---------------------------------------------------------------------------

def suggest(state: Dict[str, float]) -> Dict[str, Any]:
    """Generate corrective actions for violated constraints."""
    issues = drift(state)
    actions = []

    if issues["soil_positive"]:
        actions.append("Increase biomass input, reduce tillage/disturbance")
    if issues["water_non_degrading"]:
        actions.append("Improve water retention (mulch, contouring, infiltration)")
    if issues["no_overextraction"]:
        actions.append("Reduce yield pressure or increase regeneration capacity")
    if issues["energy_ratio"]:
        actions.append("Reduce external inputs or improve system efficiency")

    return {
        "issues": issues,
        "actions": actions,
    }


# ---------------------------------------------------------------------------
# Effective Yield & Coupling
# ---------------------------------------------------------------------------

def effective_yield(state: Dict[str, float]) -> Dict[str, float]:
    """Calculate yield adjusted for waste, nutrients, and ecological coupling.

    Y_adj = Y_g × (1 - W_f) × N_d²
    g(k) = 1 + α × k   (ecological amplification)
    Y_eff = Y_adj × g(k)
    H_total = Y_eff × production_area
    """
    wf = state["waste_factor"]
    nd = state["nutrient_density"]
    yg = state["output_yield"]

    # Adjust for waste and nutrient density
    y_adj = yg * (1 - wf) * nd ** 2

    # Ecological coupling amplification
    alpha = state["ecological_amplification"]
    k = state["coupling_strength"]
    gk = 1 + alpha * k

    y_eff = y_adj * gk

    # Total system output
    h_total = y_eff * state["production_area"]

    return {
        "adjusted_yield": round(y_adj, 4),
        "ecological_amplification_factor": round(gk, 4),
        "effective_yield_per_acre": round(y_eff, 4),
        "total_nourishment_units": round(h_total, 4),
    }


# ---------------------------------------------------------------------------
# Thermal Limit Detection
# ---------------------------------------------------------------------------

def thermal_limit_check(state: Dict[str, float]) -> Dict[str, Any]:
    """Detect when the system is redlining or leaking heat.

    Prediction Error = |output_yield - regen_capacity|
    Thermal Load = disturbance × input_energy

    High prediction error = model/reality dissonance.
    High thermal load = system overheating from forced extraction.
    """
    pe = abs(state["output_yield"] - regen_capacity(state))
    thermal_load = state["disturbance"] * state["input_energy"]
    limit_reached = thermal_load > 0.8 or pe > 0.5

    return {
        "prediction_error": round(pe, 4),
        "thermal_load": round(thermal_load, 4),
        "critical_alert": limit_reached,
        "instruction": "REDUCE VELOCITY / INCREASE REST" if limit_reached else "NOMINAL",
    }


# ---------------------------------------------------------------------------
# Scoring / Diagnostics
# ---------------------------------------------------------------------------

def score(state: Dict[str, float]) -> float:
    """Overall health score: fraction of constraints satisfied."""
    c = constraints(state)
    return sum(c.values()) / len(c)


def report(state: Dict[str, Any]) -> Dict[str, Any]:
    """Full diagnostic report for a system state."""
    s = fill_state(state)
    return {
        "state": s,
        "constraints": constraints(s),
        "drift": drift(s),
        "score": score(s),
        "regen_capacity": round(regen_capacity(s), 4),
        "suggestions": suggest(s),
        "yield_analysis": effective_yield(s),
        "thermal_limit": thermal_limit_check(s),
    }


# ---------------------------------------------------------------------------
# Scenario Comparison
# ---------------------------------------------------------------------------

SCENARIOS = {
    "sovereign_steward": {
        "soil_trend": 0.1,
        "water_retention": 0.7,
        "input_energy": 0.5,
        "output_yield": 1.0,
        "disturbance": 0.1,
        "waste_factor": 0.1,
        "nutrient_density": 0.9,
        "production_area": 30,
        "ecological_area": 170,
        "coupling_strength": 0.9,
        "ecological_amplification": 2.0,
    },
    "big_ag_bot": {
        "soil_trend": -0.2,
        "water_retention": 0.35,
        "input_energy": 3.0,
        "output_yield": 2.5,
        "disturbance": 0.4,
        "waste_factor": 0.7,
        "nutrient_density": 0.4,
        "production_area": 200,
        "ecological_area": 0,
        "coupling_strength": 0.0,
        "ecological_amplification": 1.0,
    },
}
