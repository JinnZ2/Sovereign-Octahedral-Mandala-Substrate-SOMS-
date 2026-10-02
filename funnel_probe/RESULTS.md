# funnel_probe — results (SOMS)

LABEL: DISCRETE ANALOG. Funnels are defined for continuous phase space;
everything below is about 8-state cells under Metropolis dynamics with a
continuous slow variable added in this folder. Nothing in `src/` was edited.

Pre-registration: commit 9b4d913. Step 1 (noise): `NOISE_RESULTS.md`,
commit f40097b. Code: `slow_mu.py`, commit db4a1e7. Run from a temp
directory, 326 s; log in `samples/slow_mu_run.sample.txt`, numbers in
`samples/slow_mu_results.json` (per-config arrays trimmed, their summary
statistics kept).

## What did not hold, first

    P6  FAILED  the lowest-m(s0) quartile does not have the highest
                P(DISORDERED). At every eps the four quartiles of initial
                order read the same number (0.88/0.88/0.87/0.87 at eps=0.4;
                0.25/0.25/0.25/0.24 at eps=0.1; 0.04 x4 at 0.05).
    P4  FAILED  |F| = 0 at eps = 0.05 and 0.025; nothing persists.

And the consequence, which is the result of this folder: the spread of
P(DISORDERED) across the 4096 starts equals the 20-seed binomial noise at
every eps —

    eps     mean P   std across configs   binomial sd (n=20)   max over configs
    0.4     0.874        0.075                 0.074               1.000
    0.2     0.605        0.111                 0.109               0.950
    0.1     0.249        0.097                 0.097               0.550
    0.05    0.037        0.042                 0.042               0.250
    0.025   0.000        0.003                 0.003               0.050

so P(DISORDERED) is a function of eps alone and the initial configuration
carries no information. The "funnel set" F(eps) = {configs with P > 0.5}
goes 4096, 3163, 12, 0, 0 because a start-independent probability crosses
0.5 between eps = 0.2 and 0.1, not because a thin set of starts survives;
the 12 at eps = 0.1 are the upper tail of 4096 draws from Binomial(20, 0.25).

## Per-configuration check (follow-on order, 2026-10-02)

The quartile reading above averages 1024 starts per bin, which is exactly
where a thin start set would vanish. The map is exhaustive, so the check is
run per CONFIGURATION: each of the 4096 starts has 20 seeds, so its hit
count is Binomial(20, p) if the start carries no information, with p the
pooled rate at that eps. `per_config_check.py` scores every configuration
with an exact two-sided binomial tail against the pooled p, flags a
configuration when its tail is below 0.05/4096 (Bonferroni), and reports
the dispersion ratio (variance across configs / binomial variance) with a
chi-square tail. Output: `samples/per_config_check.sample.txt`,
`samples/per_config_check.json`.

    eps     p_hat   flagged(Bonf)  flagged(0.05)  expected(0.05)  dispersion  chi2 tail   min P  max P
    0.4     0.874               0            140             204       1.034     0.0623   0.55   1.00
    0.2     0.605               0            160             204       1.023      0.143   0.15   0.95
    0.1     0.249               0            157             204       1.012      0.291   0.00   0.55
    0.05    0.037               0            142             204       0.988      0.694   0.00   0.25
    0.025   0.000               0             20             204       0.995      0.576   0.00   0.05

Zero configurations flagged at Bonferroni at every eps; the uncorrected
0.05 flags come in BELOW the 204 expected by chance; dispersion sits at 1.0
with chi-square tails of 0.06 to 0.69. The per-configuration spread is the
20-seed binomial noise and nothing else, at the finest resolution the
exhaustive map allows.

    VERDICT   all inside sampling error at every eps
              -> genuinely start-independent; P6 fails cleanly
              -> no thin structure hidden by the quartiles

The 12 configurations in F at eps = 0.1 are the upper tail of 4096 draws
from Binomial(20, 0.25): P(X >= 11) = 0.0094, expected count 4096 x 0.0094
= 38, observed 12 (a deficit, not an excess). The one caveat is power: 20
seeds per start resolves a per-config p that differs from the pool by about
0.3 at Bonferroni; a start set whose P differed by less than that would
not be flagged here and would need more seeds per start, not more starts.

## Outcome enum, two readings kept apart

    by the pre-registered rule   FUNNEL_FOUND (discrete analog)
                                 — F non-empty at 3 of 5 eps and non-increasing,
                                   the rule's literal conditions
    by the paper's own property  NOT a funnel: a funnel is a set of INITIAL
                                 CONDITIONS reaching the forbidden attractor;
                                 here every start reaches it with the same
                                 probability, which the rule did not test
                                 and P6 did.

