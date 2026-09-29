import io
from unittest.mock import patch

import pytest
from rdflib import Graph

from bpmn_rdf_transformer.api.app import create_app
from bpmn_rdf_transformer.exceptions import RdfGraphNotFoundError, RdfStoreError
from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_file
from bpmn_rdf_transformer.rdf.mapper import to_rdf

MINIMAL_BPMN_PATH = "tests/fixtures/valid/minimal_process.bpmn"


@pytest.fixture
def client():
    app = create_app()
    return app.test_client()


def _minimal_bpmn_bytes():
    with open(MINIMAL_BPMN_PATH, "rb") as f:
        return f.read()


def test_upload_without_file_returns_400(client):
    response = client.post("/api/processes", data={})

    assert response.status_code == 400
    assert response.get_json()["type"] == "BadRequest"


@patch("bpmn_rdf_transformer.api.app.store_graph")
def test_upload_valid_bpmn_returns_graph_id_and_bpmn(mock_store, client):
    data = {"file": (io.BytesIO(_minimal_bpmn_bytes()), "minimal_process.bpmn")}

    response = client.post("/api/processes", data=data, content_type="multipart/form-data")

    assert response.status_code == 200
    body = response.get_json()
    assert "graph_id" in body
    assert "<?xml" in body["bpmn_xml"]
    assert body["warnings"] == []
    mock_store.assert_called_once()


def test_upload_malformed_bpmn_returns_400(client):
    data = {"file": (io.BytesIO(b"<not-bpmn/>"), "bad.bpmn")}

    response = client.post("/api/processes", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    assert response.get_json()["type"] in ("BpmnParseError", "BpmnValidationError")


@patch("bpmn_rdf_transformer.api.app.from_rdf")
@patch("bpmn_rdf_transformer.api.app.get_graph")
def test_get_bpmn_returns_xml(mock_get_graph, mock_from_rdf, client):
    process = parse_bpmn_file(MINIMAL_BPMN_PATH)
    mock_get_graph.return_value = Graph()
    mock_from_rdf.return_value = process

    response = client.get("/api/processes/some-id/bpmn")

    assert response.status_code == 200
    assert "<?xml" in response.get_json()["bpmn_xml"]


@patch("bpmn_rdf_transformer.api.app.get_graph")
def test_get_bpmn_nonexistent_graph_id_returns_404(mock_get_graph, client):
    mock_get_graph.side_effect = RdfGraphNotFoundError("Kein Graph mit id 'missing-id' gefunden")

    response = client.get("/api/processes/missing-id/bpmn")

    assert response.status_code == 404
    assert response.get_json()["type"] == "RdfGraphNotFoundError"


@patch("bpmn_rdf_transformer.api.app.get_graph")
def test_get_bpmn_store_failure_returns_502(mock_get_graph, client):
    mock_get_graph.side_effect = RdfStoreError("Fuseki nicht erreichbar")

    response = client.get("/api/processes/some-id/bpmn")

    assert response.status_code == 502
    assert response.get_json()["type"] == "RdfStoreError"


@patch("bpmn_rdf_transformer.api.app.get_graph")
def test_get_rdf_returns_turtle(mock_get_graph, client):
    process = parse_bpmn_file(MINIMAL_BPMN_PATH)
    mock_get_graph.return_value = to_rdf(process)

    response = client.get("/api/processes/some-id/rdf")

    assert response.status_code == 200
    assert response.content_type.startswith("text/turtle")


def test_query_without_sparql_field_returns_400(client):
    response = client.post("/api/processes/some-id/query", json={})

    assert response.status_code == 400
    assert response.get_json()["type"] == "BadRequest"


@patch("bpmn_rdf_transformer.api.app.run_select_query")
def test_query_returns_results(mock_run_query, client):
    mock_run_query.return_value = [{"id": "Task_1"}]

    response = client.post(
        "/api/processes/some-id/query", json={"sparql": "SELECT ?id WHERE { ?s ?p ?id }"}
    )

    assert response.status_code == 200
    assert response.get_json()["results"] == [{"id": "Task_1"}]


def test_update_rdf_without_turtle_field_returns_400(client):
    response = client.put("/api/processes/some-id/rdf", json={})

    assert response.status_code == 400
    assert response.get_json()["type"] == "BadRequest"


def test_update_rdf_with_malformed_turtle_returns_400(client):
    response = client.put(
        "/api/processes/some-id/rdf", json={"turtle": "this is not turtle @@@"}
    )

    assert response.status_code == 400
    assert response.get_json()["type"] == "RdfParseError"


@patch("bpmn_rdf_transformer.api.app.store_graph")
def test_update_rdf_with_valid_turtle_returns_bpmn(mock_store, client):
    process = parse_bpmn_file(MINIMAL_BPMN_PATH)
    turtle = to_rdf(process).serialize(format="turtle")

    response = client.put("/api/processes/some-id/rdf", json={"turtle": turtle})

    assert response.status_code == 200
    body = response.get_json()
    assert "<?xml" in body["bpmn_xml"]
    mock_store.assert_called_once()


@patch("bpmn_rdf_transformer.api.app.delete_graph")
def test_delete_process(mock_delete, client):
    response = client.delete("/api/processes/some-id")

    assert response.status_code == 204
    mock_delete.assert_called_once_with("some-id")
