# PRE-REGISTRATION — funnel_probe/ (SOMS)

WORK ORDER: singular-funnel probes, 4 repos (Kavik via Claude, 2026-10-01).
Source under test: Yanchuk, Wieczorek, Jardon-Kojakhmetov, Alkhayuon,
PRL 137, 147202 (2026); arXiv:2601.02001.
Committed BEFORE any probe code exists in this folder. Nothing in `src/` is
edited. Run artifacts go to a temp directory.

LABEL, carried on every output: funnels are defined for continuous phase
space; what is built here is the DISCRETE ANALOG (8-state cells, Metropolis
dynamics), and every number is about that analog.

## Outcome enum

    FUNNEL_FOUND         a set of initial configurations ending in the
                         attractor the frozen-mu (reduced) picture forbids,
                         non-empty at 3+ eps and narrowing as eps falls
    NOT_FOUND_IN_RANGE   that set is empty at every eps in the grid (printed)
    NOT_IN_CLASS         no slow state-coupled variable, and the one added
                         here fails to produce two attractors
    INCONCLUSIVE         > 5% of chains end neither ORDERED nor DISORDERED
                         at the sweep cap

## Step 1 — does SOMSEngine have a slow adaptive variable? (code reading)

Report what `src/octahedral_physics.py` carries: `anneal()` holds a
temperature T updated by `T *= (T_final/T_start)^(1/(n_steps-1))` once per
sweep — an OPEN-LOOP schedule, driven by the step counter, not by the
state; `j_ij` is fixed; `alpha` is fixed; nothing feeds a mean field back
into any parameter. The paper's eq (10) is `dmu/dt = eps(-mu + a x - b)`,
a slow variable driven BY the fast state. Rule: a schedule that reads the
clock and not the state is reported as "slow drive present, state-coupled
adaptive variable absent", and step 2 adds one.

