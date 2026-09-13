# 0006: RDF vocabulary — adopt the sBPMN ontology

## Status
Accepted

## Context
The project's core purpose (`CLAUDE.md`) requires transforming the internal
BPMN process model into RDF/OWL. Before any mapping code could be written
(Block F), the RDF vocabulary itself needed to be settled — an initial
proposal sketched a brand-new, project-invented ontology namespace from
scratch.

That proposal was corrected: this thesis had already selected the **sBPMN
ontology** (<https://sbpmn.github.io/2.0/index.html>) as its literature
reference, and the project should reuse its existing terms rather than
invent parallel ones, unless a clearly justified gap exists.

The actual ontology file (`ontology.ttl`) was downloaded and inspected
directly — not summarized secondhand — after an initial AI-assisted summary
of the page gave two inconsistent answers about `sequenceFlow`'s parent
class in a row (once claiming a nonexistent `connector` class). All facts
below were verified against the raw Turtle source with direct text search
(`grep`), not trusted from a lossy summary.

## Decision

### Vocabulary — verified class hierarchy (namespace `https://sBPMN.github.io/2.0/classes#`, prefix `sbpmnc:`)
```
baseElement
├── rootElement → callableElement → process
└── flowElement
    ├── flowNode
    │   ├── activity → task
    │   ├── event → catchEvent → startEvent
    │   ├── event → throwEvent → endEvent
    │   └── gateway → exclusiveGateway
    └── sequenceFlow
```

### Vocabulary — properties used (namespace `https://sBPMN.github.io/2.0/properties#`, prefix `sbpmnp:`)
| Property | Type | Use |
|---|---|---|
| `id` | DatatypeProperty, range `xsd:ID` | element id (domain `baseElement`, inherited by all 6 classes above) |
| `name` | DatatypeProperty, range `xsd:string` | element name (domain includes `flowElement`/`callableElement`, inherited by all 6) |
| `flowElement` | ObjectProperty, domain `process` (+3), range `flowElement` | **process containment — covers both nodes and flows in one property**, since `sequenceFlow` is itself a `flowElement` subclass |
| `sourceRef` / `targetRef` | ObjectProperty, domain includes `sequenceFlow` | connects a `sequenceFlow` to its source/target node resource |

### Model → vocabulary mapping
| Python | sBPMN class |
|---|---|
| `Process` | `sbpmnc:process` |
| `StartEvent` | `sbpmnc:startEvent` |
| `EndEvent` | `sbpmnc:endEvent` |
| `Task` | `sbpmnc:task` |
| `ExclusiveGateway` | `sbpmnc:exclusiveGateway` |
| `SequenceFlow` | `sbpmnc:sequenceFlow` |

**No local ontology extension is needed for the current 5-element scope.**
Every field on every one of the 6 dataclasses maps onto an existing sBPMN
term (`id`, `name`, `flowElement`, `sourceRef`, `targetRef`).

**Intentionally out of scope** (real sBPMN classes deliberately not used, per
`CLAUDE.md`'s "not the full BPMN 2.0 spec" rule): `laneSet`/`lane`,
`messageFlow`/`collaboration`/`participant`, `dataObject`/`dataAssociation`,
`boundaryEvent`/intermediate events, `inclusiveGateway`/`complexGateway`/
`eventBasedGateway`, `resource`/`resourceRole`. Note: `sbpmnc:parallelGateway`
already exists in the ontology — if the `ParallelGateway` stretch goal is
ever pursued, the vocabulary term is already available, no extension needed
then either.

### Instance identity (a separate concern from the ontology namespace)
- **Schema namespace**: sBPMN's own (`sbpmnc:`/`sbpmnp:` above) — not owned
  by this project, only referenced.
- **Instance namespace**: `http://bpmn-rdf-transformer.org/instance/{uuid}/`,
  prefix `proc:`. A fresh `uuid.uuid4()` is minted **inside `to_rdf()` on
  every call** — not derived from the BPMN `process_id`, and not a new
  parameter or model field.
- **Why a UUID instead of the BPMN process id**: BPMN process/element ids are
  only unique *within one file*. Two independently uploaded diagrams could
  both contain `Process_1`/`Task_1`; using those ids directly in the
  instance-URI path would cause silent collisions once multiple diagrams
  share one RDF store. A per-conversion UUID makes collision structurally
  impossible.
- **Round-trip fidelity is unaffected**: the original BPMN id is preserved
  exactly via the `sbpmnp:id` literal, asserted independently of the URI.
  The RDF → BPMN reader (Block H) reads `sbpmnp:id` directly and never
  parses or derives anything from a resource's URI.
- **`sourceRef`/`targetRef` must point at the actual node resource** (not a
  bare id string) — this isn't a choice left open to this project: sBPMN
  declares both as `owl:ObjectProperty`, which in OWL can only ever relate
  two resources, never hold a literal value.

### `isExecutable`
**Omitted from the RDF mapping for now.** The Python `Process` model does
not currently read or store this attribute at all — the parser never reads
it from source XML, and the writer unconditionally hardcodes
`isExecutable="false"` regardless of the original file's actual value. This
gap pre-dates the RDF work (it exists already in the shipped Block A–D
parser/writer); the RDF layer simply inherits it rather than papering over
it. Asserting `sbpmnp:isExecutable false` unconditionally into the RDF graph
was considered and rejected, since it could assert something factually
wrong if a source file actually had `isExecutable="true"`.

## Reasons
- **Reusing sBPMN, not inventing a parallel vocabulary**, directly serves
  the thesis: it connects the implementation to the literature already
  being cited, rather than creating unexplained divergence a defense would
  have to justify.
- **A single `sbpmnp:flowElement` property covering both nodes and flows**
  mirrors the parser's own design exactly (`bpmn_parser.py` already walks
  `<process>`'s children in one loop, dispatching by tag, treating nodes and
  flows uniformly at the top level) — the RDF mapping doesn't need to invent
  a structural distinction the rest of the codebase doesn't have either.
- **The UUID-based instance namespace is simpler than the originally
  proposed id-encoded-in-URI scheme**, not just safer: it removes the need
  for the RDF reader (Block H) to ever parse an id out of a URI — it just
  reads the `sbpmnp:id` literal, full stop.
- **`sourceRef`/`targetRef` as object properties was settled by the ontology
  itself**, not chosen freely — `owl:ObjectProperty` cannot hold a literal
  value in OWL, so once sBPMN was adopted, this was no longer an open design
  question.

## Alternatives considered
- **A brand-new, project-invented ontology namespace.** Rejected — this was
  the original (incorrect) proposal; superseded once it was established the
  thesis already committed to sBPMN as its literature/framework reference.
  Reinventing already-existing terms would have been redundant work and
  weaker to defend.
- **Encoding the BPMN `process_id` into the instance URI path**
  (`.../process/{process_id}/{element_id}`). Rejected — real collision risk
  across independently uploaded diagrams, since BPMN ids aren't globally
  unique; superseded by the per-conversion UUID scheme.
- **Keeping `sourceRef`/`targetRef` as plain id-string literals**, mirroring
  the Python model's `source_ref: str` field exactly. Not actually available
  as a real alternative once sBPMN was adopted — foreclosed by the
  ontology's own `owl:ObjectProperty` declaration.
- **Always writing `sbpmnp:isExecutable false`.** Rejected — risks asserting
  incorrect data into the graph for any source file where the original value
  was actually `true`.

## Consequences
- Block F (the mapper) has a fully settled target vocabulary and URI
  strategy to implement against — no remaining open design questions.
- Block H (the reader) needs no URI-parsing logic at all, only needs to read
  `sbpmnp:id` literals — simpler than originally planned.
- The `isExecutable` fidelity gap remains open as a separate, optional,
  small future ticket touching the Python model/parser/writer — not RDF
  code, and not addressed by this decision.
- Generating a fresh UUID per `to_rdf()` call means the same diagram
  converted twice produces two different URI sets. Acceptable for every
  currently planned use (upload → convert → validate → convert back, within
  one flow); flagged for revisiting if a later block (Fuseki storage,
  re-opening a previously converted diagram) needs the same diagram to
  produce stable, identical URIs across multiple separate operations over
  time.

## Future review
Revisit `isExecutable` if full round-trip fidelity for that specific
attribute becomes worth the small model/parser/writer change it requires.
Revisit instance-URI stability (fresh-per-call vs. stable-per-diagram) once
Fuseki storage (Block I) or any diagram re-editing workflow is designed, if
either needs a diagram's identity to persist across multiple independent
conversions.
