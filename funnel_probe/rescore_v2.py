#!/usr/bin/env python3
"""
rescore_v2.py -- RULES_V2.md applied to EXISTING data (nothing re-run): Rule N (noise band,
bootstrap over seeds) and Rule T (thinness T1, start-selectivity T2) in front of FUNNEL_FOUND.
Usage: python3 funnel_probe/rescore_v2.py   (writes rescore_v2_results.json into the cwd)
"""

import json, os, sys
from math import comb
import numpy as np
from scipy.stats import chi2

HERE = os.path.dirname(os.path.abspath(__file__))
DRAWS, SEED, T1_SHARE, ALPHA_T2 = 1000, 0, 0.25, 0.01    # RULES_V2.md; T1_SHARE is [CHOICE 1]


def bootstrap(counts, n, in_F, draws=DRAWS, seed=SEED):
    """Resample each configuration's n seed outcomes: k* ~ Binomial(n, k/n). Returns (|F|*, meanP*) arrays."""
    rng = np.random.default_rng(seed)
    k = np.asarray(counts); p = k / n
    sim = rng.binomial(n, p, size=(draws, len(k))) / n
    return in_F(sim).sum(axis=1), sim.mean(axis=1)


def rule_n(obs, boots, direction):
    """direction: 'nonincreasing' or 'nondecreasing' along the grid order. Returns per-step records."""
    out = []
    for i in range(len(obs) - 1):
        change = obs[i + 1] - obs[i]
        sd = float(np.sqrt(boots[i].var() + boots[i + 1].var()))
        wrong = change > 0 if direction == "nonincreasing" else change < 0
        out.append({"step": i, "change": float(change), "sd": sd, "band": 2 * sd,
                    "violation": bool(wrong and abs(change) > 2 * sd), "wrong_direction": bool(wrong)})
    return out


def two_sided_tails(counts, n, p):
    pmf = np.array([comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(n + 1)])
    tails = np.array([pmf[pmf <= pmf[j] + 1e-15].sum() for j in range(n + 1)])
    return tails[np.asarray(counts)]


def t_gates(counts, n, in_F):
    k = np.asarray(counts); N = len(k); p = k.mean() / n
    share = float(in_F(k / n).sum() / N)
    t1 = share <= T1_SHARE
    if p <= 0 or p >= 1:
        return {"share": share, "T1": t1, "dispersion": None, "chi2_tail": None, "flagged": 0, "T2": False, "p": p}
    disp = float(k.var() / (n * p * (1 - p)))
    stat = float(((k - n * p) ** 2 / (n * p * (1 - p))).sum()); tail = float(chi2.sf(stat, N - 1))
    flagged = int((two_sided_tails(k, n, p) < 0.05 / N).sum())
    t2 = (disp > 1 and tail < ALPHA_T2) or flagged > 0
    return {"share": share, "T1": t1, "dispersion": disp, "chi2_tail": tail, "flagged": flagged, "T2": t2, "p": p}


def outcome(nonempty, rule_n_ok, persists, gates, t2_evaluable=True):
    if not nonempty:
        return "NOT_FOUND_IN_RANGE (F empty at every drive)"
    if not rule_n_ok:
        return "NOT_FOUND_IN_RANGE (not non-increasing under Rule N)"
    if not persists:
        return "NOT_FOUND_IN_RANGE (does not persist at the slowest drive)"
    if not gates["T1"]:
        return "NOT_FOUND_IN_RANGE, `set not thin` (|F|/N = %.3f > %.2f)" % (gates["share"], T1_SHARE)
    if not t2_evaluable:
        return "FUNNEL_FOUND, qualifier `start-selectivity NOT_EVALUABLE`"
    if not gates["T2"]:
        return "NOT_FOUND_IN_RANGE, `not start-selective` (dispersion %.3f, chi2 tail %.3f, flagged %d)" % (gates["dispersion"], gates["chi2_tail"], gates["flagged"])
    return "FUNNEL_FOUND (V2: thin and start-selective)"


def report_rule_n(name, obs, recs):
    print("  Rule N on %s: %s" % (name, ["%.4g" % o for o in obs]))
    for r in recs:
        print("     step %d: change %+.4g  band +-%.4g  %s" % (r["step"], r["change"], r["band"],
              "VIOLATION" if r["violation"] else ("wrong direction, inside band" if r["wrong_direction"] else "ok")))
    return not any(r["violation"] for r in recs)


def main():
    d = json.load(open(os.path.join(HERE, "samples", "slow_mu_per_config_counts.json")))
    n = d["n_seeds"]; eps = d["eps"]; C = [np.array(c) for c in d["counts_disordered"]]
    in_F = lambda P: P > 0.5
    print("RULES V2 re-scoring -- SOMS slow-mu sweep (per-configuration counts, %d seeds, %d configs), eps grid %s" % (n, len(C[0]), eps))
    F = [int(in_F(c / n).sum()) for c in C]; meanP = [float((c / n).mean()) for c in C]
    bF, bM = zip(*[bootstrap(c, n, in_F) for c in C])
    okF = report_rule_n("|F| (predicted non-increasing as eps falls)", F, rule_n(F, bF, "nonincreasing"))
    okM = report_rule_n("mean P(dis)", meanP, rule_n(meanP, bM, "nonincreasing"))
    nonempty = any(f > 0 for f in F); persists = F[-1] > 0
    slow = max(i for i in range(len(F)) if F[i] > 0) if nonempty else None
    g = t_gates(C[slow], n, in_F) if slow is not None else None
    if g:
        print("  T gates at the slowest drive with F non-empty (eps = %s): |F|/N = %.4f -> T1 %s ; dispersion %.3f chi2 tail %.3f flagged %d -> T2 %s"
              % (eps[slow], g["share"], g["T1"], g["dispersion"], g["chi2_tail"], g["flagged"], g["T2"]))
    out = outcome(nonempty, okF, True, g)   # 'persists' in the delivered rule meant non-empty at the smallest eps, which failed (P4); V2 gates are applied at the slowest NON-EMPTY drive, as RULES_V2 states
    print("  delivered-rule reading: FUNNEL_FOUND ; V2 OUTCOME: %s" % out)
    pred = "NOT_FOUND_IN_RANGE, `not start-selective`"
    print("  RULES_V2 prediction for SOMS: %s -> %s" % (pred, "HELD" if out.startswith(pred) else "FAILED"))
    json.dump({"F": F, "meanP": meanP, "gates": g, "outcome": out, "prediction_held": out.startswith(pred)},
              open("rescore_v2_results.json", "w"), indent=1)


if __name__ == "__main__":
    main()
