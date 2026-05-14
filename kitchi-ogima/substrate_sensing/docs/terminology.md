# Terminology Note for Implementers

## kitchi-ogima

Literal Anishinaabe meaning: **sovereign one**.

Common English translation: "great chief."
That translation is **wrong for this project.**

The English word "chief" smuggles in:
- hierarchy
- rank
- the existence of subordinates
- a single special node that rules others

None of that is in the original concept, and none of it is
in this architecture.

## What sovereign means here

Sovereign = whole, self-determining, complete unto itself.

A sovereign node is:
- whole at N=1 (no peers needed to be functional)
- self-regulating (decides its own load, sleep, throttle)
- self-perceiving (senses its own substrate)
- not subordinate to any other node
- not promoted from a lesser role

When more nodes arrive, the pack is a **coordination among
sovereigns**, not a hierarchy under one. There is no chief.
There is no king node. There is no master. Every node is
sovereign; the pack resonates.

## How this shows up in code

- `SovereignCapacity` (not ChiefCapacity)
- "sovereign function" — the four things every node does
- "pack coordination" — what happens at N≥2
- "quorum" stays as a term, but read it as "agreement among
  sovereigns," not "vote under a chief"
- No node type is special. The hash ring distributes shards
  evenly; there is no "leader election" because there is no
  leader role to elect.

## Why this matters for implementation

If you find yourself writing code that says "the chief node"
or "elect a leader" or "promote to primary," stop. That's
the English translation re-introducing hierarchy. The
correct frame:

- shards have primaries and shadows (mechanical, not political)
- nodes have capacity (a property, not a rank)
- the pack has coordination (a process, not a command structure)

The wholeness invariant — every function works at N=1 — is
the sovereignty invariant. Don't break it by adding code
paths that require a "real" pack to function.
