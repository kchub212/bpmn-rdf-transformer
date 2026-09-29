import io
import os

import pytest

from bpmn_rdf_transformer.api.app import create_app

pytestmark = pytest.mark.skipif(
    not os.environ.get("FUSEKI_BASE_URL"),
    reason="FUSEKI_BASE_URL not set - skipping tests that need a real running Fuseki instance",
)


@pytest.fixture
def client():
    app = create_app()
    return app.test_client()


def test_full_flow_upload_view_query_edit_view_delete(client):
    with open("tests/fixtures/valid/minimal_process.bpmn", "rb") as f:
        bpmn_bytes = f.read()

    upload_response = client.post(
        "/api/processes",
        data={"file": (io.BytesIO(bpmn_bytes), "minimal_process.bpmn")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    graph_id = upload_response.get_json()["graph_id"]

    bpmn_response = client.get(f"/api/processes/{graph_id}/bpmn")
    assert bpmn_response.status_code == 200
    assert "<?xml" in bpmn_response.get_json()["bpmn_xml"]

    query_response = client.post(
        f"/api/processes/{graph_id}/query",
        json={
            "sparql": """
                PREFIX sbpmnp: <https://sBPMN.github.io/2.0/properties#>
                SELECT ?id WHERE { ?s sbpmnp:id ?id }
            """
        },
    )
    assert query_response.status_code == 200
    ids = {row["id"] for row in query_response.get_json()["results"]}
    assert "StartEvent_1x4t1so" in ids

    rdf_response = client.get(f"/api/processes/{graph_id}/rdf")
    assert rdf_response.status_code == 200
    turtle = rdf_response.get_data(as_text=True)

    edit_response = client.put(f"/api/processes/{graph_id}/rdf", json={"turtle": turtle})
    assert edit_response.status_code == 200
    assert "<?xml" in edit_response.get_json()["bpmn_xml"]

    delete_response = client.delete(f"/api/processes/{graph_id}")
    assert delete_response.status_code == 204

    after_delete_response = client.get(f"/api/processes/{graph_id}/bpmn")
    assert after_delete_response.status_code == 404
    assert after_delete_response.get_json()["type"] == "RdfGraphNotFoundError"


def test_delete_process_is_idempotent(client):
    with open("tests/fixtures/valid/minimal_process.bpmn", "rb") as f:
        bpmn_bytes = f.read()

    upload_response = client.post(
        "/api/processes",
        data={"file": (io.BytesIO(bpmn_bytes), "minimal_process.bpmn")},
        content_type="multipart/form-data",
    )
    graph_id = upload_response.get_json()["graph_id"]

    first_delete = client.delete(f"/api/processes/{graph_id}")
    assert first_delete.status_code == 204

    second_delete = client.delete(f"/api/processes/{graph_id}")
    assert second_delete.status_code == 204
