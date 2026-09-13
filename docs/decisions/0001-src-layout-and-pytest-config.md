# 0001: Use a src-layout Python package with pytest pythonpath configuration

## Status
Accepted

## Context
This is a Bachelor thesis project that will grow over several milestones: a BPMN
parser, an RDF/OWL transformer, later a Flask web backend, and a bpmn-js frontend
integration. The repository structure chosen at the very start needs to support
this growth without becoming confusing, and needs to keep test code cleanly
separated from library code.

There are two common ways to lay out a Python package:

- **Flat layout**: the package folder sits directly in the repository root,
  e.g. `bpmn_rdf_transformer/` next to `tests/`.
- **src layout**: the package folder is nested one level deeper, inside a
  `src/` directory, e.g. `src/bpmn_rdf_transformer/`.

## Decision
Use the src-layout: `src/bpmn_rdf_transformer/`.

Configure pytest through `pyproject.toml`'s `[tool.pytest.ini_options]` table,
using `pythonpath = ["src"]`. This tells pytest to add `src/` to Python's import
path when running tests, so test files can simply write
`from bpmn_rdf_transformer... import ...` without any extra installation step.

## Reasons
- **Avoids accidental imports.** In a flat layout, if pytest (or Python) is run
  from the repository root, it is easy for Python's import system to
  accidentally pick up files from the current working directory instead of the
  intended package — especially once test files and package files start using
  similar names. The src-layout prevents this structurally: the package is
  simply not on the default import path unless something (here, the pytest
  config) explicitly adds it.
- **Matches common Python packaging practice.** This will matter once the
  project becomes a real installable package, for example when the Flask
  backend needs to import `bpmn_rdf_transformer` as a normal dependency.
- **No extra install step for now.** The `pythonpath` pytest option lets tests
  run right after `pip install pytest`, without needing `pip install -e .`.
  This keeps the very first "clone and run tests" experience simple.

## Alternatives considered
- **Flat layout without `src/`.** Simpler at first glance — one less folder
  level — but more fragile: import-path bugs caused by flat layouts are a
  well-known and hard-to-explain Python pitfall. Rejected because the small
  cost of one extra folder avoids a class of bugs that would be awkward to
  debug and to justify in a thesis defense.
- **Editable install (`pip install -e .`) instead of the `pythonpath` config.**
  This is the more "standard" long-term packaging approach, but it adds an
  install step every time the environment is recreated (e.g. a fresh clone, a
  new venv, a CI runner). Deferred until a later milestone actually needs the
  package to run outside of pytest, such as a Flask app importing it directly.

## Consequences
- Every new module lives under `src/bpmn_rdf_transformer/...`.
- Tests are run with `pytest` (or `python -m pytest`) from the repository
  root; pytest automatically reads `pyproject.toml` for its configuration.
- No `pip install` of the project itself is needed yet — only `pytest` as a
  development dependency.

## Future review
Revisit this decision when Flask (or any other component that runs outside of
pytest) is introduced. At that point, switching to an editable install
(`pip install -e .`) may become worthwhile, since the package will need to be
importable both by pytest and by a running server process.
