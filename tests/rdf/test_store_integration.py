import os

import pytest

from bpmn_rdf_transformer.exceptions import RdfStoreError
from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file
from bpmn_rdf_transformer.rdf import store
from bpmn_rdf_transformer.rdf.mapper import to_rdf

pytestmark = pytest.mark.skipif(
    not os.environ.get("FUSEKI_BASE_URL"),
    reason="FUSEKI_BASE_URL not set - skipping tests that need a real running Fuseki instance",
)


def test_store_and_retrieve_graph_round_trip():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    store.store_graph(graph, "integration-test-1")
    retrieved = store.get_graph("integration-test-1")

    assert len(retrieved) == len(graph)

    store.delete_graph("integration-test-1")


def test_delete_then_get_raises():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    graph = to_rdf(process)

    store.store_graph(graph, "integration-test-2")
    store.delete_graph("integration-test-2")

    with pytest.raises(RdfStoreError):
        store.get_graph("integration-test-2")


def test_run_select_query_is_scoped_to_one_named_graph():
    process_a = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    process_b = parse_bpmn_file("tests/fixtures/valid/multiple_tasks.bpmn")

    # process_a.id and several node ids are shared between these two fixtures
    # (multiple_tasks.bpmn was built by extending a copy of minimal_process.bpmn),
    # so the scoping check needs an id that only exists in one of the two graphs.
    marker_only_in_a = next(
        node_id for node_id in process_a.nodes if node_id not in process_b.nodes
    )
    marker_only_in_b = next(
        node_id for node_id in process_b.nodes if node_id not in process_a.nodes
    )

    store.store_graph(to_rdf(process_a), "integration-test-query-a")
    store.store_graph(to_rdf(process_b), "integration-test-query-b")

    try:
        rows = store.run_select_query(
            """
            PREFIX sbpmnp: <https://sBPMN.github.io/2.0/properties#>
            SELECT ?id WHERE { ?s sbpmnp:id ?id }
            """,
            "integration-test-query-a",
        )
        ids = {row["id"] for row in rows}

        assert marker_only_in_a in ids
        assert marker_only_in_b not in ids
    finally:
        store.delete_graph("integration-test-query-a")
        store.delete_graph("integration-test-query-b")
