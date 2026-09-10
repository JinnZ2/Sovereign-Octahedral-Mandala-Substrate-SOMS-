"""
E07a — Symmetry, Identifiability, and Information Loss (static arm)
====================================================================
Work order: docs/experiment_07_symmetry_identifiability_report.md (generated
by this script) states hypotheses, controls and results.

Objects
-------
State space          : words x in {0..7}^n            (n = 4 by default, |X| = 4096)
Geometry R           : a metric d_R on the 8 states   (8x8 integer/float matrix)
Relational rep       : M_R(x) = ( d_R(x_i, x_j) )_{i<j}
Collision            : x ~_R y  <=>  M_R(x) == M_R(y)
Label isometry group : Iso(d_R) = { g in S_8 : d_R(g a, g b) = d_R(a, b) }
Component group      : S_n acting on positions
Combined group       : Iso(d_R) x S_n acting on words, y = g(x o sigma)
Information loss     : L_R = log2|X| - H([X]_R)  under UNIFORM measure on X
Decomposition        : L_R = L_sym + L_excess
                       L_sym    = log2|X| - H(Iso-orbits)   (removed by declared symmetry)
                       L_excess = H(Iso-orbits) - H(classes) (representation loss beyond symmetry)

Every quantity is computed by exhaustive enumeration; nothing is sampled
except the more-data control, which is seeded.

Geometries
----------
G1 numeric : |a - b|
G2 cyclic  : min(|a-b|, 8-|a-b|)
G3 angular : 45 * G2   (documented; excluded from the joint, same partition as G2)
G4 Gray    : Hamming distance of GRAY_CODES
G6 Cayley  : O_h Cayley-graph distance via GeometricState.from_classical_state
joint      : (G1, G2, G4, G6)

Not run here (E07b, dynamic arm): Boltzmann-weighted L_R and temporal
trajectories. Both depend on the annealer scale fix documented in
experiments/README.md "Results".

Run:  python experiments/run_symmetry_identifiability.py [--n 4] [--out docs/]
"""

import argparse
import hashlib
import itertools
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)

from src import OhGroup, GeometricState, GRAY_CODES  # noqa: E402

N_STATES = 8


# ============================================================
# Geometries
# ============================================================

def state_metrics():
    idx = np.arange(N_STATES)
    g1 = np.abs(idx[:, None] - idx[None, :]).astype(float)
    g2 = np.minimum(g1, N_STATES - g1)
    g3 = 45.0 * g2
    bits = np.array([[int(c) for c in GRAY_CODES[s]] for s in range(N_STATES)])
    g4 = (bits[:, None, :] != bits[None, :, :]).sum(-1).astype(float)
    grp = OhGroup.instance()
    st = [GeometricState.from_classical_state(grp, s) for s in range(N_STATES)]
    g6 = np.array([[st[a].cayley_distance_to(st[b]) for b in range(N_STATES)]
                   for a in range(N_STATES)])
    return {"G1_numeric": g1, "G2_cyclic": g2, "G3_angular": g3,
            "G4_gray": g4, "G6_cayley": g6}


JOINT_MEMBERS = ("G1_numeric", "G2_cyclic", "G4_gray", "G6_cayley")


# ============================================================
# Symmetry groups
# ============================================================

_ALL_S8 = None


def all_s8():
    global _ALL_S8
    if _ALL_S8 is None:
        _ALL_S8 = np.array(list(itertools.permutations(range(N_STATES))), dtype=np.int64)
    return _ALL_S8


def isometry_group(d):
    """All label permutations g with d[g a, g b] == d[a, b]."""
    perms = all_s8()
    ok = np.ones(len(perms), dtype=bool)
    for a in range(N_STATES):
        for b in range(a + 1, N_STATES):
            ok &= np.isclose(d[perms[:, a], perms[:, b]], d[a, b])
    return perms[ok]


def component_group(n):
    return np.array(list(itertools.permutations(range(n))), dtype=np.int64)


# ============================================================
# Words, relational representation, classes
# ============================================================

def all_words(n):
    return np.array(list(itertools.product(range(N_STATES), repeat=n)), dtype=np.int64)


def encode(words):
    """Word array (..., n) -> base-8 integer (...)."""
    n = words.shape[-1]
    w = np.zeros(words.shape[:-1], dtype=np.int64)
    for k in range(n):
        w = w * N_STATES + words[..., k]
    return w


def relation_matrix(d, words):
    """M_R(x) as the upper-triangle vector, shape (|X|, n(n-1)/2)."""
    n = words.shape[1]
    cols = [d[words[:, i], words[:, j]] for i in range(n) for j in range(i + 1, n)]
    return np.stack(cols, axis=1)


def classes_from_keys(keys):
    """keys: list of hashable per word. Returns dict key -> list of word indices."""
    cl = defaultdict(list)
    for i, k in enumerate(keys):
        cl[k].append(i)
    return cl


def entropy_bits(sizes, total):
    p = np.asarray(sizes, dtype=float) / total
    return float(-(p * np.log2(p)).sum())


# ============================================================
# Orbits
# ============================================================

def images(words, iso, comp):
    """Return three int arrays of images per word:
       comp_img (|X|, n!), iso_img (|X|, |Iso|), comb_img (|X|, |Iso| * n!)."""
    comp_img = np.stack([encode(words[:, s]) for s in comp], axis=1)
    iso_img = np.stack([encode(g[words]) for g in iso], axis=1)
    comb = []
    for g in iso:
        for s in comp:
            comb.append(encode(g[words[:, s]]))
    comb_img = np.stack(comb, axis=1)
    return comp_img, iso_img, comb_img


def orbit_stats(img):
    """Orbit sizes and number of orbits from an image table."""
    sizes = np.array([len(np.unique(row)) for row in img])
    canon = img.min(axis=1)
    n_orbits = len(np.unique(canon))
    return sizes, n_orbits, canon


# ============================================================
# Pair classification (precedence chain + lattice)
# ============================================================

