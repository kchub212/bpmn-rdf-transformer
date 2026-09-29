# BPMN-RDF Transformer – Current Project Status

*This file is a snapshot of the repository as it actually exists right now, based on inspecting the current source tree, test suite, `CLAUDE.md`, and `docs/decisions/`. It replaces an earlier snapshot that was taken before Milestone 0 was even implemented and had become badly out of date.*

*Note: CLAUDE.md itself still contains wording from the project's early 'Milestone 0' phase (e.g. 'Do not add Flask, RDFLib, Fuseki, or bpmn-js until BPMN parsing is complete and tested') — that instruction has since been fulfilled by the implemented work. For the current implementation status, this file reflects the actual state of the repository; the remaining working-style and architecture guidance in CLAUDE.md still applies.*

## 1. Project Goal

Per [CLAUDE.md](CLAUDE.md), this is a Bachelor thesis project:

**Web-based bidirectional transformation and visualization of BPMN process models in RDF/OWL knowledge graphs.**

| Part of the goal | Status |
|---|---|
| Upload a BPMN XML file | **Implemented** — Flask `POST /api/processes` |
| Visualize the BPMN diagram | **Implemented** — bpmn-js in the browser |
| Parse BPMN XML into an internal model | **Implemented** — `parser/bpmn_parser.py` |
| Internal Python process model | **Implemented** — `model/process.py` |
| Transform BPMN into RDF/OWL | **Implemented** — `rdf/mapper.py` |
| Validate/improve the RDF graph | **Implemented** — `rdf/validation.py`, `rdf/improvement.py` |
| Store RDF in Fuseki | **Implemented** — `rdf/store.py` |
| Inspect/query the RDF graph | **Partially implemented** — raw SPARQL SELECT via `POST /api/processes/<id>/query`; no dedicated inspection UI yet |
| Transform RDF back into BPMN XML | **Implemented** — `rdf/reader.py` |
| Visualize the generated BPMN again | **Implemented** — same bpmn-js viewer, re-rendered after Apply/upload |

The project has completed **Blocks A through K** of its internal roadmap (BPMN model → parser → writer → BPMN-DI layout → sBPMN vocabulary → RDF mapper → RDF validation/improvement → RDF reader → Fuseki storage → Flask API → web frontend).

## 2. Current Project Structure

```
bpmn-rdf-transformer/
├── CLAUDE.md
├── PROJECT_STATUS.md          (this file)
├── pyproject.toml
├── .gitignore
├── docs/decisions/            (6 ADRs, see Section 10)
├── frontend/                  (npm project, esbuild build step only)
│   ├── package.json / package-lock.json
│   ├── build.mjs
│   └── src/{bpmn-entry.js, turtle-entry.js}
├── src/bpmn_rdf_transformer/
│   ├── exceptions.py                  (7 custom exception classes)
│   ├── model/process.py               (dataclasses)
│   ├── parser/{bpmn_parser.py, validation.py}
│   ├── writer/{bpmn_writer.py, layout.py}
│   ├── rdf/{mapper.py, validation.py, improvement.py, reader.py, store.py}
│   └── api/
│       ├── app.py, errors.py
│       ├── static/{css, js, vendor}   (vendor/ = committed esbuild output + bpmn-js assets)
│       └── templates/index.html
└── tests/
    ├── fixtures/{valid, invalid}/      (9 .bpmn files)
    └── model/, parser/, writer/, rdf/, api/   (92 tests total)
```

## 3. Internal Data Model

`src/bpmn_rdf_transformer/model/process.py` — five frozen dataclasses (`StartEvent`, `EndEvent`, `Task`, `ExclusiveGateway`, `SequenceFlow`, each with `id: str`, `name: str | None = None`; `SequenceFlow` adds `source_ref`/`target_ref`), no shared base class (ADR 0002), plus a mutable `Process` (`id`, `name`, `nodes: dict[str, FlowNode]`, `sequence_flows: list[SequenceFlow]`).

**Supported BPMN elements:** `StartEvent`, `EndEvent`, `Task`, `ExclusiveGateway`, `SequenceFlow`. `ParallelGateway` is **not implemented** — an explicitly optional stretch goal, deferred until the rest of the app is complete.

## 4. BPMN Parser, Validation, Writer

