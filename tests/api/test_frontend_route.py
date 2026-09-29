import pytest

from bpmn_rdf_transformer.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return app.test_client()


def test_index_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'id="bpmn-container"' in response.data
    assert b'id="turtle-container"' in response.data
    assert b'id="file-input"' in response.data
    assert b'id="upload-button"' in response.data
