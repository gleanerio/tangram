import os
from flask import Flask, Response, request, redirect
from flask.views import MethodView
from flask_cors import CORS
from pyshacl import validate
import rdflib
import requests
from bs4 import BeautifulSoup
import urllib
import urllib.request
import logging

from flasgger import Swagger

app = Flask(__name__,
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
    "schemes": [
        "http",
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

# Add in a function that reads the local shape and returns human or machine response
# It will be method GET with ?url=URL&format=[human,machine]&shape=[required,recommended]
# /rescheck
@app.route('/ucheck', methods=['GET'])
def netcheck():
    if request.method == 'GET':
        u = request.args.get('url')  # if key doesn't exist, returns None
        f = request.args.get('format')  # if key doesn't exist, returns None
        s = request.args.get('shape')  # if key doesn't exist, returns None

        # read in shape graph
        if s == 'recommended':
            sg = open("./shapes/googleRecommended.ttl", 'r')
        else:
            sg = open("./shapes/googleRequired.ttl", 'r')

        s = rdflib.Graph()
        sr = s.parse(sg, format="ttl")

        html = urllib.request.urlopen(u).read()
        d = rdflib.Graph()

        if ".jsonld" in u:
            with urllib.request.urlopen(u) as response:
                jld = response.read()
            dr = d.parse(data=jld, format="json-ld")

        else:
            soup = BeautifulSoup(html, "html.parser")
            p = soup.find('script', {'type': 'application/ld+json'})
            dr = d.parse(data=p.contents[0], format="json-ld")

        # call pySHACL
        conforms, v_graph, v_text = validate(dr, shacl_graph=sr,
                                             data_graph_format="json-ld",
                                             shacl_graph_format="ttl",
                                             inference='none', debug=False,
                                             serialize_report_graph=False)

        # I default to robot, but then never both to test that  :(
        if f == 'human':
            return '{} {}'.format(conforms, v_text)
        else:
            return v_graph.serialize(format="nt")


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
            return Response(v_text, mimetype="text/plain")
        else:
            skolemized = v_graph.skolemize(authority="http://ld.geoschemas.org", basepath="/")
            skolemized.namespace_manager = v_graph.namespace_manager
            return Response(skolemized.serialize(format=out_format), mimetype=OUTPUT_FORMATS[out_format])


    def get(self):
        '''
        Perform SHACL validation on provided data and SHACL sources.

        The locations of the data graph and shacl shape graph are provided as URLs, and
        must be accessible without authentication. The data graph must in serialized in
        json-ld and the SHACL graph in turtle.
        ---
        parameters:
          - name: "datagraph"
            in: "query"
            required: true
            description: "URL for data graph source"
            default: "https://raw.githubusercontent.com/datadavev/science-on-schema.org/2020-SOSOV/validation/testingDataGraphs/ds_badns1.json"
          - name: "shapegraph"
            in: "query"
            required: true
            description: "URL for SHACL graph source"
            default: "https://raw.githubusercontent.com/datadavev/science-on-schema.org/2020-SOSOV/validation/shapes/so_namespace.ttl"
          - name: format
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
        out_format = request.args.get('format', 'human')
        if out_format not in OUTPUT_FORMATS.keys():
            return Response(status=422, response=f"Unrecognized format requested: {out_format}")
        try:
            data_graph = rdflib.ConjunctiveGraph()
            data_graph.parse(request.args['datagraph'], format="json-ld")
        except KeyError as e:
            return Response(status=422, response="Data graph URL is required.")
        except Exception as e:
            return Response(status=422, response=str(e))
        try:
            shacl_graph = rdflib.ConjunctiveGraph()
            shacl_graph.parse(request.args['shapegraph'], format="turtle")
        except KeyError as e:
            return Response(status=422, response="SHACL shape graph URL is required.")
        except Exception as e:
            return Response(status=422, response=str(e))
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
            name: datagraph
            description: Data graph file
            type: file
            required: true
          - in: formData
            name: shapegraph
            description: SHACL shape graph file
            type: file
            required: true
          - in: formData
            name: format
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
        out_format = request.form.get('format', 'human')
        app.logger.debug("out_format = %s", out_format)
        if out_format not in OUTPUT_FORMATS.keys():
            return Response(status=422, response=f"Unrecognized format requested: {out_format}")
        try:
            data_graph = rdflib.ConjunctiveGraph()
            data_graph.parse(request.files['datagraph'], format="json-ld")
        except KeyError as e:
            return Response(status=422, response="Data graph file is required.")
        except Exception as e:
            return Response(status=422, response=str(e))
        try:
            shacl_graph = rdflib.ConjunctiveGraph()
            shacl_graph.parse(request.files['shapegraph'], format="turtle")
        except KeyError as e:
            return Response(status=422, response="SHACL shape graph file is required.")
        except Exception as e:
            return Response(status=422, response=str(e))
        return self.doVerification(data_graph, shacl_graph, out_format)


app.add_url_rule('/verify', view_func=VerifyView.as_view('verify'))


@app.route("/")
def index():
    return redirect("/apidocs")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
