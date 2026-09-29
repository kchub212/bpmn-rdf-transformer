from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from bpmn_rdf_transformer.exceptions import (
    BpmnError,
    BpmnParseError,
    BpmnValidationError,
    RdfGraphNotFoundError,
    RdfParseError,
    RdfStoreError,
    RdfValidationError,
)

STATUS_CODES = {
    BpmnParseError: 400,
    BpmnValidationError: 400,
    RdfParseError: 400,
    RdfValidationError: 422,
    RdfStoreError: 502,
    RdfGraphNotFoundError: 404,
}


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(BpmnError)
    def handle_bpmn_error(error: BpmnError):
        status = STATUS_CODES.get(type(error), 400)
        return jsonify(error=str(error), type=type(error).__name__), status

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return jsonify(error=error.description, type=error.name), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        return jsonify(error="Unerwarteter Serverfehler", type="InternalServerError"), 500
