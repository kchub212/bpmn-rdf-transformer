# 0005: BPMN-DI layout assumes acyclic process graphs

## Status
Accepted (as a documented limitation). The recommended fix described below is
**not yet implemented** — this ADR records the discovery and the decision to
leave it unresolved for now, deliberately.

## Context
Block D (`writer/layout.py`) computes an automatic left-to-right layout for
BPMN diagrams by assigning each node a "level" (x-column). The algorithm used
is a topological sort (Kahn's algorithm): a node is only assigned a level
once every one of its predecessors has already been processed, and its level
becomes `1 + the longest path from any start node` — this is what guarantees
no edge ever points backward on the page.

While reviewing this algorithm, it became clear that it silently assumes the
process graph has **no cycles**. If a cycle exists, the node(s) involved
never reach the state Kahn's algorithm requires (all predecessors processed),
so they never get a "real" level from the main algorithm. A defensive
fallback (`if node_id not in level: level[node_id] = 0`) prevents a crash or
infinite loop, but it dumps every unreached node at level 0, arbitrarily —
producing a diagram that may have overlapping or visually nonsensical
positions for the cyclic portion, without any error being raised.

Importantly, **nothing else in the project currently rejects cycles either**.
BPMN loops (e.g. a retry pattern: `Task → ExclusiveGateway → back to Task`)
are completely legitimate, common BPMN constructs, fully expressible with the
current 5 supported element types. Neither the parser nor `validate_process()`
(ADR 0004) checks edge direction or graph structure — they only check id
presence/uniqueness and reference resolution. So a cyclic file would
currently parse and validate without complaint, and only degrade quietly at
the layout step.

## Decision
1. **Document this as a limitation of the layout algorithm specifically**,
   not of BPMN parsing or validation.
2. **Do not reject cyclic processes in `validate_process()`.** Cycles are
   semantically valid BPMN; `validate_process()`'s scope (per ADR 0004) is
   BPMN *rule* violations, not layout *capability* limits. Conflating the two
   would mean rejecting legitimate, ordinary BPMN input just because one
   downstream step (automatic layout) isn't sophisticated enough yet.
3. **Recommended future direction (not yet implemented):** add a targeted
   check inside `compute_layout()` or `write_bpmn()` that detects an
   unresolved cycle and raises a clear, specific error at write time —
   instead of silently falling back to overlapping level-0 placement. This
   keeps the "fail loudly rather than silently produce something subtly
   wrong" pattern this project has followed everywhere else (unsupported
   elements, missing ids, the `name=None` vs. `name=""` handling in the
   writer).

## Reasons
- **Enforcing this in `validate_process()` would be the wrong layer.** That
  function exists to check whether a `Process` breaks a BPMN rule. A cycle
  doesn't break any BPMN rule — it breaks an *assumption our own layout
  algorithm makes*. Those are different kinds of problems, and mixing them
  would make `validate_process()` reject valid input for an implementation
  reason, not a semantic one.
- **Silently leaving the level-0 fallback as "the" behavior would be
  inconsistent with the rest of the project.** Every other place a
  structural problem was found (Blocks A–D), the response was to fail loudly
  with a clear, specific error rather than produce a technically-valid-but-
  wrong result. Leaving this one silent would be the odd one out.
- **A write-time check is the right layer**, because it's specifically the
  *writer's* algorithm (not parsing, not validation) that has this
  assumption — the error belongs where the assumption lives.

## Alternatives considered
- **Enforce cycle-rejection in `validate_process()`.** Rejected — see Reasons
  above; this conflates BPMN-semantic validity with one algorithm's current
  capability.
- **Leave the silent level-0 fallback as permanent, accepted behavior.**
  Rejected — inconsistent with this project's established fail-loud pattern,
  and could produce a confusing, hard-to-debug diagram with no indication of
  why it looks wrong.
- **Implement a cycle-tolerant layout algorithm now** (e.g. proper
  back-edge detection and handling, as used in real Sugiyama-style layered
  graph drawing). Rejected for now — genuine added complexity beyond
  "automatic left-to-right layout" as originally scoped, and there is no
  current fixture or use case that requires it yet.

## Consequences
- As of Block D, the code still silently falls back cyclic nodes to level 0
  — this ADR records the gap without closing it.
- A small, well-scoped follow-up ticket (adding the write-time error check
  described above) is recommended before the application accepts arbitrary
  user-uploaded BPMN files rather than only the project's own curated test
  fixtures — that's the point at which a real-world cyclic diagram becomes
  likely rather than hypothetical.
- This is good, concrete material for the thesis's limitations/future-work
  discussion: a constraint discovered during implementation, with reasoning
  for why it was left as a documented limitation rather than fixed
  immediately.

## Future review
Implement the write-time cycle-detection error before Block J (Flask) starts
accepting arbitrary uploaded files. Revisit the "leave it as a limitation"
decision entirely if a genuinely cycle-tolerant layout algorithm ever
becomes worth the added complexity.
