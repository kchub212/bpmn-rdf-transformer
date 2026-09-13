# 0002: Internal BPMN process model as plain Python dataclasses

## Status
Accepted

## Context
Per `CLAUDE.md`, the project needs an internal domain model that sits between
BPMN XML and RDF/OWL, so that BPMN-to-RDF conversion logic is not scattered
across the codebase:

```
BPMN XML → BPMN parser → Internal Process Model → RDF transformer → RDF graph
```

Milestone 0 needs to represent five kinds of things: a Process, Start Events,
End Events, Tasks, and Sequence Flows. Two design questions had to be answered:

1. How should each element type be represented in Python?
2. Should the element types (`StartEvent`, `EndEvent`, `Task`, `SequenceFlow`)
   share a common base class, since they all have an `id` and an optional
   `name`?

## Decision
Represent every BPMN element type as an independent, flat `@dataclass`, with
**no shared base class** between them:

```python
@dataclass(frozen=True)
class StartEvent:
    id: str
    name: str | None = None

@dataclass(frozen=True)
class EndEvent:
    id: str
    name: str | None = None

@dataclass(frozen=True)
class Task:
    id: str
    name: str | None = None

@dataclass(frozen=True)
class SequenceFlow:
    id: str
    source_ref: str
    target_ref: str
    name: str | None = None

FlowNode = StartEvent | EndEvent | Task  # type hint only, not a real class

@dataclass
class Process:
    id: str
    name: str | None = None
    nodes: dict[str, FlowNode] = field(default_factory=dict)
    sequence_flows: list[SequenceFlow] = field(default_factory=list)
```

`StartEvent`, `EndEvent`, `Task`, and `SequenceFlow` are **frozen** (immutable).
`Process` is a regular, mutable dataclass.

## Reasons
- **Dataclasses give useful behaviour for free.** `@dataclass` automatically
  generates `__init__`, `__eq__`, and `__repr__`. `__eq__` in particular means
  two parsed models can be compared for equality directly with `==`, which is
  exactly what `CLAUDE.md` asks for ("compare BPMN models semantically, not
  XML character by character") — without writing any comparison code by hand.
- **`frozen=True` matches how these objects are actually used.** A BPMN
  element is fully known the moment it is parsed from one XML tag; nothing in
  Milestone 0 needs to change an element afterwards. Making the leaf classes
  immutable prevents accidental changes later, and makes equality comparisons
  trustworthy (two elements with the same field values are simply equal).
- **No shared base class.** A base class such as
  `BpmnElement(id, name)` was considered, to avoid repeating the `id`/`name`
  fields four times. It was rejected because `SequenceFlow` needs two extra
  *required* fields (`source_ref`, `target_ref`), and Python's dataclass rule
  that "a field without a default cannot follow a field with a default" would
  force either an awkward field ordering, a fake default value (e.g.
  `source_ref: str = ""`), or `field(kw_only=True)` just to make the
  inheritance work. Any of these is a workaround for the *language*, not a
  reflection of the *problem*, and would be difficult to explain line-by-line
  in a thesis defense. Four small, fully self-contained classes are simpler to
  read, and every field of every class is visible in one place.
- **`Process` is not frozen**, because it is built up incrementally while the
  parser walks the XML tree — nodes and flows are added one at a time as
  parsing proceeds. It only becomes conceptually "finished" after parsing and
  validation both succeed.

## Alternatives considered
- **Shared base class `BpmnElement(id, name)`.** Rejected for the reason
  above: it forces `SequenceFlow` into an awkward dataclass field-ordering
  workaround, in exchange for removing two lines of duplication per class.
- **Plain dictionaries** (e.g. `{"type": "task", "id": "...", "name": "..."}`)
  instead of dataclasses. Rejected because it gives up type checking, IDE
  autocomplete, and free `__eq__`/`__repr__`; `CLAUDE.md` explicitly asks for
  dataclasses and type hints.
- **Abstract base class (`abc.ABC`) with abstract methods.** Rejected as
  unnecessary: Milestone 0's element types share *shape* (some common fields),
  not *behaviour* (no methods yet), so there is nothing for an abstract method
  to usefully declare.
- **Fully mutable dataclasses (no `frozen=True`).** Rejected because
  immutability better matches how these objects are used (built once from
  XML, never edited afterwards) and avoids a class of bugs where one part of
  the code accidentally mutates an element that another part still holds a
  reference to.

## Consequences
- Each dataclass is small, self-contained, and can be understood without
  looking at a parent class.
- There is some repetition: `id: str` and `name: str | None = None` appear in
  four separate classes instead of once. This is accepted as low-cost,
  low-risk duplication, rather than something to eliminate prematurely.
- If a future milestone adds an element type that shares real *behaviour*
  with existing types (for example, gateways all needing a method to check
  "does this have more than one outgoing flow"), a base class or a small
  shared helper function can be introduced then — driven by an actual,
  concrete need instead of anticipation.

## Future review
Revisit this decision if more BPMN element types are added (gateways,
intermediate events, subprocesses, ...) and the field duplication grows large
enough to be a real maintenance cost, or if element types start needing
shared behaviour rather than just shared shape.
