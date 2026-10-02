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