- **`parser/bpmn_parser.py`** — `parse_bpmn_string()`/`parse_bpmn_file()`. Namespace-aware (`xml.etree.ElementTree`), dispatches by tag, raises `BpmnParseError` immediately on any unsupported element ("fail loudly," ADR 0004) or a missing `id`. Duplicate **node** ids are caught in the parser itself (not validation) since `Process.nodes` is a dict that would otherwise silently overwrite (ADR 0004 amendment).
- **`parser/validation.py`** — `validate_process()`: checks `sourceRef`/`targetRef` resolve to real nodes, and no duplicate ids between flows or flow-vs-node. Does **not** check `Process.id` against element ids (handled instead at the RDF layer via UUID-scoped instance URIs, ADR 0006).
- **`writer/bpmn_writer.py`** / **`writer/layout.py`** — `write_bpmn(process)` regenerates BPMN XML plus BPMN-DI, always via automatic left-to-right layout (Kahn's-algorithm-based leveling), never preserving original coordinates (per `CLAUDE.md`). **Known limitation:** cyclic process graphs degrade silently to overlapping level-0 placement rather than erroring — documented, not fixed (ADR 0005).

## 5. RDF: Mapping, Validation, Improvement, Reading

- **Vocabulary:** the external **sBPMN ontology** (`https://sBPMN.github.io/2.0/`), not a project-invented one (ADR 0006). All 5 element types map onto existing sBPMN classes; no local extension needed.
- **`rdf/mapper.py`** — `to_rdf(process) -> Graph`. Instance URIs use a fresh `uuid.uuid4()` per call (`http://bpmn-rdf-transformer.org/instance/{uuid}/...`), with `process/{id}` vs `element/{id}` path segments so a `Process.id` equal to one of its own element ids never collides. `sbpmnp:id` is stored as a plain RDF string literal (see ADR 0006 for the datatype reasoning). `isExecutable` is omitted (the Python model never captures it at all — a pre-existing gap the RDF layer inherits rather than papers over).
- **`rdf/validation.py`** — `validate_rdf(graph)`, four rules, each raising `RdfValidationError` on failure: (1) dangling `sourceRef`/`targetRef`; (2) duplicate `sbpmnp:id` within the *same* process, scoped so `Process.id == element.id` and same-id-across-different-processes both stay valid; (3) missing or invalid (non-exactly-one) `sbpmnp:id`; (4) `sourceRef`/`targetRef` must have exactly one value and must point at an actual flowNode.
- **`rdf/improvement.py`** — `improve_rdf(graph)`, two independent responsibilities: a **warning** (not an error) for any `ExclusiveGateway` with fewer than 2 outgoing flows; and **silent** hand-rolled superclass/hierarchy enrichment (no `owlrl`) filling in sBPMN's class hierarchy (e.g. `task → activity → flowNode → flowElement → baseElement`). Idempotent.
- **`rdf/reader.py`** — `from_rdf(graph) -> Process`, the inverse of the mapper. Calls `validate_rdf()` first, then `validate_process()` on the reconstructed model before returning. Requires exactly one `sbpmnc:process` per graph (explicit, clear error otherwise). Detects concrete leaf types even after `improve_rdf()`'s superclass enrichment.
- **Round-trip fidelity** (BPMN → RDF → BPMN) is covered by dedicated tests for all three valid fixtures, comparing semantically (dict/set equality), not XML-character-for-character, per `CLAUDE.md`.

## 6. Fuseki Storage

`rdf/store.py` — `store_graph`, `get_graph`, `delete_graph`, `run_select_query`, talking to Fuseki directly over HTTP (`requests`), not RDFLib's `SPARQLStore`. One named graph per uploaded process (`graph_id`, caller-supplied, decoupled from the mapper's own instance-URI UUID). `store_graph()` itself enforces "exactly one `sbpmnc:process` per graph" as a storage-layer invariant.

Error handling distinguishes failure kinds: `RdfGraphNotFoundError` (subclass of `RdfStoreError`) for a `graph_id` that doesn't exist, vs. plain `RdfStoreError` for genuine connectivity/server failures. `delete_graph()` is deliberately **idempotent** — deleting an already-absent graph still succeeds, since the goal state ("this graph doesn't exist") already holds.

