from unittest.mock import MagicMock, patch

import pytest
import requests
from rdflib import Graph

from bpmn_rdf_transformer.exceptions import RdfGraphNotFoundError, RdfStoreError
from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file
from bpmn_rdf_transformer.rdf import store
from bpmn_rdf_transformer.rdf.mapper import to_rdf


def _valid_graph():
    process = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    return to_rdf(process)


def test_store_graph_rejects_graph_with_no_process():
    with pytest.raises(RdfStoreError):
        store.store_graph(Graph(), "some-id")


def test_store_graph_rejects_graph_with_two_processes():
    process_a = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    process_b = parse_bpmn_file("tests/fixtures/valid/minimal_process.bpmn")
    combined = to_rdf(process_a) + to_rdf(process_b)

    with pytest.raises(RdfStoreError):
        store.store_graph(combined, "some-id")


@patch("bpmn_rdf_transformer.rdf.store.requests.put")
def test_store_graph_sends_put_request(mock_put):
    mock_put.return_value = MagicMock(ok=True)

    store.store_graph(_valid_graph(), "upload-1")

    mock_put.assert_called_once()
    _, kwargs = mock_put.call_args
    assert kwargs["params"]["graph"] == store._graph_uri("upload-1")
    assert kwargs["headers"]["Content-Type"] == "text/turtle"


@patch("bpmn_rdf_transformer.rdf.store.requests.put")
def test_store_graph_raises_on_bad_response(mock_put):
    mock_put.return_value = MagicMock(ok=False, status_code=500, text="server error")

    with pytest.raises(RdfStoreError):
        store.store_graph(_valid_graph(), "upload-1")


@patch("bpmn_rdf_transformer.rdf.store.requests.put")
def test_store_graph_raises_when_fuseki_unreachable(mock_put):
    mock_put.side_effect = requests.exceptions.ConnectionError("no connection")

    with pytest.raises(RdfStoreError):
        store.store_graph(_valid_graph(), "upload-1")


@patch("bpmn_rdf_transformer.rdf.store.requests.get")
def test_get_graph_parses_turtle_response(mock_get):
    original_graph = _valid_graph()
    mock_get.return_value = MagicMock(
        ok=True, status_code=200, text=original_graph.serialize(format="turtle")
    )

    result = store.get_graph("upload-1")

    assert len(result) == len(original_graph)


@patch("bpmn_rdf_transformer.rdf.store.requests.get")
def test_get_graph_raises_not_found_on_404(mock_get):
    mock_get.return_value = MagicMock(ok=False, status_code=404, text="not found")

    with pytest.raises(RdfGraphNotFoundError):
        store.get_graph("missing-id")


@patch("bpmn_rdf_transformer.rdf.store.requests.get")
def test_get_graph_not_found_is_also_a_store_error(mock_get):
    mock_get.return_value = MagicMock(ok=False, status_code=404, text="not found")

    with pytest.raises(RdfStoreError):
        store.get_graph("missing-id")


@patch("bpmn_rdf_transformer.rdf.store.requests.delete")
def test_delete_graph_sends_delete_request(mock_delete):
    mock_delete.return_value = MagicMock(ok=True)

    store.delete_graph("upload-1")

    mock_delete.assert_called_once()
    _, kwargs = mock_delete.call_args
    assert kwargs["params"]["graph"] == store._graph_uri("upload-1")


@patch("bpmn_rdf_transformer.rdf.store.requests.delete")
def test_delete_graph_raises_on_bad_response(mock_delete):
    mock_delete.return_value = MagicMock(ok=False, status_code=500, text="error")

    with pytest.raises(RdfStoreError):
        store.delete_graph("upload-1")


@patch("bpmn_rdf_transformer.rdf.store.requests.delete")
def test_delete_graph_treats_404_as_success(mock_delete):
    mock_delete.return_value = MagicMock(ok=False, status_code=404, text="not found")

    store.delete_graph("already-gone")  # must not raise


@patch("bpmn_rdf_transformer.rdf.store.requests.post")
def test_run_select_query_parses_json_bindings(mock_post):
    mock_response = MagicMock(ok=True)
    mock_response.json.return_value = {
        "results": {
            "bindings": [
                {"id": {"type": "literal", "value": "StartEvent_1x4t1so"}},
            ]
        }
    }
    mock_post.return_value = mock_response

    rows = store.run_select_query("SELECT ?id WHERE { ?s ?p ?id }", "upload-1")

    assert rows == [{"id": "StartEvent_1x4t1so"}]


@patch("bpmn_rdf_transformer.rdf.store.requests.post")
def test_run_select_query_raises_on_bad_response(mock_post):
    mock_post.return_value = MagicMock(ok=False, status_code=400, text="bad query")

    with pytest.raises(RdfStoreError):
        store.run_select_query("SELECT ...", "upload-1")