The rule is reported as written and not amended after the fact. Its defect
is recorded: "a set of configurations with P > 0.5 that narrows with eps" is
satisfiable by a uniform P(eps) crossing 0.5, so a future pre-registration
on this construction needs start-selectivity (P6, or a between-config
variance above binomial) as a gate, not a side prediction.

## Why the start is forgotten (reading, not a pre-registered result)

With K = 15 and mu0 = 4 the effective energy scale is 60 x dE at the first
sweep; the control with mu frozen at 4 visits an exact ground state within
400 sweeps in 100% of pairs, and in practice within one or two. The slow
variable moves by eps(-mu + 3m - 2) per sweep: at eps = 0.4 and m ~ 0.3 on
the first sweep that is -2 per sweep, so whether mu turns negative before
the chain has ordered is decided by the first one or two Metropolis sweeps
— a race between two rates, with the initial configuration erased on the
same timescale the race is decided on. The paper's funnel exists because x
near 0 has a continuum of depths to sit at; eight states per cell has no
analogous depth coordinate. That is the discrete analog's answer, and it is
a property of the construction, stated as such.

## What held

    P1  K = 10 gives one stable fixed point (-1.92): the pre-registered
        fallback fired and K = 15 gives two (-1.94, 0.85; unstable 0.34).
        Recorded, not tuned: the rule and its order were fixed in advance.
    P2  control, mu frozen at 4: ground visited in 100% of pairs.
    P3  |F(eps)| non-increasing: 4096, 3163, 12, 0, 0.
    P5  ln(max P) vs 1/eps slope -0.082 (negative; the exponential shape
        holds for the MEAN as well: 0.874, 0.605, 0.249, 0.037, 0.000).
    twin energy = SOMSEngine.energy_landscape to 4.4e-16 on 200 configs.
    INCONCLUSIVE fraction <= 3.5% at every eps (threshold 5%).

## Step 1 report (code reading)

`SOMSEngine.anneal()` carries one slow drive, the temperature
`T *= (T_final/T_start)^(1/(n_steps-1))` once per sweep: open-loop, driven
by the step counter, never by the state. `j_ij` and `alpha` are fixed. No
state-coupled adaptive variable exists in `src/`; the one used here was
added in `funnel_probe/` as the paper's eq (10).

Scope: stochastic (Metropolis, fixed seeds, 20 per start), K = 15, a = 3,
b = 2, mu0 = 4, T_MAX = 400 sweeps, Euler step dt = 1 sweep on mu (coarse
at eps = 0.4, pre-registered), n = 4 cells on MandalaMap(u=20, depth=1)
ring-1 petals with J_nn = 1; DISCRETE state space, continuous slow variable.

## Re-scored under RULES V2 (noise band + thinness; `RULES_V2.md`, `rescore_v2.py`, nothing re-run)

Output `samples/rescore_v2.sample.txt`, numbers `samples/rescore_v2_results.json`.

    RULES V2 re-scoring -- SOMS slow-mu sweep (per-configuration counts, 20 seeds, 4096 configs), eps grid [0.4, 0.2, 0.1, 0.05, 0.025]
      Rule N on |F| (predicted non-increasing as eps falls): ['4096', '3163', '12', '0', '0']
         step 0: change -933  band +-49.26  ok
         step 1: change -3151  band +-52.56  ok
         step 2: change -12  band +-19.83  ok
         step 3: change +0  band +-0.3183  ok
      Rule N on mean P(dis): ['0.8743', '0.6052', '0.2486', '0.03662', '0.0002441']
         step 0: change -0.2691  band +-0.004006  ok
         step 1: change -0.3565  band +-0.004454  ok
         step 2: change -0.212  band +-0.003258  ok
         step 3: change -0.03638  band +-0.00132  ok
      T gates at the slowest drive with F non-empty (eps = 0.1): |F|/N = 0.0029 -> T1 True ; dispersion 1.012 chi2 tail 0.291 flagged 0 -> T2 False
      delivered-rule reading: FUNNEL_FOUND ; V2 OUTCOME: NOT_FOUND_IN_RANGE, `not start-selective` (dispersion 1.012, chi2 tail 0.291, flagged 0)
      RULES_V2 prediction for SOMS: NOT_FOUND_IN_RANGE, `not start-selective` -> HELD

What V2 changes here: the delivered rule's FUNNEL_FOUND falls to NOT_FOUND_IN_RANGE
on the T2 gate alone -- the set at eps = 0.1 is thin (12 of 4096) and is NOT
start-selective (dispersion 1.012, no configuration flagged), which is a
binomial tail wearing a funnel's size. Rule N finds no violation anywhere
(the sequence was genuinely monotone). The re-scoring prediction HELD.
