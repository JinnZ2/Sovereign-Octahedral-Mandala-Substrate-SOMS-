# kitchi-ogima

A distributed sovereignty layer for salvaged hardware.

`kitchi-ogima` is Anishinaabe for **sovereign one** — whole,
self-determining, complete unto itself. The common English
translation ("great chief") is misleading: this is not a
hierarchy, there is no leader node, and no node is special.

Every node in a kitchi-ogima pack is sovereign. A pack of one
is whole. A pack of many is a coordination *among* sovereigns,
not a structure *under* one.

## What this is

- A way to give salvaged binary hardware multi-sense awareness
  by reading the side channels (heat, EM, power, timing,
  magnetic, acoustic) that standard architecture treats as noise.
- A sharded coordination layer that grows as more hardware
  joins, without ever having an "incomplete" state.
- A test-encoded invariant: every function works at N=1 using
  the same code path it uses at N=100.

## What this is not

- A leader-elected distributed system
- A master/worker architecture
- A product or service
- A static design that requires a minimum hardware footprint

## Core invariant

Wholeness at every N. If you find yourself writing a code path
that only activates when N≥2, you have broken the sovereignty
invariant. Refactor until the same function handles N=1 and
N=many naturally.

## Calibration

**Why the framework exposes its own breaking points:** the
constraint stack is structured to fail visibly under specific
conditions rather than mask invalid outputs. The breaking
points are the calibration signal. See
[CALIBRATION_AS_PERFECTION.md](https://github.com/JinnZ2/JinnZ2/blob/main/CALIBRATION_AS_PERFECTION.md)
for the underlying framing.

## License

CC0. Knowledge outside the extraction ledger.
