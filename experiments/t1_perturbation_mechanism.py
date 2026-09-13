"""
T1 — Perturbation on G1/G6: algebraic degeneracy vs readout coarseness
=======================================================================
Question. E07a found 8648 genuine (non-isometric) collision pairs under G1
and 20131 under G6 on 4-cell words. A generic real-valued metric produces
non-isometric collisions with measure zero, so one of two mechanisms is
operating:

  (a) readout coarseness    the readout merges distinct relation vectors
                            (multiset, sum, binning, rounding)
  (b) metric degeneracy     the metric's values coincide in ways a generic
                            metric's would not. Two sub-kinds:
        (b-tie)  many state pairs share one distance level
                 (G1 |a-b| has 7 levels for 28 pairs; G6 has 5)
        (b-add)  additive coincidences among levels (1+2 = 3, phi^2 = phi+1)

Design. 3 readouts x 3 perturbations, per geometry.

  readouts       vector   M_R(x) ordered upper triangle       (E07a's readout)
                 multiset sorted M_R(x)                        (homometry / Patterson)
                 sum      sum of M_R(x)                        (scalar)
  perturbations  none
                 level    d(a,b) -> d(a,b) + eps[level of d(a,b)]   keeps ties, kills additive relations
                 pair     d(a,b) -> d(a,b) + eps[{a,b}]             kills ties and additive relations

Predictions (exact-equality readouts)
  vector:   none == level  (only ties matter);   pair -> ~0
  multiset: none != level  iff additive coincidences contribute
            level != pair  iff ties contribute
  sum:      coarsest; survives pair-noise only through exact multiset equality

"Genuine" is always measured against the perturbed metric's own isometry
group (brute force over S_8), so a perturbation that breaks a symmetry is
charged to the symmetry, not miscounted as a new collision.

Run: python experiments/t1_perturbation_mechanism.py  (from repo root)
"""
import json
import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import run_symmetry_identifiability as e07  # noqa: E402


def perturb(d, kind, rng, scale=1e-2):
    d = d.astype(float).copy()
    n = d.shape[0]
    if kind == "none":
        return d
    if kind == "level":
        levels = sorted(set(d[~np.eye(n, dtype=bool)].tolist()))
        eps = {lv: rng.uniform(0, scale) for lv in levels}
        out = d.copy()
        for a in range(n):
            for b in range(n):
                if a != b:
                    out[a, b] = d[a, b] + eps[d[a, b]]
        return out
    if kind == "pair":
        out = d.copy()
        for a in range(n):
            for b in range(a + 1, n):
                e = rng.uniform(0, scale)
                out[a, b] += e
                out[b, a] += e
        return out
    raise ValueError(kind)


def readout_keys(M, kind):
    if kind == "vector":
        return [tuple(np.round(r, 9)) for r in M]
    if kind == "multiset":
        return [tuple(np.round(np.sort(r), 9)) for r in M]
    if kind == "sum":
        return [round(float(r.sum()), 9) for r in M]
    raise ValueError(kind)


