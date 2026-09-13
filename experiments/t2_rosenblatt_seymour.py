"""
T2 — Rosenblatt–Seymour check on ring-type homometric collisions
=================================================================
Universe: 4-subsets of the 8 states (70 of them), distinct elements, no
order. Readout: the multiset of the 6 pairwise distances (Patterson /
interval-vector readout). Two geometries:

  ring  Z8 cyclic distance, isometry group D8 (order 16)
  cube  Gray-code Hamming distance, isometry group B3 (order 48)

Homometric pair: same distance multiset. Non-isometric homometric pair:
same multiset, not related by the geometry's isometry group.

Rosenblatt & Seymour (1982): in a cyclic group, if A = B + C and A' = B - C
(sumset / difference set, as sets or multisets) then A and A' are
homometric. Question: do the non-isometric ring pairs FACTOR this way?
If every one does, the collision is a mechanism (a factorization), not a
coincidence. Factorization is searched over all 2-subsets B, C of Z8 and
tested up to the D8 action on A' (translation and reflection), in both
role assignments.

Also computed: |D8 ∩ B3| as permutation groups on the 8 labels, the pairs
isometric under both, and the relation of the 548 E07a joint-genuine word
pairs to this universe (they are ordered words with repeats; this is sets).

Run: python experiments/t2_rosenblatt_seymour.py  (from repo root)
"""
import itertools
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import run_symmetry_identifiability as e07  # noqa: E402

N = 8


def multiset_key(d, S):
    return tuple(sorted(d[a, b] for a, b in itertools.combinations(S, 2)))


def group_on_subsets(iso):
    """Map each 4-subset to its canonical orbit representative under iso (rows of S_8)."""
    canon = {}
    for S in itertools.combinations(range(N), 4):
        imgs = [tuple(sorted(g[list(S)].tolist())) for g in iso]
        canon[S] = min(imgs)
    return canon


def homometry_table(d, iso, label):
    subsets = list(itertools.combinations(range(N), 4))
    keys = {S: multiset_key(d, S) for S in subsets}
    canon = group_on_subsets(iso)
    by_key = defaultdict(list)
    for S in subsets:
        by_key[keys[S]].append(S)
    same = 0
    via_iso = 0
    non_iso_pairs = []
    for members in by_key.values():
        for A, B in itertools.combinations(members, 2):
            same += 1
            if canon[A] == canon[B]:
                via_iso += 1
            else:
                non_iso_pairs.append((A, B))
    return {"label": label, "group_order": int(len(iso)), "subsets": len(subsets),
            "distinct_multisets": len(by_key),
            "pairs_same_multiset": same, "pairs_via_isometry": via_iso,
            "pairs_non_isometric": len(non_iso_pairs),
            "multiset_complete": len(non_iso_pairs) == 0}, non_iso_pairs, canon


def rs_factor(A, Ap, canon_ring):
    """Search B, C 2-subsets of Z8 with B+C == A and B-C ~ Ap (up to D8), either role order."""
    A = frozenset(A)
    hits = []
    twos = list(itertools.combinations(range(N), 2))
    for B in twos:
        for C in twos:
            sums = {(b + c) % N for b in B for c in C}
            diffs = {(b - c) % N for b in B for c in C}
            if len(sums) != 4 or len(diffs) != 4:
                continue
            for X, Y, role in ((sums, diffs, "A=B+C, A'=B-C"), (diffs, sums, "A=B-C, A'=B+C")):
                if frozenset(X) == A and canon_ring[tuple(sorted(Y))] == canon_ring[tuple(sorted(Ap))]:
                    hits.append({"B": list(B), "C": list(C), "role": role})
    return hits


