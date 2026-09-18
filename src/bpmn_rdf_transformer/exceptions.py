class BpmnError(Exception):
    """Base class for all BPMN-related errors."""


class BpmnParseError(BpmnError):
    """Raised when BPMN XML cannot be turned into the internal model."""


class BpmnValidationError(BpmnError):
    """Raised when the internal model breaks a BPMN rule."""


class RdfParseError(BpmnError):
    """Raised when text submitted as RDF cannot even be parsed as Turtle."""


class RdfValidationError(BpmnError):
    """Raised when an RDF graph breaks an sBPMN-level rule."""


class RdfStoreError(BpmnError):
    """Raised when storing, loading or querying an RDF graph in Fuseki fails."""
