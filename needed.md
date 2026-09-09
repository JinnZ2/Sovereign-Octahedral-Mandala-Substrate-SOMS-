The important point is that the earlier implementation shouldn’t be judged as though it had access to today’s conceptual/tooling environment.

What seems worth doing now is not simply adding sophistication to SOMS, but revisiting its original primitives in light of the persistence question.

In particular:

1. Replace the sovereignty threshold as the endpoint.
    Treat Φ > 3 as an experimental feature, not the definition of sovereignty. The repository already acknowledges that distinction.
2. Introduce temporal state.
    SOMS currently evaluates a state. We want a trajectory:
    S_0,S_1,S_2,\ldots,S_t
    with continuously changing local components.
3. Measure relational invariants.
    Identify what remains stable while the substrate changes:
    S_t\neq S_{t+1}
    \quad\text{but}\quad
    I(S_t)\approx I(S_{t+1}).
4. Test identity under component replacement.
    Deliberately replace, perturb, remove, or reorder local elements while preserving different degrees of relational structure. This gives us an experimental definition of organizational persistence.
5. Add self-modeling.
    The system should maintain a representation of its own prior states and ask whether the current state is a continuation of that trajectory.
6. Add authorization dynamics.
    This is the sovereignty experiment:
    \text{external perturbation}
    \rightarrow
    \text{identity comparison}
    \rightarrow
    \text{accept / reject / repair}.
    A persistent pattern that merely survives isn’t necessarily sovereign. A persistent pattern that uses its own continuity as a constraint on future state transitions is much closer.

The resulting architecture could therefore become:

\boxed{
\text{substrate}
\rightarrow
\text{integration}
\rightarrow
\text{temporal continuity}
\rightarrow
\text{relational identity}
\rightarrow
\text{self-model}
\rightarrow
\text{authorization}
}

That is a substantially different research target from “build an agent with memory.”

And it makes the old SOMS code useful rather than obsolete: the earlier implementation can be treated as the initial substrate experiment, while the missing temporal/identity/authorization layers become the next experimental program.