def spectral_rs_search(non_iso_pairs, canon_ring, bound=3, n=N, k=4, allow_isometric=False):
    """
    Rosenblatt-Seymour form over Z[x]/(x^8 - 1):  S = P*Q,  T = P*Q(x^-1).
    In Fourier space: S^(k) = P^(k) Q^(k), T^(k) = P^(k) conj(Q^(k)).
    Search Q exhaustively with coefficients in [-bound, bound]; derive P^ = S^/Q^ and
    accept if P is an integer polynomial and P*Q(x^-1) lands in T's D8 orbit.
    S is fixed to one representative per class (translation/reflection of S are absorbed
    into P and a global reflection); T is compared up to D8.
    """
    # collapse the pairs to orbit classes
    classes = {}
    for A, Ap in non_iso_pairs:
        key = tuple(sorted((canon_ring[tuple(A)], canon_ring[tuple(Ap)])))
        classes.setdefault(key, (A, Ap))
    free_report = {}
    vals = list(range(-bound, bound + 1))
    Qs = np.array(list(itertools.product(vals, repeat=n)), dtype=np.int64)
    Qs = Qs[np.any(Qs != 0, axis=1)]
    FQ = np.fft.fft(Qs, axis=1)
    subset_canon = {S: canon_ring[S] for S in itertools.combinations(range(n), k)}
    found = {}
    for key, (A, Ap) in classes.items():
        Svec = np.zeros(n); Svec[list(A)] = 1
        FS = np.fft.fft(Svec)
        target_canon = canon_ring[tuple(Ap)]
        hit = None
        nz = np.abs(FS) > 1e-9
        zero_freqs = [int(j) for j in np.nonzero(~nz)[0]]
        # Where S^ = 0 and Q^ = 0 too, P^ is free. For the real frequency n/2 the fix is exact:
        # P = P0 + t * (-1)^j, and t is determined mod 1 by integrality of P0[0] + t. Complex free
        # frequencies are not handled and are reported as a gap.
        half = n // 2 if n % 2 == 0 else None
        complex_free = [j for j in zero_freqs if j not in (0, half)]
        free_report[key] = {"S_hat_zero_frequencies": zero_freqs,
                            "real_free_frequency_handled": half in zero_freqs,
                            "complex_free_frequencies_unhandled": complex_free}
        for i0 in range(0, len(Qs), 200000):
            fq = FQ[i0:i0 + 200000]
            ok = np.all(np.abs(fq[:, nz]) > 1e-9, axis=1)          # Q^ must not vanish where S^ != 0
            cand = np.nonzero(ok)[0]
            if len(cand) == 0:
                continue
            fq = fq[cand]
            FP = np.zeros_like(fq)
            FP[:, nz] = FS[nz] / fq[:, nz]                           # where S^ = 0 leave P^ = 0
            P = np.fft.ifft(FP, axis=1).real
            if half is not None and not nz[half]:
                # rows where Q^(n/2) = 0 as well: shift P along (-1)^j so that P[0] becomes integer
                qz = np.abs(fq[:, half]) < 1e-9
                if qz.any():
                    t = np.rint(P[qz, 0]) - P[qz, 0]
                    P[qz] = P[qz] + t[:, None] * ((-1) ** np.arange(n))[None, :]
            is_int = np.all(np.abs(P - np.rint(P)) < 1e-6, axis=1)
            for j in np.nonzero(is_int)[0]:
                Pi = np.rint(P[j]).astype(np.int64)
                FT = np.fft.fft(Pi) * np.conj(fq[j])
                T = np.rint(np.fft.ifft(FT).real).astype(np.int64)
                if T.min() < 0 or T.max() > 1 or T.sum() != k:
                    continue
                Tset = tuple(np.nonzero(T)[0].tolist())
                if subset_canon[Tset] == target_canon and (allow_isometric or subset_canon[Tset] != canon_ring[tuple(A)]):
                    hit = {"P": Pi.tolist(), "Q": Qs[cand[j] + i0].tolist(), "S": list(A), "T": list(Tset)}
                    break
            if hit:
                break
        found[key] = hit
    return {"coefficient_bound": bound, "Q_polynomials_searched": int(len(Qs)),
            "classes": [{"canonical_A": list(k[0]), "canonical_A_prime": list(k[1]),
                         "representative_pair": [list(v[0]), list(v[1])]} for k, v in classes.items()],
            "pairs_factoring": sum(1 for v in found.values() if v is not None),
            "pairs_total": len(found),
            "free_frequency_report": {str(list(map(list, k_))): v for k_, v in free_report.items()},
            "examples": [v for v in found.values() if v is not None],
            "unfactored": [list(k) for k, v in found.items() if v is None]}


