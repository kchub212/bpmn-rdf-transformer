# 0003: Two-level custom exception hierarchy

## Status
Accepted

## Context
`CLAUDE.md` requires "meaningful custom errors instead of raw library errors."
The BPMN parser (Milestone 0) can fail in two structurally different ways:

1. The XML itself is broken, or is missing something the parser needs (e.g.
   invalid XML syntax, a missing `<process>` element, an element without a
   required `id` attribute, or an element type outside the supported MVP
   scope). This is a **parsing** problem: the internal model could not even
   be built.
2. The XML is well-formed and parses without trouble, but the resulting model
   breaks a BPMN rule — for example, a sequence flow's `sourceRef` or
   `targetRef` points at an id that does not exist. This is a **validation**
   problem: the internal model was built, but it is not semantically correct.

An earlier sketch of this milestone considered a deep hierarchy, with a
dedicated exception subclass for every specific failure reason (for example
`MalformedXmlError`, `MissingAttributeError`, `UnsupportedElementError`,
`DanglingReferenceError`, `DuplicateIdError`).

## Decision
Use a shallow, three-class exception hierarchy:

```python
class BpmnError(Exception):
    """Base class for all BPMN-related errors."""

class BpmnParseError(BpmnError):
    """The XML could not be turned into the internal model."""

class BpmnValidationError(BpmnError):
    """The internal model was built, but it breaks a BPMN rule."""
```

No further subclasses are defined. The specific reason for a failure (which
attribute was missing, which id was duplicated, which reference was dangling)
is communicated through the exception's message text, not through additional
exception types. Tests that need to check *which* specific problem occurred
use pytest's `match=` argument to check the message text, for example:

```python
with pytest.raises(BpmnValidationError, match="sourceRef"):
    ...
```

## Reasons
- **The two categories map directly onto the parser's two stages** (see ADR
  0004: parsing, then validation). Knowing whether `BpmnParseError` or
  `BpmnValidationError` was raised tells the caller *which stage* failed,
  which is the distinction that actually matters for deciding what to do
  next — e.g., a future web UI might say "your file is not valid BPMN XML"
  for the first case and "your process has a broken connection" for the
  second.
- **A deep hierarchy adds classes without adding behaviour.** Every one of
  the originally sketched subclasses (`MalformedXmlError`,
  `DanglingReferenceError`, ...) would contain nothing but `pass` — a class
  with no logic of its own, existing only to be a distinct type. For a
  project whose explicit goal is simple, defensible code, that is complexity
  without payoff.
- **Message text is precise enough for this project's size.** A clear error
  message (e.g. `"Sequence flow 'Flow_1' has an unknown sourceRef 'Task_X'"`)
  communicates the same information a dedicated exception class would, and is
  simpler to write, read, and test.
- **A single common base (`BpmnError`) still allows broad handling.** Code
  that does not care about the parse/validate distinction can catch
  everything BPMN-related with one `except BpmnError:`.

## Alternatives considered
- **Deep hierarchy, one subclass per failure reason** (the original sketch).
  Rejected as overengineered for the current project size: each subclass
  would carry no logic, only a name.
- **A single, flat `BpmnError` with no subclasses at all.** Rejected because
  it throws away the one distinction that is genuinely useful — parse-time
  failure vs. validate-time failure — which the parser's own two-stage
  design (ADR 0004) already makes natural to expose.
- **Letting raw `xml.etree.ElementTree` exceptions (e.g. `ET.ParseError`)
  propagate directly**, instead of wrapping them. Rejected — this is
  explicitly disallowed by `CLAUDE.md`, and it would leak an implementation
  detail (the specific XML library used) into code that calls the parser.

## Consequences
- Only three exception classes to define, each a few lines long, with clear
  docstrings.
- Precise test assertions rely on message text (via `match=`) rather than on
  exception type. This creates a small coupling between error message
  wording and test code — a deliberate, accepted trade-off in exchange for
  fewer classes.
- If the project later needs to programmatically *distinguish* failure
  reasons — not just show a message, but actually branch on which failure
  occurred — specific subclasses can be reintroduced at that point, guided by
  a real, concrete need instead of anticipation.

## Future review
Revisit if a future caller (for example, a Flask API endpoint) needs to
distinguish failure reasons in code, not just display an error message to a
user, or if the number of distinct failure reasons grows large enough that
matching on message text in tests becomes fragile or unclear.
