# RULES V2 — noise band and thinness criterion (pre-registered re-scoring)

Order (Kavik via Claude, 2026-10-02): "rules: add the noise band and the
thinness criterion; re-score existing data under them." Committed before
`rescore_v2.py` exists. The outcome enum keeps its four members; V2 adds
two gates in front of FUNNEL_FOUND and a tolerance in front of every
monotonicity test. Existing data is re-scored; nothing is re-run.

## Defect being repaired (recorded in SOMS and Mandala RESULTS.md)

A literal monotonicity test on a 20-seed estimate has no noise band, so it
fires on noise (Mandala N=21: |F| 405, 301, 317) and passes on a
start-independent curve (SOMS: P = f(eps) only, |F| 4096, 3163, 12, 0, 0).

## Rule N (noise band)

For a sequence q(r_1), ..., q(r_m) over the drive grid (q = |F| or
mean P), a step r_i -> r_{i+1} is a VIOLATION of the predicted direction
only if the observed change in the wrong direction exceeds 2 sd_i, where
sd_i is the standard deviation of q(r_i) - q(r_{i+1}) under a bootstrap
that resamples each configuration's n seed outcomes with replacement
(1000 draws, numpy default_rng(0)); runs at different r are independent,
so sd_i = sqrt(var_i + var_{i+1}). "Non-increasing" means no violation.

## Rule T (thinness), two gates in front of FUNNEL_FOUND

At the slowest drive at which F is non-empty:

    T1  minority      |F| / N_starts <= 0.25        [CHOICE 1: 0.25 stipulated]
    T2  selective     per-configuration dispersion ratio > 1 with a
                      chi-square tail < 0.01, OR at least one configuration
                      flagged at Bonferroni 0.05 / N_starts (exact two-sided
                      binomial tail against the pooled rate)

FUNNEL_FOUND requires the delivered rule's conditions (non-empty,
non-increasing under Rule N, persists) AND T1 AND T2. A set failing T1 is
reported NOT_FOUND_IN_RANGE with qualifier `set not thin`; failing T2,
`not start-selective`. Where T2 cannot be computed (starts are random
seeds, not enumerated configurations) it is NOT_EVALUABLE and the outcome
carries that qualifier rather than passing or failing it.

## Pre-registered re-scoring predictions

    SOMS       Rule N: the 4096, 3163, 12, 0, 0 sequence is non-increasing
               (no violation). T1 passes at eps = 0.1 (12/4096). T2 FAILS
               (dispersion 1.012, chi2 tail 0.29, 0 flagged).
               -> NOT_FOUND_IN_RANGE, `not start-selective`
    Mandala    N=15: Rule N no violation (monotone as delivered); T1 FAILS
               (360/512 = 0.70) -> NOT_FOUND_IN_RANGE, `set not thin`.
               N=21: the 301 -> 317 step is INSIDE 2 sd under Rule N (so
               Q3 re-scores HELD); T1 FAILS (317/512) -> NOT_FOUND_IN_RANGE,
               `set not thin`. T2 passes at both N (greedy-ok vs
               greedy-fails split is a start effect).
    GO (C20)   the GAS success set per width at B = 2000 (25, 15, 1, 0, 0
               of 32): Rule N non-increasing in w; T1 passes only at
               w = 0.4 (1/32); T2 NOT_EVALUABLE (one seed per start, starts
               not enumerated). -> FUNNEL_FOUND stands at w = 0.4 ONLY,
               with qualifier `start-selectivity NOT_EVALUABLE`; at
               w <= 0.2 nothing persists -> NOT_FOUND_IN_RANGE.

A re-scoring that contradicts these predictions is reported as such.