def dihedral_canon(n, k):
    """Canonical orbit representative of every k-subset of Z_n under the dihedral group D_n."""
    canon = {}
    for S in itertools.combinations(range(n), k):
        imgs = []
        for t in range(n):
            imgs.append(tuple(sorted((x + t) % n for x in S)))
            imgs.append(tuple(sorted((-x + t) % n for x in S)))
        canon[S] = min(imgs)
    return canon


def z12_forte_control(bound=1):
    """Positive control: the first Z12 Z-relation pair {0,1,4,6}/{0,1,3,7} (Forte 4-Z15 / 4-Z29)."""
    n = 12
    canon = dihedral_canon(n, 4)
    A, Ap = (0, 1, 4, 6), (0, 1, 3, 7)
    d = np.minimum(np.abs(np.arange(n)[:, None] - np.arange(n)[None, :]),
                   n - np.abs(np.arange(n)[:, None] - np.arange(n)[None, :]))
    homometric = multiset_key(d, A) == multiset_key(d, Ap)
    non_iso = canon[A] != canon[Ap]
    res = spectral_rs_search([(A, Ap)], canon, bound=bound, n=n, k=4)
    return {"pair": [list(A), list(Ap)], "homometric_in_Z12": bool(homometric),
            "non_isometric_in_Z12": bool(non_iso), "search": res}


def mechanics_control(n=8, k=4, bound=1, seed=11, draws=200000):
    """Construct S = PQ, T = PQ(x^-1) from random P, Q with coefficients in [-bound, bound]
    (T may be isometric to S) and check the spectral search recovers a factorization."""
    rng = np.random.RandomState(seed)
    canon = dihedral_canon(n, k)
    P = rng.randint(-bound, bound + 1, size=(draws, n)); Q = rng.randint(-bound, bound + 1, size=(draws, n))
    FP, FQ = np.fft.fft(P, axis=1), np.fft.fft(Q, axis=1)
    S = np.rint(np.fft.ifft(FP * FQ, axis=1).real).astype(np.int64)
    T = np.rint(np.fft.ifft(FP * np.conj(FQ), axis=1).real).astype(np.int64)
    ok = (S.min(1) >= 0) & (S.max(1) <= 1) & (S.sum(1) == k) & (T.min(1) >= 0) & (T.max(1) <= 1) & (T.sum(1) == k)
    # prefer a pair whose P or Q is not a unit and whose S != T
    picks = []
    for i in np.nonzero(ok)[0]:
        a = tuple(np.nonzero(S[i])[0].tolist()); b = tuple(np.nonzero(T[i])[0].tolist())
        if a != b and np.count_nonzero(P[i]) > 1 and np.count_nonzero(Q[i]) > 1:
            picks.append((a, b, P[i].tolist(), Q[i].tolist()))
        if len(picks) >= 3:
            break
    results = []
    for a, b, Pi, Qi in picks:
        res = spectral_rs_search([(a, b)], canon, bound=bound, n=n, k=k, allow_isometric=True)
        results.append({"S": list(a), "T": list(b), "constructed_P": Pi, "constructed_Q": Qi,
                        "isometric": canon[a] == canon[b], "search_recovers": res["pairs_factoring"] == 1,
                        "recovered": res["examples"][:1]})
    return {"n": n, "k": k, "bound": bound, "candidates_found": int(ok.sum()), "checked": results,
            "all_recovered": all(r["search_recovers"] for r in results) if results else None}


