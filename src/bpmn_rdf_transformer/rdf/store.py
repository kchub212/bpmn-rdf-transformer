import os

import requests
from rdflib import RDF, Graph

from bpmn_rdf_transformer.exceptions import RdfGraphNotFoundError, RdfStoreError
from bpmn_rdf_transformer.rdf.mapper import SBPMNC

# SBPMNC/SBPMNP are defined in rdf/mapper.py, even though validation.py,
# improvement.py, reader.py and this module all depend on them for the same
# reason (the shared sBPMN vocabulary). Known, deferred cleanup - not addressed here.

FUSEKI_BASE_URL = os.environ.get("FUSEKI_BASE_URL", "http://localhost:3030/bpmn")
GRAPH_BASE = "http://bpmn-rdf-transformer.org/graph/"


def _graph_uri(graph_id: str) -> str:
    return f"{GRAPH_BASE}{graph_id}"


def store_graph(graph: Graph, graph_id: str) -> None:
    # Enforces the storage invariant discussed and agreed on: one named graph
    # must represent exactly one uploaded process. This is a storage-layer
    # rule, not a general RDF-validity rule, so it lives here and not in
    # validate_rdf().
    process_count = len(list(graph.subjects(RDF.type, SBPMNC.process)))
    if process_count != 1:
        raise RdfStoreError(
            f"Graph muss genau einen sbpmnc:process enthalten, {process_count} gefunden"
        )

    turtle = graph.serialize(format="turtle")

    try:
        response = requests.put(
            f"{FUSEKI_BASE_URL}/data",
            params={"graph": _graph_uri(graph_id)},
            data=turtle.encode("utf-8"),
            headers={"Content-Type": "text/turtle"},
        )
    except requests.exceptions.RequestException as e:
        raise RdfStoreError(f"Fuseki nicht erreichbar: {e}") from e

    if not response.ok:
        raise RdfStoreError(
            f"Speichern fehlgeschlagen (Status {response.status_code}): {response.text}"
        )


def get_graph(graph_id: str) -> Graph:
    try:
        response = requests.get(
            f"{FUSEKI_BASE_URL}/data",
            params={"graph": _graph_uri(graph_id)},
            headers={"Accept": "text/turtle"},
        )
    except requests.exceptions.RequestException as e:
        raise RdfStoreError(f"Fuseki nicht erreichbar: {e}") from e

    if response.status_code == 404:
        raise RdfGraphNotFoundError(f"Kein Graph mit id '{graph_id}' gefunden")
    if not response.ok:
        raise RdfStoreError(
            f"Laden fehlgeschlagen (Status {response.status_code}): {response.text}"
        )

    graph = Graph()
    graph.parse(data=response.text, format="turtle")
    return graph


def delete_graph(graph_id: str) -> None:
    try:
        response = requests.delete(
            f"{FUSEKI_BASE_URL}/data",
            params={"graph": _graph_uri(graph_id)},
        )
    except requests.exceptions.RequestException as e:
        raise RdfStoreError(f"Fuseki nicht erreichbar: {e}") from e

    if response.status_code == 404:
        return  # already absent - the goal state already holds, treat as success

    if not response.ok:
        raise RdfStoreError(
            f"Löschen fehlgeschlagen (Status {response.status_code}): {response.text}"
        )


def run_select_query(sparql: str, graph_id: str) -> list[dict]:
    try:
        response = requests.post(
            f"{FUSEKI_BASE_URL}/sparql",
            data={
                "query": sparql,
                "default-graph-uri": _graph_uri(graph_id),
            },
            headers={"Accept": "application/sparql-results+json"},
        )
    except requests.exceptions.RequestException as e:
        raise RdfStoreError(f"Fuseki nicht erreichbar: {e}") from e

    if not response.ok:
        raise RdfStoreError(
            f"SPARQL-Anfrage fehlgeschlagen (Status {response.status_code}): {response.text}"
        )

    bindings = response.json()["results"]["bindings"]
    return [{var: value["value"] for var, value in row.items()} for row in bindings]
