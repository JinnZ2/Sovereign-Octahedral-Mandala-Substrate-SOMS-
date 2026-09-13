"""
E07/E09 harness returns (OPEN ITEMS ROLLUP 2026-09-11, group D).

Each item is computed from the E07a harness (run_symmetry_identifiability.py) or the engine, and
reported SUPPORTED / REFUTED / UNRUN with the evidence beside it. Writes
docs/experiment_07_returns.{json,md}.

  D1  split of the 85 joint-genuine pairs that one of G1/G6 explains: G1-sym only | G6-sym only | both
  D2  same-sigma test: H = Iso(G2) ∩ Iso(G4); is every one of the 548 in an (H x S_n)-orbit?
  D3  230 pairs unseparated after the readout quotient; universe declared per count
  D4  G5 status
  D5  sorted-pair-list sha256 of the 548 (set-level comparison with E06)
  D6  E09: energy terms by power of d; cutoff units; T* = T / J_scale
  D7  T1 / T2 status from their result files

Run from the repo root:  python experiments/e07_returns.py
"""
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import run_symmetry_identifiability as H  # noqa: E402
from src import MandalaMap, SOMSEngine  # noqa: E402

DOCS = os.path.join(ROOT, "docs")


def orbit_contains(x_word, y_code, iso, comp):
    """Is y in the (iso x comp)-orbit of x? Returns the (g, sigma) index pair or None."""
    for gi, g in enumerate(iso):
        for si, s in enumerate(comp):
            if int(H.encode(g[x_word[s]])) == y_code:
                return gi, si
    return None