def rs_reachable_z8(bound=1):
    """Which non-isometric homometric 4-subset classes of Z8 are of the form (PQ, PQ(x^-1)) at all,
    P and Q both with coefficients in [-bound, bound]? Exhaustive over P x Q via FFT."""
    vals = list(range(-bound, bound + 1))
    polys = np.array(list(itertools.product(vals, repeat=N)), dtype=np.int64)
    polys = polys[np.any(polys != 0, axis=1)]
    F = np.fft.fft(polys, axis=1)
    canon = dihedral_canon(N, 4)
    reached = {}
    chunk = 128
    for i in range(0, len(polys), chunk):
        FP = F[i:i + chunk]
        S = np.rint(np.fft.ifft(FP[:, None, :] * F[None, :, :], axis=2).real).astype(np.int64)
        T = np.rint(np.fft.ifft(FP[:, None, :] * np.conj(F)[None, :, :], axis=2).real).astype(np.int64)
        ok = (S.min(2) >= 0) & (S.max(2) <= 1) & (S.sum(2) == 4) & (T.min(2) >= 0) & (T.max(2) <= 1) & (T.sum(2) == 4)
        for ci, qi in zip(*np.nonzero(ok)):
            a = tuple(np.nonzero(S[ci, qi])[0].tolist()); b = tuple(np.nonzero(T[ci, qi])[0].tolist())
            ca, cb = canon[a], canon[b]
            if ca != cb:
                reached.setdefault(tuple(sorted((ca, cb))), {"P": polys[i + ci].tolist(), "Q": polys[qi].tolist()})
    return {"coefficient_bound": bound, "polynomials": int(len(polys)),
            "non_isometric_classes_reachable": [{"A": list(k[0]), "A_prime": list(k[1]), **v} for k, v in reached.items()]}


def overlay_check(m):
    """|D8 ∩ B3| and both-isometric pair counts under the Gray labeling (E07) and plain binary."""
    ring = m["G2_cyclic"]
    iso_ring = e07.isometry_group(ring)
    out = {}
    for label, codes in (("gray", {s: e07.GRAY_CODES[s] for s in range(N)}),
                         ("binary", {s: format(s, "03b") for s in range(N)})):
        bits = np.array([[int(c) for c in codes[s]] for s in range(N)])
        cube = (bits[:, None, :] != bits[None, :, :]).sum(-1).astype(float)
        iso_cube = e07.isometry_group(cube)
        cube_set = {tuple(g.tolist()) for g in iso_cube}
        inter = [g for g in iso_ring if tuple(g.tolist()) in cube_set]
        canon_r = group_on_subsets(iso_ring)
        canon_c = group_on_subsets(iso_cube)
        canon_i = group_on_subsets(np.array(inter))
        subsets = list(itertools.combinations(range(N), 4))
        common_orbits = sum(1 for A, B in itertools.combinations(subsets, 2)
                            if canon_r[A] == canon_r[B] and canon_c[A] == canon_c[B])
        by_intersection = sum(1 for A, B in itertools.combinations(subsets, 2) if canon_i[A] == canon_i[B])
        out[label] = {"D8_cap_B3_order": len(inter),
                      "pairs_in_common_D8_orbit_and_common_B3_orbit": common_orbits,
                      "pairs_related_by_an_element_of_D8_cap_B3": by_intersection}
    return out


