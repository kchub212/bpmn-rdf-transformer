# BPMN RDF Transformer — Project Instructions

## Project purpose
This is a Bachelor thesis project about:

**Web-based bidirectional transformation and visualization of BPMN process models in RDF/OWL knowledge graphs.**

The final system should allow a user to:
1. Upload a BPMN XML file.
2. Visualize the BPMN diagram.
3. Transform BPMN into RDF/OWL.
4. Inspect and query the RDF graph.
5. Transform RDF/OWL back into BPMN XML.
6. Visualize the generated BPMN again.

## Working style
- Work in small milestones.
- Do not create a huge project dump.
- Before editing several files or adding a new component, first explain the plan and wait for approval.
- Prefer simple, readable, maintainable code.
- Explain important decisions and code in simple language.
- Identify risks, validation needs, and edge cases before implementation.
- Do not introduce unnecessary frameworks or dependencies.

## Planned stack
- Python
- Flask later for the web backend
- xml.etree.ElementTree for BPMN XML parsing
- RDFLib for RDF/OWL generation and reading
- Apache Jena Fuseki later for triple storage and SPARQL
- bpmn-js later for BPMN visualization
- pytest for tests
- Git for version control

## Architecture direction
Use an internal domain model between BPMN XML and RDF/OWL:

BPMN XML
→ BPMN parser
→ Internal Process Model
→ RDF transformer
→ RDF graph / Fuseki

RDF graph
→ RDF reader
→ Internal Process Model
→ BPMN XML writer
→ BPMN-DI layout generation
→ bpmn-js visualization

Do not spread direct BPMN-to-RDF logic across the project.

## MVP scope
Initially support only:
- Process
- Start Event
- End Event
- Task
- Sequence Flow

Do not add Flask, RDFLib, Fuseki, or bpmn-js until BPMN parsing is complete and tested.

## Technical rules
- Handle BPMN XML namespaces correctly.
- Preserve BPMN element IDs in BPMN → RDF → BPMN.
- Validate sourceRef and targetRef in sequence flows.
- Compare BPMN models semantically, not XML character by character.
- Generated BPMN must later contain enough BPMN-DI data to render in bpmn-js.
- Start with automatic left-to-right layout instead of preserving original coordinates.
- Use meaningful custom errors instead of raw library errors.

## Code conventions
- Use Python dataclasses where suitable.
- Use type hints.
- Keep functions small and focused.
- Write pytest tests for every parser, validation, mapping, and round-trip feature.
- Store BPMN test files in tests/fixtures/.
- Use clear names.

## Git and documentation
- Use small atomic commits with feat:, fix:, test:, docs:, refactor:.
- Store important architecture decisions in docs/decisions/.
- Never commit .venv/, generated files, or secrets.

## Current milestone
Milestone 0: Parse-only walking skeleton.

The goal is:
- Define the internal Python Process Model.
- Parse BPMN XML exported from bpmn.io.
- Support start events, end events, tasks, and sequence flows.
- Add validation, custom exceptions, fixtures, and pytest tests.

Do not write implementation code before proposing a plan.
## Code simplicity and learning requirements

- Write code at the level of a Bachelor student, not like a large enterprise system.
- Prefer the simplest correct solution.
- Keep files, classes, and functions short.
- Avoid unnecessary abstraction, design patterns, helper layers, and advanced Python features.
- Do not create functions only to make the architecture look more professional.
- Use clear names and straightforward logic.
- Add comments only when they explain something that is not obvious.
- Every line of code should have a clear purpose.
- Before adding complexity, explain why it is necessary and ask for approval.
- After each implementation step, explain the code precisely and in simple language.
- Explain each class, function, parameter, return value, and important line.
- Show a small practical example of how the code works.
- Do not continue to the next step until I confirm that I understand the current code.