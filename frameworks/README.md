# Frameworks — mental-model lenses

A small, curated library of **lenses** the agent applies when synthesizing (via the
`memex-frameworks` skill). A lens is a structured way of interrogating a topic — it produces
assumptions, failure modes, questions, and framings, **not invented facts**.

## The latticework (meta-taxonomy)

Every atomic item is tagged with the strategic problem(s) it serves, via the `latticework:`
frontmatter field:

| Tag | Problem |
| --- | --- |
| `problem-1` | Seeing reality clearly |
| `problem-2` | Deciding under uncertainty |
| `problem-3` | Allocating time and energy |
| `problem-4` | Avoiding self-deception |
| `problem-5` | Playing long games |

## Lenses

- [First principles](first-principles.md) — reduce to fundamentals; rebuild from there.
- [Inversion](inversion.md) — study how it fails; avoid the failure.
- [Second-order effects](second-order-effects.md) — and then what?
- [Base rates](base-rates.md) — what's the reference class?
- [Incentives](incentives.md) — who benefits, and how are they measured?

## Using a lens

1. Pick the lens(es) that fit the topic.
2. Run the lens's core question against the item.
3. Capture what it surfaces as new claims/questions/decisions (with provenance).
4. Tag the item with the lens and the latticework problem(s) it addresses.

Lenses are additive: most non-trivial topics deserve two or three.