def run():
    m = e07.state_metrics()
    ring, cube = m["G2_cyclic"], m["G4_gray"]
    iso_ring = e07.isometry_group(ring)
    iso_cube = e07.isometry_group(cube)
    ring_tab, ring_non, canon_ring = homometry_table(ring, iso_ring, "ring/D8")
    cube_tab, cube_non, canon_cube = homometry_table(cube, iso_cube, "cube/B3")

    # intersection of the two groups as permutations of the 8 labels
    cube_set = {tuple(g.tolist()) for g in iso_cube}
    both = [g for g in iso_ring if tuple(g.tolist()) in cube_set]
    # pairs isometric under both groups (any two subsets in a common orbit of both)
    subsets = list(itertools.combinations(range(N), 4))
    iso_both_pairs = sum(1 for A, B in itertools.combinations(subsets, 2)
                         if canon_ring[A] == canon_ring[B] and canon_cube[A] == canon_cube[B])

    # RS factorization of every non-isometric ring pair
    rs = []
    n_factor = 0
    for A, Ap in ring_non:
        hits = rs_factor(A, Ap, canon_ring)
        if hits:
            n_factor += 1
        rs.append({"A": list(A), "A_prime": list(Ap), "factors": len(hits),
                   "example": hits[0] if hits else None})
    signed = spectral_rs_search(ring_non, canon_ring, bound=3)
    forte12 = z12_forte_control(bound=1)
    reach8 = rs_reachable_z8(bound=1)
    mech = mechanics_control()
    overlay = overlay_check(m)
    forte = [r for r in rs if set(r["A"]) | set(r["A_prime"]) == {0, 1, 3, 4, 6, 7} and
             ({0, 1, 4, 6} in (set(r["A"]), set(r["A_prime"])) or {0, 1, 3, 7} in (set(r["A"]), set(r["A_prime"])))]

    # relation of the E07a 548 to this universe
    words = e07.all_words(4)
    comp = e07.component_group(4)
    res = e07.analyse("joint", [m[g] for g in e07.JOINT_MEMBERS], words, comp)
    gp = res["_genuine_pairs"]
    distinct = 0
    ring_iso_sets = 0
    cube_iso_sets = 0
    ring_homometric_nonisometric = 0
    same_set = 0
    for a, b in gp:
        x, y = words[a], words[b]
        if len(set(x.tolist())) == 4 and len(set(y.tolist())) == 4:
            distinct += 1
            Sx, Sy = tuple(sorted(x.tolist())), tuple(sorted(y.tolist()))
            if Sx == Sy:
                same_set += 1
            if canon_ring[Sx] == canon_ring[Sy]:
                ring_iso_sets += 1
            if canon_cube[Sx] == canon_cube[Sy]:
                cube_iso_sets += 1
            if multiset_key(ring, Sx) == multiset_key(ring, Sy) and canon_ring[Sx] != canon_ring[Sy]:
                ring_homometric_nonisometric += 1
    repeats_hist = Counter()
    for a, b in gp:
        repeats_hist[len(set(words[a].tolist()))] += 1

    c0137 = canon_ring[(0, 1, 3, 7)]
    in_class = [c0137 in (cl["canonical_A"] and tuple(cl["canonical_A"]), tuple(cl["canonical_A_prime"]))
                for cl in signed["classes"]]
    out = {
        "universe": "4-subsets of 8 states, multiset-of-distances readout",
        "orbit_of_0137_is_in_a_nonisometric_homometric_class": bool(any(in_class)),
        "canonical_0137": list(c0137),
        "ring": ring_tab, "cube": cube_tab,
        "D8_cap_B3_order": len(both),
        "pairs_isometric_under_both": iso_both_pairs,
        "overlay_check": overlay,
        "rosenblatt_seymour": {
            "non_isometric_ring_pairs": len(ring_non),
            "set_factorizations_B_plus_C": n_factor,
            "set_fraction": (n_factor / len(ring_non)) if ring_non else None,
            "spectral_search": signed,
            "positive_control_Z12_forte": forte12,
            "rs_reachable_classes_Z8": reach8,
            "mechanics_control": mech,
            "set_level_lemma": "With |B| = |C| = 2 and 0 in C = {0, c} (translate), B - C = B ∪ (B - c) = (B + C) - c, so T is always a translate of S. No 4-element homometric pair in any cyclic group is a set-level Rosenblatt–Seymour pair; the 0/64 above is forced, not found.",
            "pairs": rs,
            "forte_Z_relation_0146_0137": forte,
        },
        "E07a_548_vs_this_universe": {
            "joint_genuine_word_pairs": len(gp),
            "by_number_of_distinct_states_in_word": dict(sorted(repeats_hist.items())),
            "both_words_have_4_distinct_states": distinct,
            "of_those_same_underlying_set": same_set,
            "of_those_sets_D8_related": ring_iso_sets,
            "of_those_sets_B3_related": cube_iso_sets,
            "of_those_ring_homometric_non_isometric": ring_homometric_nonisometric,
        },
    }
    return out


