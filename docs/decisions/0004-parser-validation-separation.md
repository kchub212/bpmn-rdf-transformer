# 0004: Separate parsing from validation, and fail loudly on unsupported elements

## Status
Accepted

## Context
`CLAUDE.md`'s architecture direction places a "BPMN parser" between BPMN XML
and the internal Process Model, and separately requires validating
`sourceRef`/`targetRef` in sequence flows. This raised two design questions:

1. Should turning XML into objects, and checking that those objects follow
   BPMN's rules, be one combined step, or two separate steps?
2. Milestone 0's scope (MVP) intentionally supports only five things: Process,
   Start Event, End Event, Task, and Sequence Flow. What should happen when
   the parser encounters a BPMN element type it does not support yet — for
   example a gateway — inside a `<process>` element?

## Decision
**1. Split parsing and validation into two separate functions**, in two
separate modules:

- `parser/bpmn_parser.py` turns BPMN XML into a `Process` object. Its only
  job is structural: read the XML tree, find the supported elements, build
  the matching dataclass instances (ADR 0002). It does not check whether the
  resulting model makes semantic sense.
- `parser/validation.py` provides `validate_process(process: Process) -> None`,
  which checks an already-built `Process` object for BPMN rule violations
  (currently: dangling `sourceRef`/`targetRef`, duplicate ids). It never
  touches XML.

`parse_bpmn_file()` and `parse_bpmn_string()` (the two public entry points)
call parsing and then validation in sequence, so the common case — "give me a
correct model, or a clear error" — is still a single function call for
whoever uses the parser.

**2. Fail loudly on unsupported elements.** Any element found directly inside
`<process>` that is not one of the five supported types causes the parser to
raise `BpmnParseError` immediately, instead of silently skipping it. Elements
outside `<process>` — in particular `<bpmndi:BPMNDiagram>`, which bpmn.io
always exports for diagram layout — are simply never visited by the parser,
so they never trigger this error; they are not "unsupported," they are
outside the parser's area of interest.

## Reasons

### Why separate parsing from validation
- These are genuinely different concerns: "is this XML shaped like BPMN" is a
  structural question, "does this BPMN model make sense" is a semantic
  question. Keeping them in separate functions means each can be understood,
  tested, and explained on its own.
- Validation logic can be tested by building a `Process` object directly in
  Python and calling `validate_process()` on it — no XML fixture file needed
  for every rule under test. This keeps validation tests short and focused on
  the rule being tested, not on XML syntax.
- This matches the layered architecture `CLAUDE.md` already describes
  (XML → parser → internal model → ...): validation is a check *on* the
  internal model, not a detail of parsing XML.

### Why fail loudly on unsupported elements
- Milestone 0's scope is explicitly limited to five element types. If the
  parser silently ignored an element it does not understand (e.g. a
  gateway), it would return a `Process` object that *looks* complete and
  valid, but is quietly missing part of the original diagram. That silent
  data loss would likely only be discovered much later — for example once
  RDF round-tripping is implemented, as a confusing mismatch between what was
  uploaded and what comes back out. Raising an error immediately turns a
  hard-to-diagnose future bug into an obvious, immediate one, right where the
  information is lost.
- This directly follows `CLAUDE.md`'s instruction to use meaningful custom
  errors rather than silently doing something other than what the input
  asked for.

## Alternatives considered
- **One combined `parse_and_validate()` function.** Rejected because it would
  force every validation-rule test to also go through XML parsing, and would
  mix two concerns — "is the XML well-formed" and "is the resulting model
  correct" — inside one function body.
- **Silently skipping unsupported elements.** This was the "easier" option in
  the sense that it would let more real-world BPMN files parse without
  error. Rejected because of the silent-data-loss risk described above,
  which conflicts with this project's core goal of faithful BPMN ↔ RDF
  round-tripping.
- **Silently skipping unsupported elements, but logging a warning.**
  Considered as a middle ground, but rejected for Milestone 0: it still
  produces an apparently "successful" result for an incomplete parse, and the
  project has no logging infrastructure yet — adding one just to support this
  would be a bigger change than the problem deserves.

## Consequences
- Two small modules (`bpmn_parser.py`, `validation.py`) instead of one, each
  with a narrow, single job.
- Any BPMN file that uses an element type outside the MVP scope (gateways,
  subprocesses, boundary events, etc.) will currently fail to parse entirely,
  rather than parsing the supported parts and dropping the rest. This is a
  known, intentional limitation of Milestone 0 — not a bug — and will be
  relaxed as later milestones add support for more element types.
- `parse_bpmn_file()` / `parse_bpmn_string()` remain the only two functions
  most callers (including most tests) need to know about. The parsing/
  validation split is visible mainly to whoever wants to test validation
  rules directly, without going through XML.

## Future review
Revisit the "fail loudly" behaviour once more BPMN element types are
supported. At that point, decide per element type whether it should still be
"known and currently unsupported" (should keep erroring) or "safe to ignore"
(for example, a purely visual or documentation-only element, if one is ever
found to exist in real BPMN files).

## Amendment: duplicate node ids must be caught during parsing, not validation

While implementing `validate_process()` (Part 7), it turned out that this
ADR's original plan for duplicate-id detection does not work for one specific
case: two *nodes* (e.g. a `task` and an `endEvent`) sharing the same `id`.

**Why:** `Process.nodes` is a `dict[str, FlowNode]`, keyed by each node's own
`id` (ADR 0002). The parser (`bpmn_parser.py`) builds it with
`process.nodes[node.id] = node`. If two nodes in the source XML share an
`id`, the second one silently **overwrites** the first in the dictionary —
this is just how Python dicts behave; there is no error, and no trace of the
first node is left behind. By the time parsing finishes and
`validate_process()` would run on the resulting `Process`, the collision has
already been destroyed: the object looks like a perfectly normal `Process`
with one fewer node than the source file actually had.

This does **not** affect duplicates involving a `SequenceFlow` id — flows are
collected into `Process.sequence_flows`, a plain `list`, which never
overwrites anything. A duplicate between two flow ids, or between a flow id
and a node id, is still fully visible after parsing and can still be checked
by `validate_process()`.

**Revised decision:** duplicate-**node**-id detection moves into the parser
itself (`bpmn_parser.py`), raising `BpmnParseError` at the exact point where
a second node would otherwise overwrite an existing one — immediately before
`process.nodes[node.id] = node`. `validate_process()` (`validation.py`)
keeps responsibility for everything that *is* still visible after parsing:
dangling `source_ref`/`target_ref`, a flow id duplicating another flow id,
and a flow id duplicating a node id.

**Why this option over changing `Process.nodes` to a list:** the alternative
— storing nodes in a list instead of a dict, so nothing is ever silently
lost — would keep all duplicate-id logic in one place (`validate_process()`,
matching the original plan exactly), but it would change the `Process` model
agreed and tested in ADR 0002/Part 4, and every id-based node lookup the
parser and any future code performs. Catching the problem at the one place
it actually occurs (the dict write in the parser) is a smaller, more
targeted fix for a problem that is specific to that one data structure.

**Consequence:** duplicate-node-id is now a `BpmnParseError` (structural),
not a `BpmnValidationError` (semantic) — a small inconsistency with this
ADR's original "parse vs. validate" split, but justified because the model's
own storage mechanism (not the XML, not a genuine ambiguity in the data)
is what makes the information unrecoverable if not caught immediately.