## Step 2 — the slow variable, added in funnel_probe/ only

    cells      n = 4: MandalaMap(u=20, depth=1), ring-1 petals 0..3
               (angles 0, 45, 90, 135 deg on one ring). Distances normalised
               so the nearest-neighbour coupling is 1 (the repo's own README
               normalisation); j = fret_coupling(d_norm + I).
    fast       SOMSEngine energy_landscape, problem_type PROTEIN_FOLDING
               (alpha = 0.5), reproduced in a vectorised twin
               (`funnel_probe/slow_mu.py`) that is CHECKED against
               SOMSEngine.energy_landscape on 200 random configurations
               (|dE| < 1e-9) before any sweep. Metropolis at T = 1 with
               effective energy  mu * K * E(s); proposal mixture as the
               engine's relax_step (free with prob alpha, else
               ALLOWED_TRANSITIONS); one sweep over the 4 cells in random
               order = one unit of time.
    order par. m(s) = 1 - E(s)/E_max,  E_max = max over all 4096 configs
    slow       mu <- mu + eps * (-mu + a*m(s) - b),  a = 3, b = 2  (eq 10,
               Euler with dt = one sweep). Fixed points of the reduced
               picture: ordered m=1 -> mu* = +1; disordered m=0 -> mu* = -2.
    K          the coupling scale. K = 10 is the pre-set value. Fallback
               rule, decided BEFORE any eps sweep: run the self-consistency
               map mu -> 3*<m>_ss(mu) - 2 (steady-state <m> from 2000
               sweeps at fixed mu) on mu in [-3, 5]; if it has fewer than
               two stable fixed points at K = 10, take the smallest K in
               {15, 20, 30} that gives two, and record which. If none does,
               the construction returns NOT_IN_CLASS.
    start      mu0 = 4 (the paper's), s0 = EVERY one of the 8^4 = 4096
               configurations (exhaustive, not sampled)
    eps        {0.4, 0.2, 0.1, 0.05, 0.025}
    seeds      20 per (configuration, eps); seed = eps_idx*10^6 +
               config_idx*32 + k; numpy default_rng
    cap        T_max = 400 sweeps (10 relaxation times at the smallest eps)
    exits      classified at T_max by the slow variable:
                 ORDERED     mu > +0.5   (the reduced picture's prediction
                                          for every start, since mu0 > 0)
                 DISORDERED  mu < -1.0   (the funnel-side attractor)
                 INCONCLUSIVE otherwise
               also recorded: whether the chain ever visited an exact
               ground state (all four cells equal, E = 0) before T_max.
    control    reduced picture: mu frozen at 4 (eps = 0), same seeds,
               P(visit ground within T_max) per configuration.

Readouts per eps: the FUNNEL SET F(eps) = configurations with
P(DISORDERED) > 0.5; |F(eps)|; max over configurations of P(DISORDERED);
P(DISORDERED) as a function of the initial order parameter m(s0); the
ground-visit rate.

Pre-registered predictions:
    P1  bistability at the chosen K (two stable fixed points)
    P2  control (mu frozen at 4): ground visited within T_max for >= 95%
        of (configuration, seed) pairs — the reduced picture forbids the
        funnel
    P3  |F(eps)| is non-increasing as eps decreases (narrows)
    P4  |F(eps)| > 0 at eps = 0.025 (persists) — the weakest prediction
    P5  max P(DISORDERED) falls roughly as exp(-c/eps): a straight line in
        ln(max P) vs 1/eps with negative slope over the eps values where
        max P > 0
    P6  configurations with the lowest m(s0) are the last to leave F

## Step 1 — reference + noise (shared across the four repos, identical text)

Reference: `singular_funnel_pitchfork.py` vendored UNCHANGED (sha256 recorded
below). Step 0 result on this machine before any repo work: selftest 4/4 PASS,
STATUS REPRODUCED, mu0=4 eps=0.1 edge log10 x0* = -7.30, slope
d(ln x0*)/d(1/eps) = -1.616. Matches the order's expected values.

Noise script `funnel_noise.py` (stdlib only), Euler-Maruyama, dt = 0.01,
T_max = 600, a = 3, b = 2, eps = 0.1, mu0 = 4.

    model (a)  additive on x, reflecting at x = 0:
               x  <- |x + x(mu - x^2) dt + sigma sqrt(dt) xi|
               mu <- mu + eps(-mu + a x - b) dt
    model (b)  additive on mu, x integrated as y = ln x (deterministic):
               y  <- y + (mu - x^2) dt
               mu <- mu + eps(-mu + a x - b) dt + sigma sqrt(dt) xi

Absorbing exits (declared before any run; differ from the reference's because
the e0 test `x < 1e-8` is not meaningful under x-noise of that size):
    e0  : mu < -0.5 and x < 0.1
    e2  : x > 1.0
    INCONCLUSIVE : neither reached by T_max

Grid:
    starts     mu0 = 4, x0 in {1e-9, 10^-8.5, 1e-8}   (all inside the
               deterministic funnel, whose edge at mu0=4, eps=0.1 is 10^-7.30)
    sigma (a)  10^-11, 10^-10.5, ..., 10^-6      (11 values)
    sigma (b)  10^-4, 10^-3.5, ..., 10^0         (9 values)
    runs       200 per (model, start, sigma); seed = 7919*model_idx
               + 1009*start_idx + 101*sigma_idx + run_idx; random.Random(seed)
    readout    P(e0) with a Wilson 95% interval; sigma_half = the log-
               interpolated sigma at which P(e0) first falls to <= 0.5 of
               P(e0) at the smallest sigma on the grid, per (model, start)

Pre-registered predictions (checked, not tuned):
    P1  at the smallest sigma, P(e0) >= 0.95 for every start (noise
        negligible; reproduces the deterministic funnel)
    P2  P(e0) is non-increasing in sigma up to sampling noise (no rise
        larger than 0.10 between adjacent grid points)
    P3  model (a): sigma_half in [1e-9, 1e-7] (noise competes directly
        with a funnel of width ~5e-8 in x)
    P4  model (b): sigma_half in [1e-2, 1] (noise enters x only through
        the time integral of mu; margin to the edge is ~3.9 nats of ln x)
    P5  sigma_half(b) / sigma_half(a) > 1e4
    P6  within one model, sigma_half across the three starts agrees to
        within a factor of 3 (the width, not the depth, sets survival)

Outcome enum for this step:
    FUNNEL_FOUND         P1 holds and sigma_half lies inside the grid
    NOT_FOUND_IN_RANGE   P(e0) never halves inside the grid (range printed)
    NOT_IN_CLASS         not applicable: this is the paper's own system
    INCONCLUSIVE         > 5% of runs at any grid point used for the
                         decision hit T_max unclassified

vendored reference sha256: 466629a741722183a09221a1594c8f75db7d922ce00eede3afd8e7f01c1f9c46

Scope on every result: stochastic (Metropolis), fixed seeds; parameter
set as above; DISCRETE state space, continuous slow variable. A null is
a result.