def write_md(out, path):
    L = []
    w = L.append
    w("# T2 — Rosenblatt–Seymour check on ring-type homometric collisions\n")
    w("Generated by `experiments/t2_rosenblatt_seymour.py`. Universe: 4-subsets of 8 states, "
      "distance-multiset readout.\n")
    w("| geometry | \\|G\\| | distinct multisets | same multiset | via isometry | non-isometric |")
    w("|---|---|---|---|---|---|")
    for k in ("ring", "cube"):
        t = out[k]
        w(f"| {t['label']} | {t['group_order']} | {t['distinct_multisets']} | {t['pairs_same_multiset']} | "
          f"{t['pairs_via_isometry']} | {t['pairs_non_isometric']} |")
    w(f"\n|D8 ∩ B3| on the 8 labels = **{out['D8_cap_B3_order']}**; pairs isometric under both groups = "
      f"**{out['pairs_isometric_under_both']}**.\n")
    ov = out["overlay_check"]
    w("Overlay of the ring on the cube depends on the labeling:\n")
    w("| labeling | \\|D8 ∩ B3\\| | pairs in a common D8 orbit AND a common B3 orbit | pairs related by an element of D8 ∩ B3 |")
    w("|---|---|---|---|")
    for k, v in ov.items():
        w(f"| {k} | {v['D8_cap_B3_order']} | {v['pairs_in_common_D8_orbit_and_common_B3_orbit']} | "
          f"{v['pairs_related_by_an_element_of_D8_cap_B3']} |")
    rs = out["rosenblatt_seymour"]
    w("\n## Rosenblatt–Seymour factorization\n")
    w(f"Non-isometric ring pairs: {rs['non_isometric_ring_pairs']}.\n")
    w(f"- As **sets**, A = B + C and A' = B − C with B, C 2-subsets of Z8, A' up to D8: "
      f"**{rs['set_factorizations_B_plus_C']}** of {rs['non_isometric_ring_pairs']} factor.")
    sp = rs["spectral_search"]
    w(f"- The {rs['non_isometric_ring_pairs']} pairs collapse to **{sp['pairs_total']}** D8-orbit class(es): " +
      "; ".join(f"{c['canonical_A']} / {c['canonical_A_prime']}" for c in sp["classes"]) + ".")
    w(f"- Over **Z[x]/(x⁸−1)**, Q exhaustive with coefficients in [−{sp['coefficient_bound']}, {sp['coefficient_bound']}] "
      f"({sp['Q_polynomials_searched']} polynomials), P derived spectrally as Ŝ/Q̂ and required integer, "
      f"T = PQ(x⁻¹) compared up to D8: **{sp['pairs_factoring']}** of {sp['pairs_total']} class(es) factor.")
    w(f"- The orbit of (0,1,3,7) (canonical {out['canonical_0137']}) lies in that class: "
      f"**{out['orbit_of_0137_is_in_a_nonisometric_homometric_class']}**.\n")
    if sp["examples"]:
        w("| S | T | P | Q |")
        w("|---|---|---|---|")
        for e in sp["examples"]:
            w(f"| {e['S']} | {e['T']} | {e['P']} | {e['Q']} |")
    if sp["unfactored"]:
        w(f"\nNot factored within the bound: " + "; ".join(f"{a}/{b}" for a, b in sp["unfactored"]))
    w(f"\n**Lemma (set level).** {rs['set_level_lemma']}\n")
    mc = rs["mechanics_control"]
    w(f"**Mechanics control.** Random P, Q with coefficients in [−{mc['bound']}, {mc['bound']}] in Z{mc['n']} produced "
      f"{mc['candidates_found']} (PQ, PQ(x⁻¹)) pairs of {mc['k']}-sets; the search recovers a factorization for "
      f"**{sum(1 for r in mc['checked'] if r['search_recovers'])}/{len(mc['checked'])}** checked "
      f"(all isometric: {all(r['isometric'] for r in mc['checked']) if mc['checked'] else 'n/a'}).")
    fr = sp["free_frequency_report"]
    for kk, v in fr.items():
        w(f"- free-frequency report for {kk}: Ŝ = 0 at {v['S_hat_zero_frequencies']}; real n/2 frequency handled = "
          f"{v['real_free_frequency_handled']}; complex free frequencies unhandled = {v['complex_free_frequencies_unhandled']}")
    pc = rs["positive_control_Z12_forte"]
    w(f"\n**Positive control, Z12 Forte pair {pc['pair'][0]}/{pc['pair'][1]}**: homometric = {pc['homometric_in_Z12']}, "
      f"non-isometric = {pc['non_isometric_in_Z12']}, factors within Q-bound {pc['search']['coefficient_bound']} = "
      f"**{pc['search']['pairs_factoring']}/{pc['search']['pairs_total']}**" +
      (f" (P={pc['search']['examples'][0]['P']}, Q={pc['search']['examples'][0]['Q']})" if pc['search']['examples'] else "") + ".")
    rr = rs["rs_reachable_classes_Z8"]
    w(f"\n**RS-reachable classes in Z8** (all P×Q with coefficients in [−{rr['coefficient_bound']}, {rr['coefficient_bound']}]): "
      f"{len(rr['non_isometric_classes_reachable'])} non-isometric homometric class(es) of 4-subsets have the form (PQ, PQ(x⁻¹)).")
    for c in rr["non_isometric_classes_reachable"]:
        w(f"- {c['A']} / {c['A_prime']}  P={c['P']} Q={c['Q']}")
    w("\nThe set-level search is the naive reading of the theorem; the signed polynomial search is the "
      "theorem's actual form (Laurent polynomials with integer coefficients). A pair not found within the "
      "bound is unresolved, not refuted.\n")
    w("\nForte Z-relation {0,1,4,6}/{0,1,3,7}: " +
      (f"present, {rs['forte_Z_relation_0146_0137'][0]['factors']} factorizations, e.g. "
       f"{rs['forte_Z_relation_0146_0137'][0]['example']}" if rs["forte_Z_relation_0146_0137"] else "not among the pairs") + "\n")
    e = out["E07a_548_vs_this_universe"]
    w("## Relation to the E07a joint-genuine word pairs (548)\n")
    w("| quantity | value |")
    w("|---|---|")
    for k, v in e.items():
        w(f"| {k} | {v} |")
    w("\nWords are ordered and may repeat states; subsets are unordered and distinct. The two universes "
      "share only the word pairs whose components are 4 distinct states, and even there the readouts differ "
      "(ordered vector vs multiset).")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    out = run()
    docs = os.path.join(ROOT, "docs")
    with open(os.path.join(docs, "experiment_07_T2_rosenblatt_seymour.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    write_md(out, os.path.join(docs, "experiment_07_T2_rosenblatt_seymour.md"))
    for k in ("ring", "cube"):
        t = out[k]
        print(f"{t['label']:8s} |G|={t['group_order']:2d} same={t['pairs_same_multiset']} iso={t['pairs_via_isometry']} non-iso={t['pairs_non_isometric']}")
    print("D8∩B3 =", out["D8_cap_B3_order"], " iso under both =", out["pairs_isometric_under_both"])
    rs = out["rosenblatt_seymour"]
    print(f"RS sets: {rs['set_factorizations_B_plus_C']}/{rs['non_isometric_ring_pairs']} pairs factor as B+C / B-C")
    sp = rs["spectral_search"]
    print(f"RS spectral (Q bound {sp['coefficient_bound']}, P derived): {sp['pairs_factoring']}/{sp['pairs_total']} orbit-pairs factor; classes: {sp['classes']}")
    print("Forte pair in Z8:", rs["forte_Z_relation_0146_0137"][:1] or "not homometric in Z8")
    pc = rs["positive_control_Z12_forte"]; print("Z12 Forte control:", pc["homometric_in_Z12"], pc["non_isometric_in_Z12"], "factors:", pc["search"]["pairs_factoring"], pc["search"]["examples"][:1])
    print("RS-reachable Z8 classes (bound 1):", rs["rs_reachable_classes_Z8"]["non_isometric_classes_reachable"])
    print("mechanics control:", json.dumps({k: v for k, v in rs["mechanics_control"].items() if k != "checked"}), [ (r["isometric"], r["search_recovers"]) for r in rs["mechanics_control"]["checked"]])
    print("free freq:", sp["free_frequency_report"])
    print("548 vs sets:", json.dumps(out["E07a_548_vs_this_universe"]))
