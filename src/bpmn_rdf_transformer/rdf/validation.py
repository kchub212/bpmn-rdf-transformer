from rdflib import Graph, RDF

from bpmn_rdf_transformer.exceptions import RdfValidationError
from bpmn_rdf_transformer.rdf.mapper import SBPMNC, SBPMNP


FLOW_NODE_CLASSES = {
    SBPMNC.startEvent,
    SBPMNC.endEvent,
    SBPMNC.task,
    SBPMNC.exclusiveGateway,
}


# Rule 1: sourceRef/targetRef must point at a resource that actually exists in the graph.
DANGLING_REF_QUERY = """
PREFIX sbpmnp: <https://sBPMN.github.io/2.0/properties#>

SELECT ?flow ?ref WHERE {
  ?flow sbpmnp:sourceRef|sbpmnp:targetRef ?ref .
  FILTER NOT EXISTS { ?ref ?p ?o . }
}
"""

# Rule 2: no two flowElements of the SAME process may share an id.
# Scoped per process (via ?process) and restricted to flowElements only,
# so a Process.id equal to one of its own element ids never triggers this rule.
DUPLICATE_ID_QUERY = """
PREFIX sbpmnc: <https://sBPMN.github.io/2.0/classes#>
PREFIX sbpmnp: <https://sBPMN.github.io/2.0/properties#>

SELECT ?process ?id (COUNT(?element) AS ?count) WHERE {
  ?process a sbpmnc:process ;
           sbpmnp:flowElement ?element .
  ?element sbpmnp:id ?id .
}
GROUP BY ?process ?id
HAVING (COUNT(?element) > 1)
"""


def validate_rdf(graph: Graph) -> None:
    dangling = list(graph.query(DANGLING_REF_QUERY))
    if dangling:
        row = dangling[0]
        raise RdfValidationError(
            f"Verweis auf nicht existierende Ressource: {row.ref} (referenziert von {row.flow})"
        )

    duplicates = list(graph.query(DUPLICATE_ID_QUERY))
    if duplicates:
        row = duplicates[0]
        raise RdfValidationError(
            f"Doppelte ID '{row.id}' innerhalb des Prozesses {row.process} gefunden "
            f"({row['count']} Elemente)"
        )

    # Rule 3: every process and every flowElement must have exactly one sbpmnp:id,
    # and that id must be a non-empty value ("missing or invalid").
    elements_needing_id = set(graph.subjects(RDF.type, SBPMNC.process))
    elements_needing_id.update(graph.objects(None, SBPMNP.flowElement))

    for element in elements_needing_id:
        ids = list(graph.objects(element, SBPMNP.id))
        if len(ids) != 1 or not str(ids[0]).strip():
            raise RdfValidationError(f"Ressource {element} hat keine gültige sbpmnp:id")

    # Rule 4: every sourceRef/targetRef must have exactly one value, and that value
    # must point at an actual flowNode (startEvent, endEvent, task or exclusiveGateway),
    # not e.g. another sequenceFlow. The sBPMN ontology itself declares no range for
    # sourceRef/targetRef, so nothing at the ontology level stops a malformed graph
    # from having zero, two, or a wrongly-typed value here.
    for flow in graph.subjects(RDF.type, SBPMNC.sequenceFlow):
        for prop in (SBPMNP.sourceRef, SBPMNP.targetRef):
            targets = list(graph.objects(flow, prop))
            if len(targets) != 1:
                raise RdfValidationError(
                    f"Sequenzfluss {flow} hat nicht genau einen Wert für {prop} "
                    f"({len(targets)} gefunden)"
                )

            target = targets[0]
            target_types = set(graph.objects(target, RDF.type))
            if not (target_types & FLOW_NODE_CLASSES):
                raise RdfValidationError(
                    f"Sequenzfluss {flow} verweist über {prop} auf {target}, "
                    "das kein flowNode ist"
                )
