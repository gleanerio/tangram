import os
import flask #from flask import Flask, Response, request, redirect
from flask.views import MethodView
from flask_cors import CORS
import rdflib
from pyshacl import validate

from flasgger import Swagger

app = flask.Flask(__name__,
            static_url_path='',
            static_folder='web/static',
            template_folder='web/templates')
app.config['SWAGGER'] = {
    'title':'Tangram',
}

swagger_template = {
    "info": {
        "title": "Tangram SHACL Verification",
        "description":"Service for evaluating schema.org content against ESIP Science on schema.org guidelines.",
        "version":"0.2.0",
    },
    "basePath":"/dev",
    "schemes": [
        "https"
    ]
}

swagger = Swagger(app, template=swagger_template)

OUTPUT_FORMATS = {
    'human': 'text/plain',
    'json-ld':'application/ld+json',
    'turtle':'text/turtle',
    'nt':'text/plain',
    'n3':'text/n3',
}

cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

def response422(msg):
    return flask.Response(status=422, response=msg)

class VerifyView(MethodView):

    def doVerification(self, data_graph, shacl_graph, out_format, needs_schemaorg=False):
        # call pySHACL
        ont_graph = None
        inference = "none"
        if needs_schemaorg:
            # TODO: handle this
            # Load schema.org graph
            # set inference to 'rdfs'
            pass
        conforms, v_graph, v_text = validate(data_graph, shacl_graph=shacl_graph,
                                             data_graph_format="json-ld",
                                             shacl_graph_format="ttl",
                                             ont_graph=ont_graph,
                                             inference=inference, debug=False,
                                             serialize_report_graph=False)
        if out_format == 'human':
            return flask.Response(v_text, mimetype="text/plain")
        else:
            skolemized = v_graph.skolemize(authority="http://ld.geoschemas.org", basepath="/")
            skolemized.namespace_manager = v_graph.namespace_manager
            return flask.Response(skolemized.serialize(format=out_format), mimetype=OUTPUT_FORMATS[out_format])


    def get(self):
        '''
        Perform SHACL validation on provided data and SHACL sources.

        The locations of the data graph and shacl shape graph are provided as URLs, and
        must be accessible without authentication. The data graph must in serialized in
        json-ld and the SHACL graph in turtle.
        ---
        parameters:
          - name: "dg"
            in: "query"
            required: true
            description: "URL for data graph source"
            default: "https://raw.githubusercontent.com/datadavev/science-on-schema.org/2020-SOSOV/validation/testingDataGraphs/ds_badns1.json"
          - name: "sg"
            in: "query"
            required: true
            description: "URL for SHACL graph source"
            default: "https://raw.githubusercontent.com/datadavev/science-on-schema.org/2020-SOSOV/validation/shapes/so_namespace.ttl"
          - name: fmt
            in: "query"
            description: Format of response
            type: "string"
            enum: ['human', 'json-ld', 'turtle', 'nt', 'n3']
            default: human
        produces:
          - text/plain
          - text/turtle
          - application/n-triples
          - application/ld+json
        responses:
          422:
            description: Missing or invalid input data
          200:
            description: Result of SHACL evaluation
        '''
        data_graph = None
        shacl_graph = None
        out_format = flask.request.args.get('fmt', 'human')
        if out_format not in OUTPUT_FORMATS.keys():
            return response422(f"Unrecognized format requested: {out_format}")
        try:
            data_graph = rdflib.ConjunctiveGraph()
            data_graph.parse(flask.request.args['dg'], format="json-ld")
        except KeyError as e:
            return response422("Data graph URL is required.")
        except Exception as e:
            return response422(str(e))
        try:
            shacl_graph = rdflib.ConjunctiveGraph()
            shacl_graph.parse(flask.request.args['sg'], format="turtle")
        except KeyError as e:
            return response422("SHACL shape graph URL is required.")
        except Exception as e:
            return response422(str(e))
        return self.doVerification(data_graph, shacl_graph, out_format)


    def post(self):
        '''
        Perform SHACL validation on provided data and SHACL shape graphs.

        The data graph and SHACL shape graph are provided as file uploads.
        The data graph must in serialized in json-ld and the SHACL graph in turtle.
        ---
        consumes:
          - multipart/form-data
        produces:
          - text/plain
          - text/turtle
          - application/n-triples
          - application/ld+json
        parameters:
          - in: formData
            name: dg
            description: Data graph file
            type: file
            required: true
          - in: formData
            name: sg
            description: SHACL shape graph file
            type: file
            required: true
          - in: formData
            name: fmt
            description: Format of response
            type: "string"
            enum: ['human', 'json-ld', 'turtle', 'nt', 'n3']
            default: human
        responses:
          422:
            description: Missing or invalid input data
          200:
            description: Result of SHACL evaluation

        '''
        data_graph = None
        shacl_graph = None
        out_format = flask.request.form.get('fmt', 'human')
        app.logger.debug("out_format = %s", out_format)
        if out_format not in OUTPUT_FORMATS.keys():
            return response422(f"Unrecognized format requested: {out_format}")
        try:
            data_graph = rdflib.ConjunctiveGraph()
            data_graph.parse(flask.request.files['dg'], format="json-ld")
        except KeyError as e:
            return response422("Data graph file is required.")
        except Exception as e:
            return response422(str(e))
        try:
            shacl_graph = rdflib.ConjunctiveGraph()
            shacl_graph.parse(flask.request.files['sg'], format="turtle")
        except KeyError as e:
            return response422("SHACL shape graph file is required.")
        except Exception as e:
            return response422(str(e))
        return self.doVerification(data_graph, shacl_graph, out_format)


app.add_url_rule('/verify', view_func=VerifyView.as_view('verify'))


@app.route("/")
def index():
    return flask.redirect("apidocs")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