def classify_pairs(classes, comp_img, iso_img, comb_img):
    """
    For every unordered pair in every nontrivial class decide which
    declared symmetry relates them.

    lattice   : comp_only / iso_only / either / combined_only / genuine
    precedence: component -> isometry -> combined -> genuine (E06 convention)
    """
    lat = Counter()
    prec = Counter()
    genuine_pairs = []
    n_pairs = 0
    sorted_comp = np.sort(comp_img, axis=1)
    sorted_iso = np.sort(iso_img, axis=1)
    sorted_comb = np.sort(comb_img, axis=1)

    def member(sorted_row, y):
        k = np.searchsorted(sorted_row, y)
        return k < len(sorted_row) and sorted_row[k] == y

    for members in classes.values():
        if len(members) < 2:
            continue
        members = np.asarray(members)
        for a_pos, x in enumerate(members):
            ys = members[a_pos + 1:]
            for y in ys:
                n_pairs += 1
                in_comp = member(sorted_comp[x], y)
                in_iso = member(sorted_iso[x], y)
                in_comb = member(sorted_comb[x], y)
                if in_comp and in_iso:
                    lat["either"] += 1
                elif in_comp:
                    lat["comp_only"] += 1
                elif in_iso:
                    lat["iso_only"] += 1
                elif in_comb:
                    lat["combined_only"] += 1
                else:
                    lat["genuine"] += 1
                    genuine_pairs.append((int(x), int(y)))
                if in_comp:
                    prec["component_permutation"] += 1
                elif in_iso:
                    prec["state_label_isometry"] += 1
                elif in_comb:
                    prec["combined_symmetry"] += 1
                else:
                    prec["genuine_collision"] += 1
    return n_pairs, dict(lat), dict(prec), genuine_pairs


# ============================================================
# One geometry
# ============================================================

def analyse(name, d_list, words, comp, iso=None):
    """d_list: list of metrics (one for a single geometry, several for joint)."""
    t0 = time.time()
    if iso is None:
        iso = isometry_group(d_list[0])
        for d in d_list[1:]:
            iso_d = isometry_group(d)
            keep = np.array([any((g == h).all() for h in iso_d) for g in iso])
            iso = iso[keep]
    M = np.concatenate([relation_matrix(d, words) for d in d_list], axis=1)
    keys = [tuple(row) for row in M]
    classes = classes_from_keys(keys)
    sizes = np.array([len(v) for v in classes.values()])
    total = len(words)

    comp_img, iso_img, comb_img = images(words, iso, comp)
    iso_sizes, n_iso_orbits, _ = orbit_stats(iso_img)
    comb_sizes, n_comb_orbits, _ = orbit_stats(comb_img)
    iso_orbit_class_sizes = Counter(iso_img.min(axis=1).tolist())

    H_classes = entropy_bits(sizes, total)
    H_iso_orbits = entropy_bits(list(iso_orbit_class_sizes.values()), total)
    log_X = math.log2(total)

    n_pairs, lattice, precedence, genuine_pairs = classify_pairs(
        classes, comp_img, iso_img, comb_img)

    group_order = len(iso) * len(comp)
    stab_sizes = group_order // comb_sizes

    return {
        "name": name,
        "state_space_size": int(total),
        "word_length": int(words.shape[1]),
        "n_classes": int(len(classes)),
        "singleton_classes": int((sizes == 1).sum()),
        "nontrivial_classes": int((sizes > 1).sum()),
        "max_class_size": int(sizes.max()),
        "label_isometry_group_order": int(len(iso)),
        "component_group_order": int(len(comp)),
        "combined_group_order": int(group_order),
        "iso_orbits": int(n_iso_orbits),
        "combined_orbits": int(n_comb_orbits),
        "orbit_size_distribution_combined": {int(k): int(v) for k, v in
                                             sorted(Counter(comb_sizes.tolist()).items())},
        "stabilizer_size_distribution_combined": {int(k): int(v) for k, v in
                                                  sorted(Counter(stab_sizes.tolist()).items())},
        "colliding_pairs_total": int(n_pairs),
        "pairs_by_lattice": lattice,
        "pairs_by_precedence": precedence,
        "genuine_pairs": int(len(genuine_pairs)),
        "information_loss_bits": {
            "log2_X": log_X,
            "H_classes": H_classes,
            "H_iso_orbits": H_iso_orbits,
            "L_R": log_X - H_classes,
            "L_sym": log_X - H_iso_orbits,
            "L_excess": H_iso_orbits - H_classes,
        },
        "_classes": classes,
        "_genuine_pairs": genuine_pairs,
        "_iso": iso,
        "_M": M,
        "_comb_img": comb_img,
        "seconds": time.time() - t0,
    }


def public(res):
    return {k: v for k, v in res.items() if not k.startswith("_")}


# ============================================================
# Section H — cross-geometry recovery
# ============================================================

def cross_recovery(results, names):
    out = {}
    for i in names:
        gp = results[i]["_genuine_pairs"]
        row = {}
        for j in names:
            if i == j:
                continue
            Mj = results[j]["_M"]
            if not gp:
                row[j] = {"genuine_pairs_of_i": 0, "separated_by_j": 0, "verdict": "n/a"}
                continue
            sep = sum(1 for x, y in gp if not np.array_equal(Mj[x], Mj[y]))
            frac = sep / len(gp)
            verdict = ("redundant" if sep == 0 else
                       "fully_resolving" if sep == len(gp) else "partially_resolving")
            # does j introduce ambiguity that i resolves?
            Mi = results[i]["_M"]
            back = sum(1 for x, y in results[j]["_genuine_pairs"]
                       if not np.array_equal(Mi[x], Mi[y]))
            row[j] = {"genuine_pairs_of_i": len(gp), "separated_by_j": sep,
                      "fraction": frac, "verdict": verdict,
                      "j_genuine_pairs_resolved_by_i": back}
        out[i] = row
    # pairs colliding under every geometry = joint colliding pairs (consistency check)
    joint_cl = results["joint"]["_classes"]
    joint_pairs = set()
    for members in joint_cl.values():
        for a, b in itertools.combinations(sorted(members), 2):
            joint_pairs.add((a, b))
    per_geom_all = None
    for i in names:
        s_i = set()
        for members in results[i]["_classes"].values():
            if len(members) > 1:
                for a, b in itertools.combinations(sorted(members), 2):
                    s_i.add((a, b))
        per_geom_all = s_i if per_geom_all is None else per_geom_all & s_i
    out["_colliding_under_all"] = per_geom_all
    out["_joint_colliding"] = joint_pairs
    # how does each single geometry explain the joint-GENUINE pairs?
    decomp = Counter()
    for (a, b) in results["joint"]["_genuine_pairs"]:
        labels = []
        for i in names:
            r = results[i]
            row = np.sort(r["_comb_img"][a])
            k = np.searchsorted(row, b)
            in_comb = k < len(row) and row[k] == b
            labels.append("sym" if in_comb else "genuine")
        decomp[tuple(labels)] += 1
    out["_joint_genuine_by_single_geometry_explanation"] = {
        "+".join(f"{n_}={l}" for n_, l in zip(names, k)): v for k, v in decomp.items()}
    return out


