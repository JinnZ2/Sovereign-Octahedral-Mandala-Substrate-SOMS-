# terrain_prior

Observed indicator → substrate PRIOR, with stated confidence, stated scope, and what would falsify it.
CC0, stdlib only, no network.

```
observation (indicator, free text + context + region + observer_baseline)
        │
        ├── candidates()          alias match; the same object can carry two derivations
        ├── context_satisfied()   flow direction / position selects the branch; absent -> conservative + flagged
        └── derivation entry      MECHANISM MANDATORY (no mechanism -> UNRATED, P5)
                │
      ┌─────────┴──────────┐          morphology profile, supplied per platform
      ▼                    ▼                      │
  BEARING              ENTANGLEMENT  ◄────────────┘
  contact pressure     stem extent vs swing band, then joint exposure,
  vs substrate band    ankle-to-foot ratio, recovery mode
  SUPPORTED |          PASSES | SNAGS | BINDS
  MARGINAL |
  NOT_SUPPORTED
      └──── never collapsed into one score; they can point opposite ways
```

```bash
python experiments/terrain_prior/terrain_prior.py cases      # validation cases A-E
python experiments/terrain_prior/terrain_prior.py selftest
python experiments/terrain_prior/terrain_prior.py entries    # derivations, mechanism first
python experiments/terrain_prior/terrain_prior.py prior obs.json high_pressure_small_contact
```

## Files

```
derivations.jsonl      the store: one derivation per line, mechanism mandatory
morphologies.json      three platform profiles; the same observation returns different ratings per profile
terrain_prior.py       the tool
demo/derivations_no_mechanism.jsonl   validation case D: a correlation with no mechanism, produces no prior
```

## Checks

```
P1_TWO_LAYER       surface and substrate differ; a surface-only reading inverts
P2_SENSOR_INVERT   the standard suite rates this BETTER than it is (cattails, bog mat, deposition zone)
P3_MORPH_SPLIT     bearing direction differs across supplied morphologies; both reported, never merged
P4_OUT_OF_SCOPE    region outside the entry's scope; prior returned WITH the flag
P5_NO_MECHANISM    no mechanism; UNRATED, no prior
NO_DERIVATION      nothing in the store derives this indicator; an absent derivation is not a safe reading
CONTEXT_INCOMPLETE / AMBIGUOUS_DERIVATION   the context that selects the branch is missing
SWING_PROFILE_UNKNOWN                       the profile is not in SWING_BANDS; no entanglement relation computed
```

## Validation cases, as run

```
A  boulder, dry streambed, DOWNSTREAM   P1 P2 P3   bearing LOW; 98 kPa -> NOT_SUPPORTED, 4 kPa -> SUPPORTED
   same object, UPSTREAM                (clean)    bearing HIGH from the scour derivation: context selects
   same object, position UNKNOWN        CONTEXT_INCOMPLETE + AMBIGUOUS: conservative branch, other named
B  pine stand                           P1         bearing references the substrate (100-200 kPa), not the duff (10-30)
C  bog, two profiles                    P1 P2 P3   NOT_SUPPORTED vs SUPPORTED, both returned
D  entry with no mechanism              P5         no prior at all
E  cattails in a foreign region         P4         prior returned, scope mismatch flagged, entanglement BINDS
```

The boulder case is the instrument's validation target: a prior that is correct, derived from process,
opposite to what the sensors say, and available before arrival. `sensor_reads_better_why` on that entry
states why every roughness metric rates the deposition zone better than the scoured side.

## What is estimated and what is derived

The MECHANISMS come from the work order's seed set and are the content of the instrument. The BEARING
BANDS in kPa are the executor's order-of-magnitude engineering estimates: no plate-load or cone record
backs any of them. They exist so a morphology can be compared against something, and they are the first
thing a field baseline should replace. The store's header says so; nothing in the return claims otherwise.

The entanglement score is a declared heuristic, not a measurement: a vegetation term (density, binding,
woodiness) gated so that morphology can only ESCALATE a hazard the stand already presents. Without that
gate an exposed-joint platform read every stand, including soft bog moss, as a snag.

## Hard constraints, as implemented

```
no entry without a mechanism                  P5, asserted over the whole store in the selftest
no single traversability score, ever          the selftest asserts no 'score'/'rating'/'traversability' key in any return
no terrain rating without a morphology        no profile -> NO_MORPHOLOGY, no prior
region is scope, never a key                  out-of-region returns the same mechanism, flagged P4
observer_baseline carried verbatim            copied into the return unchanged
```

## Open (from the work order, unchanged)

The derivation set has to come from someone with a long direct baseline; the seeds here are the work
order's, and every bearing number is an estimate awaiting one. Game trails as a second intake path are
not specced and not built: a trail is this instrument's question already answered over whole-population
multi-year sampling, encoded as route rather than as data.
