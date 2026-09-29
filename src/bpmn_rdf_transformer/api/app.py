import uuid

from flask import Flask, jsonify, render_template, request
from rdflib import Graph

from bpmn_rdf_transformer.api.errors import register_error_handlers
from bpmn_rdf_transformer.exceptions import RdfParseError
from bpmn_rdf_transformer.parser.bpmn_parser import parse_bpmn_string
from bpmn_rdf_transformer.rdf.improvement import improve_rdf
from bpmn_rdf_transformer.rdf.mapper import to_rdf
from bpmn_rdf_transformer.rdf.reader import from_rdf
from bpmn_rdf_transformer.rdf.store import delete_graph, get_graph, run_select_query, store_graph
from bpmn_rdf_transformer.rdf.validation import validate_rdf
from bpmn_rdf_transformer.writer.bpmn_writer import write_bpmn


def create_app() -> Flask:
    app = Flask(__name__)
    register_error_handlers(app)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/processes")
    def upload_process():
        if "file" not in request.files or request.files["file"].filename == "":
            return jsonify(error="Keine Datei hochgeladen", type="BadRequest"), 400

        xml = request.files["file"].read().decode("utf-8")

        process = parse_bpmn_string(xml)
        bpmn_xml = write_bpmn(process)

        graph = to_rdf(process)
        validate_rdf(graph)
        graph, warnings = improve_rdf(graph)

        graph_id = str(uuid.uuid4())
        store_graph(graph, graph_id)

        return jsonify(graph_id=graph_id, bpmn_xml=bpmn_xml, warnings=warnings)

    @app.get("/api/processes/<graph_id>/bpmn")
    def get_process_bpmn(graph_id):
        graph = get_graph(graph_id)
        process = from_rdf(graph)
        bpmn_xml = write_bpmn(process)

        return jsonify(bpmn_xml=bpmn_xml)

    @app.get("/api/processes/<graph_id>/rdf")
    def get_process_rdf(graph_id):
        graph = get_graph(graph_id)
        turtle = graph.serialize(format="turtle")

        return turtle, 200, {"Content-Type": "text/turtle"}

    @app.post("/api/processes/<graph_id>/query")
    def query_process(graph_id):
        data = request.get_json(silent=True) or {}
        if "sparql" not in data:
            return jsonify(error="Feld 'sparql' fehlt", type="BadRequest"), 400

        results = run_select_query(data["sparql"], graph_id)

        return jsonify(results=results)

    @app.put("/api/processes/<graph_id>/rdf")
    def update_process_rdf(graph_id):
        data = request.get_json(silent=True) or {}
        if "turtle" not in data:
            return jsonify(error="Feld 'turtle' fehlt", type="BadRequest"), 400

        graph = Graph()
        try:
            graph.parse(data=data["turtle"], format="turtle")
        except Exception as e:
            raise RdfParseError(f"Turtle konnte nicht gelesen werden: {e}") from e

        validate_rdf(graph)
        graph, warnings = improve_rdf(graph)
        process = from_rdf(graph)
        store_graph(graph, graph_id)
        bpmn_xml = write_bpmn(process)

        return jsonify(bpmn_xml=bpmn_xml, warnings=warnings)

    @app.delete("/api/processes/<graph_id>")
    def delete_process(graph_id):
        delete_graph(graph_id)

        return "", 204

    return app