Verified against a real local Fuseki instance (not just mocks) via a separate integration test file per module, skipped automatically unless `FUSEKI_BASE_URL` is set.

## 7. Flask API

`api/app.py` (routes) + `api/errors.py` (error handlers), a thin layer calling the already-tested pipeline above — no business logic in routes.

| Method & path | Purpose |
|---|---|
| `GET /` | Serves the frontend page |
| `POST /api/processes` | Upload BPMN → parse → to_rdf → validate_rdf → improve_rdf → store, returns `{graph_id, bpmn_xml, warnings}` |
| `GET /api/processes/<id>/bpmn` | get_graph → from_rdf → write_bpmn |
| `GET /api/processes/<id>/rdf` | Raw Turtle |
| `POST /api/processes/<id>/query` | Scoped SPARQL SELECT |
| `PUT /api/processes/<id>/rdf` | Edited Turtle → validate_rdf → improve_rdf → from_rdf (validity gate) → store → write_bpmn |
| `DELETE /api/processes/<id>` | Idempotent delete |

All errors return consistent `{error, type}` JSON: `BpmnParseError`/`BpmnValidationError`/`RdfParseError` → 400, `RdfValidationError` → 422, `RdfGraphNotFoundError` → 404, `RdfStoreError` → 502, anything else → 500 (a `werkzeug.exceptions.HTTPException` handler and a generic `Exception` handler keep this shape uniform everywhere, never leaking a raw traceback).

**Known limitation:** the SPARQL query endpoint has no per-user isolation — `default-graph-uri` scopes the default query graph, but an explicit `GRAPH <uri>` clause could still read another stored process's data. Accepted for a single-user thesis demo; not solved.

## 8. Frontend

Plain HTML/CSS/vanilla JavaScript, served entirely by Flask — **no React/Vue, no Node server at runtime, no `rdf-elements`** (evaluated and rejected: its `RdfEditor` component offers no highlight/scroll-to-range API beyond what raw CodeMirror already gives, while adding an unused dataset/streams dependency chain).

- **BPMN visualization:** `bpmn-js` (`Viewer`), rendering + `element.click` events.
- **RDF editing:** **CodeMirror 6**, directly, plus **`@kurrawongai/codemirror-lang-turtle12`** for Turtle/TriG syntax support.
- **Build step:** `esbuild`, dev-time only, bundling `bpmn-entry.js` and `turtle-entry.js` into static files under `api/static/vendor/`. These built bundles (and the copied bpmn-js CSS/font assets) **are committed to the repository** — a deliberate, intentional exception to `CLAUDE.md`'s general rule "never commit .venv/, generated files, or secrets," made specifically so the app is runnable from a checkout with no Node/npm at runtime, only Flask.
- **Workflow implemented:** Upload → render BPMN + load RDF; click a BPMN element → search the live Turtle text for its `sbpmnp:id` → select/scroll to it in CodeMirror (or show "not found"); **Apply** (PUT edited Turtle, then **re-fetch `GET /rdf`** so the editor reflects the actual stored/enriched state, not just what was submitted — a refresh failure here is reported separately from an Apply failure, since the edit itself already succeeded); **Reset** (re-fetch from server, discarding local edits); **Download** (client-side `Blob` from the last-rendered BPMN XML, no extra request).
- **Frontend state** is deliberately minimal: `{graphId, currentBpmnXml}` only. CodeMirror's own document is the live working Turtle text; Fuseki is the persisted source of truth — nothing is cached redundantly in JS state.
- **Not automated-tested:** frontend JS has no test framework (deliberate choice); verified via manual browser checkpoints instead, mirroring how BPMN-DI visual correctness was verified in Block D.

## 9. Test Status

Command: `.venv/Scripts/python.exe -m pytest tests/ -v`