# ============================================================
# Measurement collision — the SAT readout quotient (state >= 4 -> True)
# ============================================================

def measurement_readout(results, words):
    """Pairs merged by the readout Q(x) = (x_i >= 4) although the joint M separates them."""
    q = encode((words >= 4).astype(np.int64))  # 2^n readout classes
    Mj = results["joint"]["_M"]
    keys = np.array([hash(tuple(r)) for r in Mj])
    merged = 0
    merged_but_M_separates = 0
    for cls in np.unique(q):
        idx = np.where(q == cls)[0]
        k = len(idx)
        merged += k * (k - 1) // 2
        # pairs inside the readout class with equal joint M
        c = Counter(keys[idx].tolist())
        same_M = sum(v * (v - 1) // 2 for v in c.values())
        merged_but_M_separates += k * (k - 1) // 2 - same_M
    total_pairs = len(words) * (len(words) - 1) // 2
    return {"readout": "state >= 4 -> True (SAT decoding used in benchmark_sat.py)",
            "readout_classes": int(len(np.unique(q))),
            "pairs_merged_by_readout": int(merged),
            "of_which_joint_M_separates": int(merged_but_M_separates),
            "fraction_of_all_pairs_merged": merged / total_pairs,
            "joint_M_classes": int(results["joint"]["n_classes"])}


# ============================================================
# Section D — symmetry breaking
# ============================================================

def symmetry_breaking(metrics, names, words, comp, results):
    n = words.shape[1]
    configs = {
        "cyclic": (0, 2, 4, 6),
        "half_cycle": (0, 4, 0, 4),
        "repeated_state": (3, 3, 3, 3),
        "component_symmetric": (1, 2, 2, 1),
        "combined": (0, 4, 4, 0),
        "asymmetric_control": (0, 1, 3, 7),
    }
    code_to_idx = {int(c): i for i, c in enumerate(encode(words))}
    out = {}
    for cname, cfg in configs.items():
        cfg = tuple(cfg[:n]) + tuple([0] * max(0, n - len(cfg)))
        x = code_to_idx[int(encode(np.array(cfg)))]
        row = {"config": list(cfg)}
        for g in names:
            r = results[g]
            d = metrics[g] if g in metrics else None
            comb_img = r["_comb_img"]
            orbit = len(np.unique(comb_img[x]))
            stab = r["combined_group_order"] // orbit
            key = tuple(r["_M"][x])
            cls = len(r["_classes"][key])
            # minimal perturbation: change component 0 to nearest state under d
            if d is not None:
                dists = d[cfg[0]].copy()
                dists[cfg[0]] = np.inf
                s_new = int(np.argmin(dists))
                mag = float(d[cfg[0], s_new])
            else:  # joint: nearest under the sum of member metrics
                dsum = sum(metrics[m][cfg[0]] for m in JOINT_MEMBERS).astype(float)
                dsum[cfg[0]] = np.inf
                s_new = int(np.argmin(dsum))
                mag = float(dsum[s_new])
            cfg2 = (s_new,) + cfg[1:]
            x2 = code_to_idx[int(encode(np.array(cfg2)))]
            orbit2 = len(np.unique(comb_img[x2]))
            stab2 = r["combined_group_order"] // orbit2
            cls2 = len(r["_classes"][tuple(r["_M"][x2])])
            row[g] = {"stabilizer": int(stab), "orbit": int(orbit), "class_size": int(cls),
                      "perturbed_config": list(cfg2), "perturbation_magnitude": mag,
                      "stabilizer_after": int(stab2), "orbit_after": int(orbit2),
                      "class_size_after": int(cls2),
                      "ambiguity_reduced": bool(cls2 < cls)}
        out[cname] = row
    return out


# ============================================================
# Section E — more-data control (2x2)
# ============================================================

def more_data_control(results, metrics, words, seed=0):
    rng = np.random.RandomState(seed)
    total = len(words)
    Ns = [64, 256, 1024, 4096, 16384, 65536]
    out = {"same_geometry_more_samples": {}, "same_samples_plus_geometry": {}}
    for g in ("G1_numeric", "G4_gray"):
        M = results[g]["_M"]
        keys = np.array([hash(tuple(r)) for r in M])
        exhaustive = results[g]["n_classes"]
        rows = {}
        for N in Ns:
            idx = rng.randint(0, total, size=N)
            seen = np.unique(keys[idx])
            counts = Counter(keys[idx].tolist())
            H_plug = entropy_bits(list(counts.values()), N)
            rows[N] = {"classes_observed": int(len(seen)),
                       "classes_exhaustive": int(exhaustive),
                       "H_plugin": H_plug,
                       "H_exhaustive": results[g]["information_loss_bits"]["H_classes"]}
        out["same_geometry_more_samples"][g] = rows
    # fixed N, add a geometry
    N = 1024
    idx = rng.randint(0, total, size=N)
    base = results["G1_numeric"]["_M"][idx]
    for add in ("G2_cyclic", "G4_gray", "G6_cayley"):
        M2 = np.concatenate([base, results[add]["_M"][idx]], axis=1)
        k1 = len({tuple(r) for r in base})
        k2 = len({tuple(r) for r in M2})
        out["same_samples_plus_geometry"]["G1_numeric+" + add] = {
            "N": N, "classes_G1_only": k1, "classes_joint": k2, "gain": k2 - k1}
    return out


# ============================================================
# Section J — negative controls
# ============================================================

def negative_controls(results, metrics, words, comp):
    code_to_idx = {int(c): i for i, c in enumerate(encode(words))}
    n = words.shape[1]

    def idx_of(cfg):
        return code_to_idx[int(encode(np.array(cfg)))]

    def relation(g, x, y):
        r = results[g]
        same_class = np.array_equal(r["_M"][x], r["_M"][y])
        in_comp = int(encode(words[y])) in set(encode(words[x][comp]).tolist())
        in_iso = int(encode(words[y])) in set(encode(np.stack([gg[words[x]] for gg in r["_iso"]])).tolist())
        in_comb = int(encode(words[y])) in set(r["_comb_img"][x].tolist())
        return {"same_class": bool(same_class), "component_permutation": bool(in_comp),
                "label_isometry": bool(in_iso), "combined": bool(in_comb)}

    base = (0, 1, 3, 7)[:n]
    x = idx_of(base)
    out = {}

    # 1. global cyclic shift
    y = idx_of(tuple((s + 1) % 8 for s in base))
    out["1_global_cyclic_shift"] = {
        "expected": "label_isometry under G2 (shift is a rotation of the 8-cycle); "
                    "distinguished under G1 (|a-b| not shift-invariant across the wrap)",
        "G2_cyclic": relation("G2_cyclic", x, y),
        "G1_numeric": relation("G1_numeric", x, y),
        "pass": relation("G2_cyclic", x, y)["label_isometry"] and
                relation("G2_cyclic", x, y)["same_class"] and
                not relation("G1_numeric", x, y)["same_class"],
    }
    # 2. pure component permutation
    y = idx_of(tuple(reversed(base)))
    rel = {g: relation(g, x, y) for g in JOINT_MEMBERS}
    out["2_pure_component_permutation"] = {
        "expected": "detected as component_permutation under every geometry; same_class only "
                    "if the permutation is an automorphism of M_R(x)",
        "relations": rel,
        "pass": all(r["component_permutation"] for r in rel.values()),
    }
    # 3. pure label isometry (Gray: flip bit 0 of every state)
    flip = {s: [t for t in range(8) if GRAY_CODES[t] == (('1' if GRAY_CODES[s][0] == '0' else '0') + GRAY_CODES[s][1:])][0] for s in range(8)}
    y = idx_of(tuple(flip[s] for s in base))
    rel = relation("G4_gray", x, y)
    out["3_pure_label_isometry_G4"] = {
        "expected": "same_class and label_isometry under G4",
        "G4_gray": rel, "pass": rel["same_class"] and rel["label_isometry"],
    }
    # 4/5. E05 / E06 artifacts
    for k, what in (("4_E05_known_correspondence", "E05 generating correspondence"),
                    ("5_E06_known_genuine_collision", "E06 joint-geometry collision set")):
        out[k] = {"expected": f"reproduce the {what}",
                  "status": "blocked", "reason": "artifact not reachable from this repository "
                  "(not in SOMS, method-layer, or Simulators); regenerated set used instead",
                  "pass": None}
    # 6. asymmetric vector. Asymmetry is geometry-relative: (0,1,3,7) has Gray codes
    # 000,001,010,100, which the three coordinate swaps of the cube stabilize (stab 6).
    # Stronger: at n=4 NO word is asymmetric under G4, because the 48-element cube group
    # has no regular orbit on the 70 four-subsets of cube vertices (largest orbit is 24).
    # The control therefore reports the minimum stabilizer attained under each geometry.
    def stabs_of(xi):
        return {g: results[g]["combined_group_order"] // len(np.unique(results[g]["_comb_img"][xi]))
                for g in JOINT_MEMBERS + ("joint",)}
    stabs_base = stabs_of(x)
    min_stab = {}
    for g in JOINT_MEMBERS + ("joint",):
        r = results[g]
        orbit_sizes = np.array([len(np.unique(row)) for row in r["_comb_img"]])
        st = r["combined_group_order"] // orbit_sizes
        min_stab[g] = {"min_stabilizer": int(st.min()), "words_attaining": int((st == st.min()).sum())}
    out["6_asymmetric_vector"] = {
        "candidate_config": list(base), "candidate_stabilizers": stabs_base,
        "min_stabilizer_by_geometry": min_stab,
        "expected": "min stabilizer 1 under G1, G2, G6 and joint; min stabilizer 2 under G4 "
                    "(no regular orbit of the cube group on 4-subsets at n=4)",
        "pass": all(min_stab[g]["min_stabilizer"] == 1 for g in ("G1_numeric", "G2_cyclic", "G6_cayley", "joint"))
                and min_stab["G4_gray"]["min_stabilizer"] == 2,
    }
    # 7. duplicated observation
    rel = {g: relation(g, x, x) for g in JOINT_MEMBERS}
    out["7_identical_state_duplicated"] = {
        "expected": "same_class, distance 0",
        "relations": rel, "pass": all(r["same_class"] for r in rel.values()),
    }
    return out


# ============================================================
# Section F/G — BranchSet and discriminator economy
# ============================================================

def branch_set_and_discriminators(results, recovery, n):
    joint = results["joint"]
    joint_genuine = joint["genuine_pairs"]
    iso_orders = {g: results[g]["label_isometry_group_order"] for g in JOINT_MEMBERS}
    n_fact = math.factorial(n)
    n_pairs_rel = n * (n - 1) // 2

    # Observation: the joint-genuine collision pairs. Which generator explains them?
    prec = joint["pairs_by_precedence"]
    explained = {
        "symmetry_equivalence": prec.get("combined_symmetry", 0),
        "component_reindexing": prec.get("component_permutation", 0),
        "state_label_isometry": prec.get("state_label_isometry", 0),
        "representation_collision": joint_genuine,
    }

    def branch(bid, generator, origin, divergence, discriminator, cost,
               record_state, suppression="prior", access_kind=None):
        b = {
            "id": bid, "generator": generator, "origin_pattern": origin,
            "predicted_divergence": divergence, "discriminator": discriminator,
            "cost": float(cost), "status": "open", "eliminated_by": None,
            "suppression_cause": suppression, "access_kind": access_kind,
            "predicts_elsewhere": [{
                "pattern": divergence, "domain": "E07b_dynamic_arm",
                "already_in_record": "unknown", "record_state": record_state}],
            "instrument_history": [],
        }
        return b

    branches = [
        branch("symmetry_equivalence",
               "y = g(x o sigma) for some g in Iso(d_R), sigma in S_n",
               "E07a_joint_collision_set",
               "pair lies in one combined-group orbit",
               "enumerate Iso x S_n images of x", iso_orders["G4_gray"] * n_fact,
               "no_measurement_needed"),
        branch("component_reindexing", "y = x o sigma, sigma in S_n",
               "E07a_joint_collision_set", "pair lies in one S_n orbit",
               "enumerate S_n images of x", n_fact, "no_measurement_needed"),
        branch("state_label_isometry", "y = g(x), g in Iso(d_R)",
               "E07a_joint_collision_set", "pair lies in one Iso orbit",
               "enumerate Iso images of x", max(iso_orders.values()), "no_measurement_needed"),
        branch("correspondence_equivalence",
               "x and y correspond under the E05 generating correspondence",
               "E07a_joint_collision_set",
               "pair is related by the E05 correspondence matrix",
               "apply E05 correspondence P R P^T", 1.0,
               "missing_piece", suppression="access", access_kind="instrument_missing"),
        branch("representation_collision",
               "M_R(x) = M_R(y) with no declared symmetry relating x and y",
               "E07a_joint_collision_set",
               "another geometry separates the pair",
               "evaluate one more geometry on the pair", n_pairs_rel, "instrument_exists_unrun"),
        branch("measurement_collision",
               "readout Q(x) = Q(y) although M_R(x) != M_R(y) (e.g. state>=4 -> True)",
               "E07a_joint_collision_set",
               "pair separated by M_R but merged by the readout quotient",
               "compare readout images of x and y", n, "instrument_exists_unrun"),
    ]
    # Status from the static run
    for b in branches:
        k = b["id"]
        if k in explained:
            if explained[k] == 0:
                b["status"] = "eliminated"
                b["eliminated_by"] = "E07a exhaustive enumeration: explains 0 joint-genuine pairs"
            else:
                b["status"] = "survived"
        elif k == "measurement_collision":
            b["status"] = "survived"  # readout applied: see measurement_readout in results
    branch_set = {"schema_version": "1.0", "branches": branches}

    # Discriminator economy: which branch pairs does each discriminator separate?
    ids = [b["id"] for b in branches]
    separates = {
        "enumerate S_n":            {"component_reindexing"},
        "enumerate Iso":            {"state_label_isometry"},
        "enumerate Iso x S_n":      {"symmetry_equivalence", "component_reindexing", "state_label_isometry"},
        "add one geometry":         {"representation_collision"},
        "compare readout images":   {"measurement_collision"},
        "apply E05 correspondence": {"correspondence_equivalence"},
    }
    costs = {
        "enumerate S_n": n_fact,
        "enumerate Iso": max(iso_orders.values()),
        "enumerate Iso x S_n": iso_orders["G4_gray"] * n_fact,
        "add one geometry": n_pairs_rel,
        "compare readout images": n,
        "apply E05 correspondence": float("inf"),  # blocked
    }
    econ = {}
    for name, picks in separates.items():
        # a discriminator separates branch pair (a,b) if exactly one of them is in its picked set
        dp = sum(1 for a, b in itertools.combinations(ids, 2) if (a in picks) != (b in picks))
        c = costs[name]
        econ[name] = {"cost": c if math.isfinite(c) else None,
                      "delta_pairs": dp,
                      "delta_pairs_per_cost": (dp / c) if math.isfinite(c) and c > 0 else None,
                      "blocked": not math.isfinite(c)}
    feasible = [k for k in econ if not econ[k]["blocked"]]
    cheapest_first = sorted(feasible, key=lambda k: (econ[k]["cost"], k))
    by_ratio = sorted(feasible, key=lambda k: (-econ[k]["delta_pairs_per_cost"], k))
    return branch_set, {"discriminators": econ,
                        "order_cheapest_first": cheapest_first,
                        "order_delta_pairs_per_cost": by_ratio,
                        "orderings_agree": cheapest_first == by_ratio}


# ============================================================
# Driver
# ============================================================

def run(n=4, seed=0):
    metrics = state_metrics()
    words = all_words(n)
    comp = component_group(n)
    names = list(JOINT_MEMBERS)
    results = {}
    for g in names + ["G3_angular"]:
        results[g] = analyse(g, [metrics[g]], words, comp)
    results["joint"] = analyse("joint", [metrics[g] for g in names], words, comp)

    # G3 check: same partition and same isometry group as G2
    g3_same_partition = (results["G3_angular"]["n_classes"] == results["G2_cyclic"]["n_classes"]
                         and results["G3_angular"]["_classes"].keys().__len__() ==
                         results["G2_cyclic"]["n_classes"])
    g3_same_iso = results["G3_angular"]["label_isometry_group_order"] == \
        results["G2_cyclic"]["label_isometry_group_order"]
    m2 = results["G2_cyclic"]["_M"]
    m3 = results["G3_angular"]["_M"]
    g3_partition_identical = bool(np.array_equal(m3, 45.0 * m2))

    recovery = cross_recovery(results, names)
    # consistency: pairs colliding under every geometry == joint colliding pairs
    colliding_all = recovery["_colliding_under_all"]
    joint_colliding = recovery["_joint_colliding"]
    readout = measurement_readout(results, words)

    sym_break = symmetry_breaking(metrics, names + ["joint"], words, comp, results)
    more_data = more_data_control(results, metrics, words, seed=seed)
    controls = negative_controls(results, metrics, words, comp)
    branch_set, econ = branch_set_and_discriminators(results, recovery, n)

    # scaling table over word length (partition-level only, cheap)
    scaling = {}
    for nn in (2, 3, 4):
        if nn == n:
            scaling[nn] = {g: {"n_classes": results[g]["n_classes"],
                               "L_R": results[g]["information_loss_bits"]["L_R"]}
                           for g in names + ["joint"]}
            continue
        w = all_words(nn)
        row = {}
        for g in names:
            M = relation_matrix(metrics[g], w)
            k = len({tuple(r) for r in M})
            sizes = list(Counter(tuple(r) for r in M).values())
            row[g] = {"n_classes": k, "L_R": math.log2(len(w)) - entropy_bits(sizes, len(w))}
        Mj = np.concatenate([relation_matrix(metrics[g], w) for g in names], axis=1)
        sizes = list(Counter(tuple(r) for r in Mj).values())
        row["joint"] = {"n_classes": len(sizes), "L_R": math.log2(len(w)) - entropy_bits(sizes, len(w))}
        scaling[nn] = row

    out = {
        "experiment": "E07a symmetry / identifiability / information loss (static arm)",
        "word_length": n,
        "seed": seed,
        "geometries": {g: public(results[g]) for g in names + ["G3_angular", "joint"]},
        "G3_angular_check": {"partition_identical_to_G2": g3_partition_identical,
                             "isometry_group_identical_to_G2": g3_same_iso,
                             "excluded_from_joint": True},
        "cross_geometry_recovery": {k: v for k, v in recovery.items() if not k.startswith("_")},
        "colliding_under_all_geometries": len(colliding_all),
        "colliding_under_all_equals_joint_colliding": colliding_all == joint_colliding,
        "joint_genuine_by_single_geometry_explanation":
            recovery["_joint_genuine_by_single_geometry_explanation"],
        "G2_is_function_of_G1": bool(len({tuple(r) for r in np.concatenate(
            [results["G1_numeric"]["_M"], results["G2_cyclic"]["_M"]], axis=1)})
            == results["G1_numeric"]["n_classes"]),
        "measurement_readout": readout,
        "symmetry_breaking": sym_break,
        "more_data_control": more_data,
        "negative_controls": controls,
        "branch_set": branch_set,
        "discriminator_economy": econ,
        "scaling_with_word_length": scaling,
        "temporal_extension": {"status": "deferred_to_E07b",
                               "reason": "trajectory generator requires the annealer; "
                                         "annealer scale fix pending (experiments/README.md Results)"},
        "timings_seconds": {g: results[g]["seconds"] for g in names + ["G3_angular", "joint"]},
    }
    return out


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    if isinstance(o, tuple):
        return list(o)
    raise TypeError(type(o))


def content_hash(out):
    """sha256 of the results without wall-clock timings.

    Normalized through a JSON round-trip so that an in-memory result and the
    committed file hash identically (int dict keys become strings either way).
    """
    stable = json.loads(json.dumps(out, sort_keys=True, default=_json_default))
    stable.pop("timings_seconds", None)
    stable.pop("results_sha256_excluding_timings", None)
    for g in stable.get("geometries", {}).values():
        g.pop("seconds", None)
    s = json.dumps(stable, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()


# ============================================================
# Report
# ============================================================

def fmt(x, nd=3):
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def write_report(out, path, json_path, json_hash):
    G = out["geometries"]
    names = list(JOINT_MEMBERS) + ["G3_angular", "joint"]
    L = []
    w = L.append
    w("# Experiment 07a — Symmetry, Identifiability, and Information Loss (static arm)\n")
    w("Generated by `experiments/run_symmetry_identifiability.py`. Do not edit by hand.\n")
    w(f"Word length n = {out['word_length']}, |X| = 8^n = {G['G1_numeric']['state_space_size']}, "
      f"seed = {out['seed']}.\n")
    w("## 1. Definitions\n")
    w("```")
    w("X          = {0..7}^n                              word = one n-cell configuration")
    w("d_R        : 8x8 metric on states                  one per geometry")
    w("M_R(x)     = ( d_R(x_i, x_j) )_{i<j}               relational representation")
    w("x ~_R y    <=> M_R(x) = M_R(y)                     collision (exact equality)")
    w("Iso(d_R)   = { g in S_8 : d_R(ga, gb) = d_R(a,b) } label-isometry group")
    w("S_n        : component permutations                y = x o sigma")
    w("G_R        = Iso(d_R) x S_n                        combined group, y = g(x o sigma)")
    w("orbit(x)   = { g(x o sigma) }                      |Stab(x)| = |G_R| / |orbit(x)|")
    w("L_R        = log2|X| - H([X]_R)                    uniform measure on X")
    w("L_sym      = log2|X| - H(Iso-orbits)               loss the declared symmetry already removes")
    w("L_excess   = H(Iso-orbits) - H([X]_R)              representation loss beyond symmetry")
    w("joint      = (G1, G2, G4, G6); Iso(joint) = intersection of the four Iso groups")
    w("```\n")
    w("Pair classification is reported two ways. The **precedence chain** is the E06 convention "
      "(component → isometry → combined → genuine; first match wins). The **lattice** view reports "
      "which subgroups relate the pair independently, so a pair explained by both S_n and Iso is "
      "counted as `either`, not attributed to whichever was tested first.\n")

    w("## 2. Literature-derived hypotheses\n")
    w("```")
    w("H1 (Xu & Kanan 2026)  identifiability <= information not destroyed by G_X.")
    w("                      More samples of the same geometry cannot refine the partition;")
    w("                      one more geometry can.")
    w("H2                    every single-state map is a bijection on 8 states, so collisions")
    w("                      exist only at word level under a symmetry quotient.")
    w("H3                    G3 = 45*G2 induces the same partition and the same Iso group as G2;")
    w("                      it adds zero partition information to the joint.")
    w("H4                    L_R decomposes exactly into L_sym + L_excess; L_excess > 0 means the")
    w("                      representation loses information the declared symmetry does not explain.")
    w("H5                    cheapest-first and delta-pairs/cost need not order discriminators the")
    w("                      same way; a disagreement is a result, not an error.")
    w("```\n")

    w("## 3. Controls\n")
    w("Symmetry controls: exhaustive Iso(d_R) by enumeration of S_8; S_n by enumeration; combined "
      "group images tabulated per word. Negative controls in §11. G3 handled in §5.\n")

    w("## 4. Machine-readable results\n")
    w(f"`{os.path.relpath(json_path, ROOT)}`  sha256 (timings excluded) = `{json_hash}`\n")

    w("## 5. Symmetry-group results\n")
    w("| geometry | \\|Iso(d_R)\\| | \\|S_n\\| | \\|G_R\\| | Iso-orbits | G_R-orbits | orbit sizes (size:count) |")
    w("|---|---|---|---|---|---|---|")
    for g in names:
        r = G[g]
        os_ = ", ".join(f"{k}:{v}" for k, v in r["orbit_size_distribution_combined"].items())
        w(f"| {g} | {r['label_isometry_group_order']} | {r['component_group_order']} | "
          f"{r['combined_group_order']} | {r['iso_orbits']} | {r['combined_orbits']} | {os_} |")
    c = out["G3_angular_check"]
    w(f"\nG3 check: partition identical to G2 = **{c['partition_identical_to_G2']}**, "
      f"Iso identical to G2 = **{c['isometry_group_identical_to_G2']}**. "
      f"G3 is excluded from the joint (H3).\n")

    w("## 6. Equivalence-class results\n")
    w("| geometry | classes | singleton | nontrivial | max class | colliding pairs | comp-perm | label-iso | combined | genuine |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for g in names:
        r = G[g]
        p = r["pairs_by_precedence"]
        w(f"| {g} | {r['n_classes']} | {r['singleton_classes']} | {r['nontrivial_classes']} | "
          f"{r['max_class_size']} | {r['colliding_pairs_total']} | "
          f"{p.get('component_permutation', 0)} | {p.get('state_label_isometry', 0)} | "
          f"{p.get('combined_symmetry', 0)} | {p.get('genuine_collision', 0)} |")
    w("\nLattice view (pairs related by S_n only / Iso only / either / combined only / none):\n")
    w("| geometry | comp_only | iso_only | either | combined_only | genuine |")
    w("|---|---|---|---|---|---|")
    for g in names:
        l = G[g]["pairs_by_lattice"]
        w(f"| {g} | {l.get('comp_only', 0)} | {l.get('iso_only', 0)} | {l.get('either', 0)} | "
          f"{l.get('combined_only', 0)} | {l.get('genuine', 0)} |")

    w("\n## 7. Information-loss results (bits, uniform measure)\n")
    w("| geometry | log2\\|X\\| | H(classes) | H(Iso-orbits) | L_R | L_sym | L_excess |")
    w("|---|---|---|---|---|---|---|")
    for g in names:
        i = G[g]["information_loss_bits"]
        w(f"| {g} | {fmt(i['log2_X'])} | {fmt(i['H_classes'])} | {fmt(i['H_iso_orbits'])} | "
          f"{fmt(i['L_R'])} | {fmt(i['L_sym'])} | {fmt(i['L_excess'])} |")
    w("\nScaling with word length (classes, L_R):\n")
    w("| n | " + " | ".join(list(JOINT_MEMBERS) + ["joint"]) + " |")
    w("|---|" + "---|" * 5)
    for nn, row in out["scaling_with_word_length"].items():
        w(f"| {nn} | " + " | ".join(f"{row[g]['n_classes']} ({fmt(row[g]['L_R'], 2)})"
                                   for g in list(JOINT_MEMBERS) + ["joint"]) + " |")

    w("\n## 8. Symmetry-breaking results\n")
    w("Perturbation = replace component 0 by its nearest state under d_R; magnitude = that distance.\n")
    for cname, row in out["symmetry_breaking"].items():
        w(f"**{cname}** `{row['config']}`\n")
        w("| geometry | stab | orbit | class | → perturbed | mag | stab' | orbit' | class' | ambiguity reduced |")
        w("|---|---|---|---|---|---|---|---|---|---|")
        for g in list(JOINT_MEMBERS) + ["joint"]:
            r = row[g]
            w(f"| {g} | {r['stabilizer']} | {r['orbit']} | {r['class_size']} | {r['perturbed_config']} | "
              f"{fmt(r['perturbation_magnitude'], 1)} | {r['stabilizer_after']} | {r['orbit_after']} | "
              f"{r['class_size_after']} | {r['ambiguity_reduced']} |")
        w("")

    w("## 9. More-data control (2×2)\n")
    md = out["more_data_control"]
    w("Same geometry, more samples (classes observed → exhaustive limit):\n")
    w("| N | " + " | ".join(f"{g} observed / exhaustive" for g in md["same_geometry_more_samples"]) + " |")
    w("|---|" + "---|" * len(md["same_geometry_more_samples"]))
    Ns = list(next(iter(md["same_geometry_more_samples"].values())).keys())
    for N in Ns:
        w(f"| {N} | " + " | ".join(
            f"{md['same_geometry_more_samples'][g][N]['classes_observed']} / "
            f"{md['same_geometry_more_samples'][g][N]['classes_exhaustive']}"
            for g in md["same_geometry_more_samples"]) + " |")
    w("\nSame samples (N=1024), one more geometry:\n")
    w("| combination | classes G1 only | classes joint | gain |")
    w("|---|---|---|---|")
    for k, v in md["same_samples_plus_geometry"].items():
        w(f"| {k} | {v['classes_G1_only']} | {v['classes_joint']} | +{v['gain']} |")

    w("\n## 10. BranchSet candidates\n")
    w("Observation: the joint-genuine collision pairs. Schema 1.0, method-layer `branch_set.py`.\n")
    w("| id | status | cost | discriminator | suppression |")
    w("|---|---|---|---|---|")
    for b in out["branch_set"]["branches"]:
        w(f"| {b['id']} | {b['status']} | {b['cost']:.0f} | {b['discriminator']} | "
          f"{b['suppression_cause']}{'/' + b['access_kind'] if b['access_kind'] else ''} |")

    w("\n## 11. Discriminator results\n")
    e = out["discriminator_economy"]
    w("| discriminator | cost | Δpairs | Δpairs/cost | blocked |")
    w("|---|---|---|---|---|")
    for k, v in e["discriminators"].items():
        w(f"| {k} | {v['cost'] if v['cost'] is not None else '∞'} | {v['delta_pairs']} | "
          f"{fmt(v['delta_pairs_per_cost'], 4) if v['delta_pairs_per_cost'] is not None else '—'} | {v['blocked']} |")
    w(f"\ncheapest-first:      {e['order_cheapest_first']}")
    w(f"\nΔpairs/cost:         {e['order_delta_pairs_per_cost']}")
    w(f"\norderings agree:     **{e['orderings_agree']}**\n")
    w("Note: five of the six discriminators each isolate exactly one branch, so Δpairs = 5 for all of them "
      "and the ratio ordering reduces to the cost ordering. Only `enumerate Iso x S_n` (Δpairs = 9) can move; "
      "it is last under both. H5 is therefore untested here, not confirmed: the separation structure is "
      "degenerate. A non-degenerate test needs discriminators that split different numbers of branches.\n")

    w("## 12. Cross-geometry recovery\n")
    w("For the genuine pairs of geometry i (rows), how many does geometry j (columns) separate?\n")
    cr = out["cross_geometry_recovery"]
    w("| i \\ j | " + " | ".join(JOINT_MEMBERS) + " |")
    w("|---|" + "---|" * 4)
    for i in JOINT_MEMBERS:
        cells = []
        for j in JOINT_MEMBERS:
            if i == j:
                cells.append("—")
            else:
                c = cr[i][j]
                cells.append(f"{c['separated_by_j']}/{c['genuine_pairs_of_i']} {c['verdict']}")
        w(f"| {i} | " + " | ".join(cells) + " |")
    w(f"\nPairs colliding under every geometry: **{out['colliding_under_all_geometries']}** "
      f"(equals joint colliding pairs: {out['colliding_under_all_equals_joint_colliding']}). "
      f"G2 is a function of G1 (min(|a-b|, 8-|a-b|)), so joint(G1,G2) = G1: "
      f"**{out['G2_is_function_of_G1']}**.\n")
    w("How each single geometry explains the joint-genuine pairs (sym = inside that geometry's "
      "own Iso×S_n orbit; genuine = not):\n")
    w("| explanation pattern | pairs |")
    w("|---|---|")
    for k, v in sorted(out["joint_genuine_by_single_geometry_explanation"].items(), key=lambda kv: -kv[1]):
        w(f"| {k} | {v} |")
    mr = out["measurement_readout"]
    w(f"\n**Measurement collision (readout quotient).** Readout `{mr['readout']}` has "
      f"{mr['readout_classes']} classes against {mr['joint_M_classes']} joint-M classes. It merges "
      f"{mr['pairs_merged_by_readout']} pairs ({mr['fraction_of_all_pairs_merged']:.1%} of all pairs); "
      f"the joint relational representation separates {mr['of_which_joint_M_separates']} of them. "
      f"This is the quotient that made the octahedral geometry neutral on MAX-SAT "
      f"(experiments/README.md, Results).\n")

    w("## 13. Temporal results\n")
    t = out["temporal_extension"]
    w(f"Status: **{t['status']}**. {t['reason']}\n")

    w("## 14. Negative controls and deviations from predictions\n")
    w("| control | expected | pass |")
    w("|---|---|---|")
    for k, v in out["negative_controls"].items():
        p = v.get("pass")
        w(f"| {k} | {v['expected']} | {'blocked' if p is None else p} |")
    w("\nDeviations are listed in §15 of the JSON-derived summary below.\n")

    w("## 15. Observation / structural result / interpretation\n")
    jg = G["joint"]
    w("**Observation.** " + "; ".join(
        f"{g}: {G[g]['n_classes']} classes, {G[g]['pairs_by_precedence'].get('genuine_collision', 0)} genuine pairs, "
        f"L_excess {fmt(G[g]['information_loss_bits']['L_excess'])} bits"
        for g in list(JOINT_MEMBERS) + ['joint']) + ".\n")
    w("**Structural result.** L_R = L_sym + L_excess holds exactly for every geometry (identity of the "
      "decomposition). Genuine pairs are those not in any combined-group orbit; they are a lower bound "
      "on explainable pairs relative to the declared groups and an upper bound on representation loss. "
      "The joint partition is the meet of the four partitions; the joint Iso group is the intersection.\n")
    w("**Interpretation (not claimed).** Nothing here bears on consciousness, awareness, sovereignty, "
      "selfhood, agency, semantic identity or Φ. The result concerns which configurations a relational "
      "encoding can and cannot tell apart, and which declared symmetry accounts for each merge.\n")

    w("## 16. Limitations\n")
    w("- Static arm only: uniform measure on X. The Boltzmann-weighted L_R and temporal §I are E07b.")
    w("- Genuine collisions are relative to the declared groups Iso(d_R) and S_n; a larger declared group can only shrink them.")
    w("- E05 correspondence and the E06 collision set were not reachable; the collision set was regenerated exhaustively here.")
    w("- Costs in §11 are enumeration counts, not wall-clock; blocked discriminators carry infinite cost.")
    w("- The Cayley metric G6 is irregular on the 8 chosen elements (distances 0..5, not vertex-transitive); its Iso group is therefore small and its collision structure is not comparable to G2's by inspection.\n")

    w("## 17. Reproducibility\n")
    w("```bash")
    w("pip install numpy scipy")
    w(f"python experiments/run_symmetry_identifiability.py --n {out['word_length']} --seed {out['seed']}")
    w("python -m pytest tests/test_experiment_07_symmetry_identifiability.py -q")
    w("```")
    w(f"\nResults hash (sha256, timings excluded): `{json_hash}`\n")
    with open(path, "w") as f:
        f.write("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(ROOT, "docs"))
    a = ap.parse_args()
    t0 = time.time()
    out = run(n=a.n, seed=a.seed)
    h = content_hash(out)
    out["results_sha256_excluding_timings"] = h
    os.makedirs(a.out, exist_ok=True)
    jp = os.path.join(a.out, "experiment_07_symmetry_identifiability_results.json")
    rp = os.path.join(a.out, "experiment_07_symmetry_identifiability_report.md")
    with open(jp, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=_json_default)
    write_report(out, rp, jp, h)
    G = out["geometries"]
    print(f"E07a done in {time.time() - t0:.1f}s  hash={h[:16]}")
    for g in list(JOINT_MEMBERS) + ["G3_angular", "joint"]:
        r = G[g]
        print(f"  {g:12s} |Iso|={r['label_isometry_group_order']:3d} classes={r['n_classes']:5d} "
              f"pairs={r['colliding_pairs_total']:7d} genuine={r['genuine_pairs']:6d} "
              f"L_R={r['information_loss_bits']['L_R']:.3f} L_excess={r['information_loss_bits']['L_excess']:.3f}")
    print(f"  discriminator orderings agree: {out['discriminator_economy']['orderings_agree']}")
    print(f"  negative controls: " + ", ".join(f"{k.split('_')[0]}={v.get('pass')}" for k, v in out['negative_controls'].items()))


if __name__ == "__main__":
    main()
