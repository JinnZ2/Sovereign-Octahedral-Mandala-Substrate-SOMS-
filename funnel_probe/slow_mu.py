#!/usr/bin/env python3
"""
slow_mu.py -- the DISCRETE ANALOG of a singular funnel on SOMSEngine's energy.

LABEL: funnels are defined for continuous phase space. This is a discrete
analog (8-state cells, Metropolis dynamics) and every number below is about
that analog.

Step 1 (code reading, reported in RESULTS.md): SOMSEngine.anneal() carries an
open-loop temperature schedule and no state-coupled adaptive variable.

Step 2 (this file): the paper's eq (10) added in funnel_probe/ only.
    fast   one Metropolis sweep per unit time, T = 1, effective energy
           mu * K * E(s), E = SOMSEngine.energy_landscape (alpha = 0.5),
           proposal mixture as the engine's relax_step
    slow   mu <- mu + eps (-mu + a m(s) - b),  a = 3, b = 2
           m(s) = 1 - E(s)/E_max (order parameter, 1 at the ground state)
    start  mu0 = 4, s0 = every one of the 8^4 = 4096 configurations
    exits  at T_MAX = 400 sweeps:  ORDERED mu > 0.5 | DISORDERED mu < -1.0 |
           INCONCLUSIVE otherwise; also whether the chain ever visited an
           exact ground state (all four cells equal)

The energy is a vectorised twin of SOMSEngine's, CHECKED against
SOMSEngine.energy_landscape on 200 random configurations before any sweep.
Nothing in src/ is edited.  Grid, K rule and predictions: PREREGISTRATION.md.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from src.octahedral_physics import SOMSEngine                      # noqa: E402
from src.mandala_structure import MandalaMap                        # noqa: E402
from src.octahedral_lookup import ALLOWED_TRANSITIONS, OCTAHEDRAL_EIGENVALUES  # noqa: E402

N = 4
A_, B_, MU0 = 3.0, 2.0, 4.0
T_MAX = 400
EPS_LIST = [0.4, 0.2, 0.1, 0.05, 0.025]
SEEDS = 20
K_PRESET, K_FALLBACK = 10.0, [15.0, 20.0, 30.0]
ORDERED_MU, DISORDERED_MU = 0.5, -1.0

ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
EV = np.array([OCTAHEDRAL_EIGENVALUES[s] for s in range(8)])
ANG = np.sin(np.radians(ANGLES[:, None] - ANGLES[None, :])) ** 2
TEN = ((EV[:, None, :] - EV[None, :, :]) ** 2).sum(-1)
ALLOWED = np.array([ALLOWED_TRANSITIONS[s] for s in range(8)])      # (8, 4)


def geometry():
    m = MandalaMap(u=20, depth=1)
    pos = m.pos[1:1 + N]                                            # ring-1 petals 0..3
    d = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=-1)
    d_nn = d[~np.eye(N, dtype=bool)].min()
    dn = d / d_nn                                                   # J_nn = 1
    eng = SOMSEngine(num_cells=N, problem_type="PROTEIN_FOLDING")
    J = eng.fret_coupling(dn + np.eye(N))
    return eng, J, dn


def pair_table(alpha):
    return alpha * ANG + (1.0 - alpha) * TEN


def energy(S, J, PAIR):
    """S: (M, N) ints -> (M,) energies, identical to SOMSEngine.energy_landscape."""
    E = np.zeros(len(S))
    for i in range(N):
        for j in range(i + 1, N):
            E += J[i, j] * PAIR[S[:, i], S[:, j]]
    return E


def all_configs():
    idx = np.arange(8 ** N)
    return np.stack([(idx // 8 ** k) % 8 for k in range(N)], axis=1).astype(np.int64)


def check_twin(eng, J, PAIR, rng):
    S = rng.integers(0, 8, (200, N))
    mine = energy(S, J, PAIR)
    worst = 0.0
    for k in range(200):
        eng.state_indices = S[k].copy()
        eng.orientations = ANGLES[eng.state_indices]
        worst = max(worst, abs(eng.energy_landscape(J) - mine[k]))
    return worst


def sweep(S, mu, K, J, PAIR, alpha, rng):
    M = len(S)
    ar = np.arange(M)
    order = rng.random((M, N)).argsort(axis=1)
    for pos in range(N):
        i = order[:, pos]
        old = S[ar, i]
        free = rng.random(M) < alpha
        r7 = rng.integers(0, 7, M)
        new_free = r7 + (r7 >= old)
        new_allowed = ALLOWED[old, rng.integers(0, 4, M)]
        new = np.where(free, new_free, new_allowed)
        dE = np.zeros(M)
        for j in range(N):
            Sj = S[:, j]
            dE += np.where(j != i, J[i, j] * (PAIR[new, Sj] - PAIR[old, Sj]), 0.0)
        dEeff = mu * K * dE
        acc = (dEeff <= 0) | (rng.random(M) < np.exp(-np.clip(dEeff, -700, 700)))
        S[ar, i] = np.where(acc, new, old)
    return S


def steady_m(mu_val, K, J, PAIR, alpha, E_max, rng, chains=512, burn=1000, meas=1000):
    S = rng.integers(0, 8, (chains, N))
    mu = np.full(chains, mu_val)
    acc = 0.0
    for t in range(burn + meas):
        S = sweep(S, mu, K, J, PAIR, alpha, rng)
        if t >= burn:
            acc += (1.0 - energy(S, J, PAIR) / E_max).mean()
    return acc / meas


def bistability(K, J, PAIR, alpha, E_max, rng):
    mus = np.linspace(-3.0, 5.0, 33)
    F = np.array([A_ * steady_m(m, K, J, PAIR, alpha, E_max, rng) - B_ for m in mus])
    g = F - mus
    stable, unstable = [], []
    for k in range(len(mus) - 1):
        if g[k] > 0 and g[k + 1] <= 0:
            stable.append(float(mus[k] - g[k] * (mus[k + 1] - mus[k]) / (g[k + 1] - g[k])))
        if g[k] < 0 and g[k + 1] >= 0:
            unstable.append(float(mus[k] - g[k] * (mus[k + 1] - mus[k]) / (g[k + 1] - g[k])))
    return {"K": K, "mu_grid": mus.tolist(), "F": F.tolist(), "stable": stable, "unstable": unstable}


def run_eps(eps, K, J, PAIR, alpha, E_max, configs, frozen=False):
    M = len(configs) * SEEDS
    S = np.repeat(configs, SEEDS, axis=0).copy()
    cfg_of = np.repeat(np.arange(len(configs)), SEEDS)
    mu = np.full(M, MU0)
    rng = np.random.default_rng(int(round(eps * 1e6)) if not frozen else 999_983)
    visited = np.zeros(M, dtype=bool)
    for t in range(T_MAX):
        S = sweep(S, mu, K, J, PAIR, alpha, rng)
        E = energy(S, J, PAIR)
        visited |= (E == 0.0)
        if not frozen:
            mu += eps * (-mu + A_ * (1.0 - E / E_max) - B_)
    dis = (mu < DISORDERED_MU)
    ordr = (mu > ORDERED_MU)
    P_dis = np.bincount(cfg_of, weights=dis, minlength=len(configs)) / SEEDS
    P_ord = np.bincount(cfg_of, weights=ordr, minlength=len(configs)) / SEEDS
    P_vis = np.bincount(cfg_of, weights=visited, minlength=len(configs)) / SEEDS
    return {"P_dis": P_dis, "P_ord": P_ord, "P_vis": P_vis,
            "inconclusive": float(1.0 - dis.mean() - ordr.mean())}


def main(argv):
    quick = "--quick" in argv
    t0 = time.time()
    eng, J, dn = geometry()
    alpha = eng.alpha
    PAIR = pair_table(alpha)
    rng = np.random.default_rng(0)
    out = {"label": "DISCRETE ANALOG (8-state cells, Metropolis); not a continuous-phase-space funnel",
           "alpha": alpha, "J": J.tolist(), "d_norm": dn.tolist()}
    print("DISCRETE FUNNEL ANALOG on SOMSEngine energy, n=%d cells, alpha=%.2f" % (N, alpha))
    print("  J (nn normalised to 1):\n   ", np.array2string(J, precision=4))
    worst = check_twin(eng, J, PAIR, rng)
    print("  twin energy vs SOMSEngine.energy_landscape on 200 random configs: max |dE| = %.2e  %s"
          % (worst, "PASS" if worst < 1e-9 else "FAIL"))
    out["twin_check_max_abs_err"] = worst
    if worst >= 1e-9:
        return 1
    configs = all_configs()
    E_all = energy(configs, J, PAIR)
    E_max = float(E_all.max())
    m0 = 1.0 - E_all / E_max
    n_ground = int((E_all == 0.0).sum())
    print("  4096 configurations: E_max = %.4f, exact ground states (E=0): %d, m(s0) range [%.3f, 1]"
          % (E_max, n_ground, m0.min()))
    out.update({"E_max": E_max, "n_ground": n_ground})

    # --- K: bistability check with the pre-registered fallback rule ---
    K = None
    bis_log = []
    for Kc in [K_PRESET] + ([] if quick else K_FALLBACK):
        b = bistability(Kc, J, PAIR, alpha, E_max, np.random.default_rng(11))
        bis_log.append(b)
        print("  K=%-5g self-consistency map: stable fixed points %s, unstable %s"
              % (Kc, ["%.2f" % s for s in b["stable"]], ["%.2f" % u for u in b["unstable"]]))
        if len(b["stable"]) >= 2:
            K = Kc; break
    out["bistability"] = bis_log
    if K is None:
        out["outcome"] = "NOT_IN_CLASS (no K in {10,15,20,30} gives two stable fixed points)"
        print("  OUTCOME:", out["outcome"])
        json.dump(out, open("slow_mu_results.json", "w"), indent=1)
        return 0
    out["K"] = K
    print("  K used: %g  (P1 bistability: HELD)" % K)

    # --- control: mu frozen at 4 ---
    ctl = run_eps(0.0, K, J, PAIR, alpha, E_max, configs, frozen=True)
    print("  control (mu frozen at %g): ground visited within %d sweeps in %.1f%% of (config, seed) pairs"
          % (MU0, T_MAX, 100 * ctl["P_vis"].mean()))
    out["control_ground_visit_rate"] = float(ctl["P_vis"].mean())

    # --- the sweep over eps ---
    eps_list = EPS_LIST[:2] if quick else EPS_LIST
    rows = []
    print("\n  eps      |F|   maxP(dis)  meanP(dis)  P(dis|m0 min)  ground-visit  inconclusive   (F = configs with P(DISORDERED) > 0.5)")
    for eps in eps_list:
        r = run_eps(eps, K, J, PAIR, alpha, E_max, configs)
        F = np.where(r["P_dis"] > 0.5)[0]
        # P(dis) binned by initial order parameter
        bins = np.quantile(m0, [0, 0.25, 0.5, 0.75, 1.0])
        which = np.clip(np.searchsorted(bins, m0, side="right") - 1, 0, 3)
        by_m = [float(r["P_dis"][which == q].mean()) for q in range(4)]
        row = {"eps": eps, "F_size": int(len(F)), "F_configs": configs[F].tolist()[:50],
               "maxP_dis": float(r["P_dis"].max()), "meanP_dis": float(r["P_dis"].mean()),
               "P_dis_at_min_m0": float(r["P_dis"][np.argmin(m0)]),
               "P_dis_by_m0_quartile": by_m, "ground_visit_rate": float(r["P_vis"].mean()),
               "inconclusive": r["inconclusive"], "P_dis_all": r["P_dis"].tolist()}
        rows.append(row)
        print("  %-7g %5d   %8.3f   %8.3f   %10.3f   %10.3f   %10.3f    by m0 quartile %s"
              % (eps, len(F), row["maxP_dis"], row["meanP_dis"], row["P_dis_at_min_m0"],
                 row["ground_visit_rate"], row["inconclusive"], ["%.2f" % v for v in by_m]))
    out["sweep"] = rows

    # --- pre-registered predictions ---
    sizes = [r["F_size"] for r in rows]
    maxp = [r["maxP_dis"] for r in rows]
    p2 = ctl["P_vis"].mean() >= 0.95
    p3 = all(sizes[i + 1] <= sizes[i] for i in range(len(sizes) - 1))
    p4 = sizes[-1] > 0
    pts = [(1.0 / r["eps"], np.log(r["maxP_dis"])) for r in rows if r["maxP_dis"] > 0]
    slope = None
    if len(pts) >= 2:
        xs, ys = zip(*pts); slope = float(np.polyfit(xs, ys, 1)[0])
    p5 = slope is not None and slope < 0
    p6 = all(r["P_dis_by_m0_quartile"][0] >= r["P_dis_by_m0_quartile"][3] for r in rows)
    preds = {"P1 bistability at the chosen K": True,
             "P2 control (mu frozen at 4): ground visited in >= 95% of pairs": bool(p2),
             "P3 |F(eps)| non-increasing as eps decreases": bool(p3),
             "P4 |F| > 0 at the smallest eps (persists)": bool(p4),
             "P5 ln(max P_dis) falls linearly in 1/eps (slope %s)" % ("%.3f" % slope if slope is not None else "n/a"): bool(p5),
             "P6 lowest-m0 quartile has the highest P(dis) at every eps": bool(p6)}
    print("\nPRE-REGISTERED PREDICTIONS")
    for k, v in preds.items():
        print("  %s %s" % ("HELD  " if v else "FAILED", k))
    out["predictions"] = preds
    incon = max(r["inconclusive"] for r in rows)
    if incon > 0.05:
        outcome = "INCONCLUSIVE (%.1f%% chains neither ORDERED nor DISORDERED at T_MAX)" % (100 * incon)
    elif all(s == 0 for s in sizes):
        outcome = "NOT_FOUND_IN_RANGE (F empty at every eps in %s)" % eps_list
    elif sum(1 for s in sizes if s > 0) >= 3 and p3:
        outcome = "FUNNEL_FOUND (discrete analog)"
    else:
        outcome = "NOT_FOUND_IN_RANGE (F non-empty at %d of %d eps, narrowing=%s; eps in %s)" % (
            sum(1 for s in sizes if s > 0), len(sizes), p3, eps_list)
    out["outcome"] = outcome
    print("\nOUTCOME:", outcome)
    print("scope: stochastic (Metropolis, fixed seeds), K=%g, a=3, b=2, mu0=4, T_MAX=%d, %d seeds/config,"
          " DISCRETE state space with a continuous slow variable; %.0f s" % (K, T_MAX, SEEDS, time.time() - t0))
    json.dump(out, open("slow_mu_results.json", "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