**Without a running Fuseki:** `85 passed, 7 skipped` (skips are the Fuseki-dependent integration tests, which self-skip via `pytest.mark.skipif` when `FUSEKI_BASE_URL` isn't set).
**With Fuseki running** (`--update --mem /bpmn`): `92 passed, 0 skipped, 0 failed` — last confirmed run, immediately after Block K's closing commits.

Coverage spans: model equality/defaults; parser happy-path + 6 invalid-fixture error cases; BPMN-level validation; writer round-trips + BPMN-DI presence; layout leveling; RDF mapping (7 tests); RDF validation (10 tests, all 4 rules plus edge cases); RDF improvement (7 tests); RDF reader + full BPMN→RDF→BPMN round-trip (3 fixtures); Fuseki store unit tests (mocked) + integration tests (real server); Flask API unit tests (mocked store) + one full-stack integration test; one frontend-route test.

## 10. Architectural Decisions

| ADR | Decision | Followed by code? |
|---|---|---|
| [0001](docs/decisions/0001-src-layout-and-pytest-config.md) | src-layout + pytest `pythonpath` | Yes |
| [0002](docs/decisions/0002-internal-model-as-dataclasses.md) | Flat, independent frozen dataclasses, no shared base class | Yes |
| [0003](docs/decisions/0003-custom-exception-hierarchy.md) | Shallow exception hierarchy, message text carries specificity | Yes, though the hierarchy grew beyond the original 3 classes as new distinct failure modes were found (`RdfParseError`, `RdfValidationError`, `RdfStoreError`, `RdfGraphNotFoundError`) — the *shallow, per-failure-mode* principle was kept, not the exact original class count |
| [0004](docs/decisions/0004-parser-validation-separation.md) | Parser vs. validation split; fail loudly on unsupported elements | Yes |
| [0005](docs/decisions/0005-layout-assumes-acyclic-graph.md) | Document (don't fix) that layout silently mishandles cyclic graphs | Yes — still an open, documented limitation, not yet resolved |
| [0006](docs/decisions/0006-rdf-vocabulary-sbpmn.md) | Adopt sBPMN ontology; UUID-based instance namespace; omit `isExecutable` | Yes |

## 11. Known Limitations

- **Cyclic BPMN graphs** produce a degraded (overlapping) layout rather than a clear error (ADR 0005) — recommended fix (write-time cycle detection) not yet implemented.
- **`isExecutable`** is never read from source BPMN or round-tripped (ADR 0006) — a pre-existing gap, not part of RDF work.
- **Instance URIs are fresh per `to_rdf()` call**, not stable per diagram across separate conversions (ADR 0006) — acceptable for the current upload→convert→edit→convert-back flow.
- **`pytest` is still not declared as a dependency** in `pyproject.toml` — installed manually into `.venv` only.
- **No per-user isolation** on the SPARQL query endpoint (Section 7).
- **Local Fuseki runs with `--mem`** — data is *successfully stored* for the life of the server process, not durably persisted across restarts.
- **`ParallelGateway`** is not implemented (optional stretch goal).
- No SPARQL query UI, RDF graph visualization, BPMN diffing, pySHACL validation, or reverse RDF→BPMN highlighting — all explicitly out of scope through Block K.

## 12. Open / Next Work

- Optional stretch goal: `ParallelGateway` support, only after the rest of the app is considered complete.
- Optional: a dedicated RDF inspection/query UI beyond the current raw SPARQL endpoint.
- The ADR 0005 write-time cycle-detection error remains unimplemented.
- Declaring `pytest` as a real project dependency.

## 13. How to Run

```
.venv/Scripts/python.exe -m pip install -e .        # or install deps per pyproject.toml manually
.venv/Scripts/python.exe -m pytest tests/            # 85 passed, 7 skipped without Fuseki

# Optional, for the full suite and the real app:
# start Fuseki: fuseki-server.bat --update --mem /bpmn
# then, from repo root:
.venv/Scripts/python.exe -c "from bpmn_rdf_transformer.api.app import create_app; create_app().run()"
```
Rebuilding the frontend bundles (only needed after changing frontend dependencies):
```
cd frontend && npm install && npm run build
```

## Project Snapshot

- **Latest commits:** `804136b` (Add BPMN and RDF web frontend), `b6cfa23` (Fix duplicate RDF ID error message), `e35dc01` (Handle missing RDF graphs consistently), on top of `50dad52`/`e26d73a`
- **Blocks completed:** A–K
- **Test result:** 85 passed / 7 skipped (no Fuseki) — 92 passed / 0 skipped / 0 failed (with Fuseki)
- **Number of ADRs:** 6
- **Recommended next step:** your call — optional `ParallelGateway` stretch, the ADR 0005 cycle-detection fix, or moving on to thesis writing