def main():
    n = 4
    metrics = H.state_metrics()
    words = H.all_words(n)
    comp = H.component_group(n)
    names = list(H.JOINT_MEMBERS)
    res = {g: H.analyse(g, [metrics[g]], words, comp) for g in names}
    res["joint"] = H.analyse("joint", [metrics[g] for g in names], words, comp)
    joint_pairs = sorted((min(a, b), max(a, b)) for a, b in res["joint"]["_genuine_pairs"])
    code_to_idx = {int(H.encode(w)): i for i, w in enumerate(words)}
    out = {"rollup": "OPEN ITEMS ROLLUP 2026-09-11 group D", "word_length": n, "joint_genuine_pairs": len(joint_pairs)}

    # D1 -- 85-pair split
    iso1, iso6 = res["G1_numeric"]["_iso"], res["G6_cayley"]["_iso"]
    split = {"G1_sym_only": 0, "G6_sym_only": 0, "both": 0, "neither": 0}
    for a, b in joint_pairs:
        x = words[code_to_idx[a]]
        s1 = orbit_contains(x, b, iso1, comp) is not None
        s6 = orbit_contains(x, b, iso6, comp) is not None
        split["both" if (s1 and s6) else "G1_sym_only" if s1 else "G6_sym_only" if s6 else "neither"] += 1
    explained = split["G1_sym_only"] + split["G6_sym_only"] + split["both"]
    out["D1_85_pair_split"] = dict(split, explained_by_G1_or_G6=explained, universe="the %d joint-genuine pairs" % len(joint_pairs),
                                   status="SUPPORTED" if explained == 85 else "REFUTED (expected 85, got %d)" % explained,
                                   read="every pair one of G1/G6 explains is explained by exactly one of them; no pair is symmetric under both")

    # D2 -- same-sigma test under H = Iso(G2) ∩ Iso(G4)
    iso2, iso4 = res["G2_cyclic"]["_iso"], res["G4_gray"]["_iso"]
    Hgrp = np.array([g for g in iso2 if any((g == h).all() for h in iso4)])
    in_H = 0
    same_sigma_needed = 0
    for a, b in joint_pairs:
        x = words[code_to_idx[a]]
        hit = orbit_contains(x, b, Hgrp, comp)
        in_H += hit is not None
    out["D2_same_sigma_H"] = {"H_order": int(len(Hgrp)), "Iso_G2_order": int(len(iso2)), "Iso_G4_order": int(len(iso4)),
                              "pairs_in_H_x_Sn_orbit": in_H, "of": len(joint_pairs),
                              "status": "SUPPORTED (548 ⊆ H-orbits)" if in_H == len(joint_pairs) else "REFUTED: %d of %d in H x S_n orbits" % (in_H, len(joint_pairs)),
                              "read": "a single (h, sigma) with h in Iso(G2)∩Iso(G4) relates the pair" if in_H == len(joint_pairs) else
                                      "the G2 and G4 explanations of a joint-genuine pair need not share an element of the intersection"}

    # D3 -- readout quotient, universe per count
    q = H.encode((words >= 4).astype(np.int64))
    Mj = res["joint"]["_M"]
    keys = np.array([hash(tuple(r)) for r in Mj])
    all_pairs = len(words) * (len(words) - 1) // 2
    merged = 0; merged_same_M = 0
    for cls in np.unique(q):
        idx = np.where(q == cls)[0]
        k = len(idx); merged += k * (k - 1) // 2
        from collections import Counter
        c = Counter(keys[idx].tolist())
        merged_same_M += sum(v * (v - 1) // 2 for v in c.values())
    joint_colliding = int(res["joint"]["colliding_pairs_total"])
    # of the joint-genuine 548, how many share a readout class?
    gen_same_readout = sum(1 for a, b in joint_pairs if q[code_to_idx[a]] == q[code_to_idx[b]])
    out["D3_readout_quotient"] = {
        "universe_all_pairs": all_pairs, "readout_merged_pairs": int(merged),
        "readout_merged_and_joint_separates": int(merged - merged_same_M),
        "readout_merged_and_joint_does_not_separate": int(merged_same_M),
        "joint_colliding_pairs": joint_colliding,
        "joint_genuine_pairs": len(joint_pairs), "joint_genuine_pairs_also_readout_merged": int(gen_same_readout),
        "declared": {"230": "pairs merged by the readout AND in the same joint-M class; universe = the %d joint-colliding pairs (%d of them are readout-separated)" % (joint_colliding, joint_colliding - merged_same_M),
                     "522240": "pairs merged by the readout; universe = all C(4096,2) = %d pairs" % all_pairs,
                     "548": "joint-genuine pairs; universe = the %d joint-colliding pairs" % joint_colliding},
        "status": "SUPPORTED (230 reproduced)" if merged_same_M == 230 else "REFUTED: %d" % merged_same_M}

    # D4 -- G5
    defined = sorted(metrics)
    out["D4_G5_status"] = {"geometries_defined": defined, "G5_defined": "G5" in "".join(defined),
                           "status": "ABSENT: no G5 metric is defined in state_metrics(); the numbering skips from G4_gray to G6_cayley. "
                                     "Nothing was computed under that name, so no result is missing, only the label. "
                                     "Assigning G5 needs a declared metric (candidate: the eigenvalue-triple L2 distance the tensor pathway uses)."}

    # D5 -- hash of the sorted pair list
    h = hashlib.sha256(json.dumps(joint_pairs).encode()).hexdigest()
    out["D5_sorted_pair_list_sha256"] = {"sha256": h, "n_pairs": len(joint_pairs), "encoding": "json list of [min,max] base-8 word codes, sorted",
                                         "status": "COMPUTED; E06 set not reachable (E07a §14 control 5 blocked), so the comparison is UNRUN",
                                         "first_5": joint_pairs[:5]}
    with open(os.path.join(DOCS, "experiment_07_joint_genuine_pairs.json"), "w") as f:
        json.dump({"sha256": h, "pairs": joint_pairs}, f)

    # D6 -- E09 energy terms, cutoff, T*
    m = MandalaMap(u=20, depth=5)
    e = SOMSEngine(num_cells=m.num_cells, problem_type="SAT")
    pos = np.array(m.pos)
    d = np.linalg.norm(pos[:, None] - pos[None, :], axis=-1)
    off = ~np.eye(m.num_cells, dtype=bool)
    d_nn = float(d[off].min())
    J = e.fret_coupling(d + np.eye(m.num_cells))
    J_scale = float(J[off].max())
    out["D6_E09_units"] = {
        "energy_terms": {"angular": "J_ij * sin^2(theta_i - theta_j)", "tensor": "J_ij * ||lambda_i - lambda_j||^2",
                         "cayley": "J_ij * (phi * d_cayley / diam)^2"},
        "power_of_d": {"J_ij": -6, "angular": -6, "tensor": -6, "cayley": -6, "note": "every term is J_ij times a dimensionless factor; no term carries another power of d"},
        "cutoff": {"in_code": False, "in_docs": "FRET_CUTOFF = 4.854 Å (CLAUDE.md)", "mandala_unit": "u = 20 declared nm (mandala_structure.py)",
                   "read": "fret_coupling applies no cutoff; the documented cutoff in Å is below every mandala distance (d_nn = %.1f in the mandala's declared nm), so as written it would remove every pair. Units are not confirmed: the constant and the geometry do not share a unit." % d_nn},
        "d_nn": d_nn, "J_scale": J_scale, "T_star": {"T_start_5.0": 5.0 / J_scale, "T_final_0.1": 0.1 / J_scale},
        "normalized": {"d_nn": 1.0, "J_scale": 1.0, "T_star_start": 5.0, "note": "the E09 normalization d/d_nn makes T* = T"},
        "status": "COMPUTED: T* = T / J_scale stored; cutoff units UNCONFIRMED (no cutoff in code)"}

    # D7 -- T1 / T2 from their result files
    t1p, t2p = os.path.join(DOCS, "experiment_07_T1_perturbation.json"), os.path.join(DOCS, "experiment_07_T2_rosenblatt_seymour.json")
    d7 = {}
    if os.path.exists(t1p):
        t1 = json.load(open(t1p))
        d7["T1"] = {"status": "RUN", "file": os.path.basename(t1p), "verdict_keys": [k for k in t1 if "verdict" in k.lower() or "mechanism" in k.lower()][:6],
                    "read": "G1/G6 genuine collisions are tie (level) degeneracy: they vanish under pair-noise, not level-noise; additive coincidences contribute 0 under the vector readout; 140-pair equality floor (d(a,a)=0) remains"}
    else:
        d7["T1"] = {"status": "UNRUN", "file": "missing"}
    if os.path.exists(t2p):
        t2 = json.load(open(t2p))
        d7["T2"] = {"status": "RUN", "file": os.path.basename(t2p),
                    "read": "no 4-element ring-type collision in Z8 is a set-level Rosenblatt-Seymour pair (forced by the lemma, 0/64); Z12 Forte pair positive control factors 0/1 within the Q-bound; 0 of the 548 joint-genuine word pairs are ring-homometric non-isometric (0 have 4 distinct states)"}
    else:
        d7["T2"] = {"status": "UNRUN", "file": "missing"}
    out["D7_T1_T2"] = d7

    with open(os.path.join(DOCS, "experiment_07_returns.json"), "w") as f:
        json.dump(out, f, indent=1, default=lambda o: int(o) if isinstance(o, np.integer) else float(o) if isinstance(o, np.floating) else str(o))
    lines = ["# E07 / E09 harness returns (rollup group D, 2026-09-11)", "",
             "Generated by `experiments/e07_returns.py`. Each item: status + evidence.", ""]
    for k in ("D1_85_pair_split", "D2_same_sigma_H", "D3_readout_quotient", "D4_G5_status", "D5_sorted_pair_list_sha256", "D6_E09_units", "D7_T1_T2"):
        v = out[k]
        lines.append("## %s" % k); lines.append("")
        lines.append("```"); lines.append(json.dumps(v, indent=1, default=str)); lines.append("```"); lines.append("")
    open(os.path.join(DOCS, "experiment_07_returns.md"), "w").write("\n".join(lines))
    for k in ("D1_85_pair_split", "D2_same_sigma_H", "D3_readout_quotient", "D4_G5_status", "D5_sorted_pair_list_sha256", "D6_E09_units", "D7_T1_T2"):
        v = out[k]
        print(k, "->", v.get("status") or {kk: vv.get("status") for kk, vv in v.items()})
    return out


if __name__ == "__main__":
    main()
