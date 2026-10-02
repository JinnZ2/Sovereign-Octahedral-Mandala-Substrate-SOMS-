#!/usr/bin/env python3
"""
per_config_check.py -- the thin-structure check the quartiles could hide.

Reads the raw slow_mu run (P(DISORDERED) per CONFIGURATION, 20 seeds each)
and asks, per eps: is any single configuration's count outside the sampling
error of a start-independent probability?  A funnel is thin by definition;
4096/4 = 1024 configurations per quartile averages one out.

    per configuration: exact two-sided binomial tail probability of its
                       count k out of 20 under the pooled p_hat
    flag               tail < 0.05 / 4096   (Bonferroni over configurations)
    lenient count      configurations with tail < 0.05, against the 205
                       expected from 4096 draws under the null
    dispersion         var(P_config) / (p_hat (1-p_hat) / 20), and the
                       chi-square tail of the pooled dispersion statistic

Usage: python3 funnel_probe/per_config_check.py <raw slow_mu_results.json>
"""
import json
import sys
from math import comb

import numpy as np
from scipy.stats import chi2

N_SEEDS = 20


def binom_two_sided(k, n, p):
    pmf = np.array([comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(n + 1)])
    return float(pmf[pmf <= pmf[k] + 1e-15].sum())


def main(path):
    d = json.load(open(path))
    configs = np.stack([(np.arange(4096) // 8 ** k) % 8 for k in range(4)], axis=1)
    print("per-configuration check, %d seeds each, Bonferroni threshold %.2e" % (N_SEEDS, 0.05 / 4096))
    print("  eps     p_hat   flagged(Bonf)  flagged(0.05)  expected(0.05)  dispersion  chi2 tail   min P  max P")
    out = []
    for r in d["sweep"]:
        P = np.array(r["P_dis_all"])
        k = np.rint(P * N_SEEDS).astype(int)
        p = P.mean()
        if p <= 0 or p >= 1:
            tails = np.ones(len(P))
        else:
            cache = {kk: binom_two_sided(kk, N_SEEDS, p) for kk in range(N_SEEDS + 1)}
            tails = np.array([cache[kk] for kk in k])
        bonf = np.where(tails < 0.05 / 4096)[0]
        lenient = int((tails < 0.05).sum())
        disp = P.var() / (p * (1 - p) / N_SEEDS) if 0 < p < 1 else float("nan")
        # pooled dispersion statistic: sum (k - n p)^2 / (n p (1-p)) ~ chi2(4095) under the null
        stat = float((((k - N_SEEDS * p) ** 2) / (N_SEEDS * p * (1 - p))).sum()) if 0 < p < 1 else float("nan")
        tail = float(chi2.sf(stat, len(P) - 1)) if 0 < p < 1 else float("nan")
        print("  %-6g  %.3f   %13d  %13d  %14d  %10.3f  %9.3g   %.2f   %.2f"
              % (r["eps"], p, len(bonf), lenient, int(0.05 * 4096), disp, tail, P.min(), P.max()))
        for i in bonf:
            print("      flagged config %s  P=%.2f  m(s0)=%.3f" % (configs[i].tolist(), P[i], 1 - 0))
        out.append({"eps": r["eps"], "p_hat": float(p), "flagged_bonferroni": [int(i) for i in bonf],
                    "flagged_005": lenient, "dispersion_ratio": disp, "chi2_tail": tail})
    n_flag = sum(len(o["flagged_bonferroni"]) for o in out)
    print("\nVERDICT: %s" % (
        "all configurations inside sampling error at every eps -> genuinely start-independent; P6 fails cleanly"
        if n_flag == 0 else "%d configuration(s) outside sampling error -> thin structure the quartiles hid" % n_flag))
    json.dump(out, open("per_config_check.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