def run(n=4, seed=0, geometries=("G1_numeric", "G6_cayley", "G2_cyclic", "G4_gray")):
    rng = np.random.RandomState(seed)
    metrics = e07.state_metrics()
    words = e07.all_words(n)
    comp = e07.component_group(n)
    out = {"word_length": n, "seed": seed, "cells": {}}
    for g in geometries:
        for pert in ("none", "level", "pair"):
            d = perturb(metrics[g], pert, rng)
            iso = e07.isometry_group(d)
            comp_img, iso_img, comb_img = e07.images(words, iso, comp)
            M = e07.relation_matrix(d, words)
            for ro in ("vector", "multiset", "sum"):
                classes = e07.classes_from_keys(readout_keys(M, ro))
                n_pairs, lat, prec, gp = e07.classify_pairs(classes, comp_img, iso_img, comb_img)
                sizes = [len(v) for v in classes.values()]
                out["cells"][f"{g}|{pert}|{ro}"] = {
                    "geometry": g, "perturbation": pert, "readout": ro,
                    "iso_order": int(len(iso)), "classes": int(len(classes)),
                    "colliding_pairs": int(n_pairs),
                    "genuine_pairs": int(len(gp)),
                    "L_R_bits": float(np.log2(len(words)) - e07.entropy_bits(sizes, len(words))),
                }
    # mechanism decomposition per geometry
    verdicts = {}
    for g in geometries:
        c = lambda p, r: out["cells"][f"{g}|{p}|{r}"]["genuine_pairs"]
        v = {
            "vector": {"none": c("none", "vector"), "level": c("level", "vector"), "pair": c("pair", "vector")},
            "multiset": {"none": c("none", "multiset"), "level": c("level", "multiset"), "pair": c("pair", "multiset")},
            "sum": {"none": c("none", "sum"), "level": c("level", "sum"), "pair": c("pair", "sum")},
        }
        # The equality tie d(a,a) = 0 survives every perturbation. Under the vector readout
        # at n=4 it produces exactly C(8,2)*(1 + 4) = 140 label-swap pairs: constant words
        # (a,a,a,a)~(b,b,b,b) and the four 3+1 patterns (a,a,a,b)~(b,b,b,a). These are pairs
        # a relational representation cannot see by construction (no external label).
        floor_vec = v["vector"]["pair"]
        floor_expected = 28 * (1 + n)
        add_vec = v["vector"]["none"] - v["vector"]["level"]
        tie_vec = v["vector"]["level"] - v["vector"]["pair"]
        add_ms = v["multiset"]["none"] - v["multiset"]["level"]
        tie_ms = v["multiset"]["level"] - v["multiset"]["pair"]
        add_sum = v["sum"]["none"] - v["sum"]["level"]
        if v["vector"]["none"] == 0:
            tie_vec = 0
            mech = (f"no genuine collisions under the vector readout; the {floor_vec} floor pairs appear "
                    f"under pair-noise only because the perturbation destroys the label isometry that "
                    f"explained them (transitive Iso), not because a new collision was created")
        elif add_vec == 0:
            mech = (f"(b-tie) level degeneracy: {tie_vec} pairs vanish under pair-noise, 0 under "
                    f"level-noise; additive coincidences contribute nothing; {floor_vec} remain as the "
                    f"equality floor (d(a,a)=0), which is relational label-blindness, not (a) or (b)")
        else:
            mech = f"(b-add) additive coincidence contributes {add_vec} pairs under the vector readout"
        verdicts[g] = {"genuine_by_readout_and_perturbation": v,
                       "equality_floor_pairs": floor_vec,
                       "equality_floor_expected_28x(1+n)": floor_expected,
                       "vector_additive_contribution": add_vec,
                       "vector_tie_contribution": tie_vec,
                       "multiset_additive_contribution": add_ms,
                       "multiset_tie_contribution": tie_ms,
                       "sum_additive_contribution": add_sum,
                       "mechanism_for_E07a_readout": mech}
    out["verdicts"] = verdicts
    return out


def write_md(out, path):
    L = []
    w = L.append
    w("# T1 — Perturbation on G1/G6: degeneracy vs readout coarseness\n")
    w("Generated by `experiments/t1_perturbation_mechanism.py`. Genuine = colliding pairs outside "
      "the perturbed metric's own Iso×S_n orbit.\n")
    w("| geometry | perturbation | \\|Iso\\| | readout | classes | colliding pairs | genuine | L_R bits |")
    w("|---|---|---|---|---|---|---|---|")
    for k, c in out["cells"].items():
        w(f"| {c['geometry']} | {c['perturbation']} | {c['iso_order']} | {c['readout']} | {c['classes']} | "
          f"{c['colliding_pairs']} | {c['genuine_pairs']} | {c['L_R_bits']:.3f} |")
    w("\n## Mechanism decomposition (genuine pairs)\n")
    w("| geometry | readout | none | level-noise | pair-noise | additive contribution | tie contribution |")
    w("|---|---|---|---|---|---|---|")
    for g, v in out["verdicts"].items():
        for ro in ("vector", "multiset", "sum"):
            r = v["genuine_by_readout_and_perturbation"][ro]
            add = r["none"] - r["level"]
            tie = r["level"] - r["pair"]
            w(f"| {g} | {ro} | {r['none']} | {r['level']} | {r['pair']} | {add} | {tie} |")
    w("\n## Verdict per geometry (for the E07a vector readout)\n")
    for g, v in out["verdicts"].items():
        w(f"- **{g}**: {v['mechanism_for_E07a_readout']}")
    w("")
    w("Reading: under the exact-vector readout only ties can produce a collision, so additive "
      "coincidences (1+2=3, φ²=φ+1) are structurally irrelevant to the E07a counts. On these metrics "
      "they are also irrelevant under the multiset readout (none == level); they appear only under the "
      "scalar sum. The pair-noise residual is the equality floor: d(a,a)=0 is the one tie no generic "
      "perturbation removes, and it yields exactly 28·(1+n) = 140 label-swap pairs at n=4 (constant "
      "words and 3+1 patterns) that no relational representation can separate without an external label.")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    out = run()
    docs = os.path.join(ROOT, "docs")
    with open(os.path.join(docs, "experiment_07_T1_perturbation.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    write_md(out, os.path.join(docs, "experiment_07_T1_perturbation.md"))
    for g, v in out["verdicts"].items():
        r = v["genuine_by_readout_and_perturbation"]
        print(f"{g:11s} vector none/level/pair = {r['vector']['none']}/{r['vector']['level']}/{r['vector']['pair']}   "
              f"multiset = {r['multiset']['none']}/{r['multiset']['level']}/{r['multiset']['pair']}   "
              f"sum = {r['sum']['none']}/{r['sum']['level']}/{r['sum']['pair']}")
        print(f"            -> {v['mechanism_for_E07a_readout']}")
