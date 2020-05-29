import pyshacl


def listNodeShapes(g):
    """
    Return a list of the SHACL NodeShapes in g

    Args:
        g: graph

    Returns:

    """
    for s,p,o in g.triples(None, None, "<http://www.w3.org/ns/shacl#NodeShape>"):
        print(s)
        print(p)
        print(o)
        print("===")


def validateSHACL(data_graph, shacl_graph=None, ont_graph=None, meta_shacl=False, advanced=False):
    """
    Validate data against a SHACL shape using common options.

    Calls pyshacl.validate with the options:

    :inference: "rdfs"
    :meta_shacl: True
    :abort_on_error: True
    :debug: False
    :advanced: True

    When validating shapes that use subclass inference, it is necessary for the relationships to be provided in one
    of the graphs, or separately with the ``onto_graph`` property.

    Args:
        shape_graph (:class:`~rdflib.graph.Graph`): A SHACL shape graph
        data_graph (:class:`~rdflib.graph.Graph`): Data graph to be validated with shape_graph
        ontology_graph (:class:`~rdflib.graph.Graph`): Optional ontology graph to be added to the data graph
        meta_shacl: (boolean) Perform tests against shacl shape
        advanced: (boolean) Enable advanced functionality, required for SPARQL

    Returns (tuple): Conformance (boolean), result graph (:class:`~rdflib.graph.Graph`) and result text
    """
    inference = None
    if ont_graph is not None:
        inference = 'rdfs'
    conforms, result_graph, result_text = pyshacl.validate(
        data_graph,
        shacl_graph=shacl_graph,
        ont_graph=ont_graph,
        inference=inference,
        meta_shacl=meta_shacl,
        abort_on_error=False,
        debug=False,
        advanced=advanced,
    )
    return conforms, result_graph, result_text
