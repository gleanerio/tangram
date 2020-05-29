import os
import json
import requests
import flask
from flask.views import MethodView
from flask_cors import CORS
import rdflib
import sosov.verify
from flasgger import Swagger
from extruct.jsonld import JsonLdExtractor

IS_LAMBDA = False
s3_client = None

if "SERVERTYPE" in os.environ and os.environ["SERVERTYPE"] == "AWS Lambda":
    import boto3

    IS_LAMBDA = True
    s3_client = boto3.client("s3")

app = flask.Flask(
    __name__,
    static_url_path="",
    static_folder="web/static",
    template_folder="web/templates",
)

app.config["SWAGGER"] = {
    "title": "Tangram",
}

swagger_template = {
    "info": {
        "title": "Tangram SHACL Verification",
        "description": "Service for evaluating schema.org content against ESIP Science on schema.org guidelines.",
        "version": "0.2.0",
    },
    "basePath": os.environ.get("lambda_base_path", ""),
    "schemes": ["https", "http"],
}

swagger = Swagger(app, template=swagger_template)

OUTPUT_FORMATS = {
    "human": "text/plain",
    "json-ld": "application/ld+json",
    "turtle": "text/turtle",
    "nt": "text/plain",
    "n3": "text/n3",
}

cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config["CORS_HEADERS"] = "Content-Type"


def getSchemaOrgTurtlePath():
    if IS_LAMBDA:
        fn_schema = "/tmp/schema.org.ttl"
        if not os.path.exists(fn_schema):
            app.logger.info("Refresh cache of schemaorg.ttl")
            bucket = os.environ.get("resources_bucket", "sosov-data")
            s3_client.download_file(bucket, "resources/data/schema.org.ttl", fn_schema)
        return fn_schema
    return os.abspath("resources/data/schema.org.ttl")


def response422(msg):
    return flask.Response(status=422, response=msg)


def getJsonLdFromHTML(html_text):
    """
    Returns an array of json_ld structures found in the provided html_text
    """
    jslde = JsonLdExtractor()
    return jslde.extract(html_text)


class VerifyView(MethodView):
    def doVerification(
        self, data_graph, shacl_graph, out_format, needs_schemaorg=False
    ):
        ont_graph = None
        advanced = False
        meta_shacl = False
        conforms, v_graph, v_text = sosov.verify.validateSHACL(
            data_graph,
            shacl_graph=shacl_graph,
            ont_graph=ont_graph,
            meta_shacl=meta_shacl,
            advanced=advanced,
        )
        if out_format == "human":
            return flask.Response(v_text, mimetype="text/plain")
        else:
            skolemized = v_graph.skolemize(
                authority="http://ld.geoschemas.org", basepath="/"
            )
            skolemized.namespace_manager = v_graph.namespace_manager
            return flask.Response(
                skolemized.serialize(format=out_format),
                mimetype=OUTPUT_FORMATS[out_format],
            )

    def get(self):
        """
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
          - name: "df"
            in: "query"
            required: false
            description: "Format for datagraph"
            type: "string"
            enum: ["html","json-ld","turtle","nt","n3"]
            default: "json-ld"
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
        """
        app.logger.debug("GET on verify")
        data_graph = None
        shacl_graph = None
        out_format = flask.request.args.get("fmt", "human")
        app.logger.debug("out_format = %s", out_format)
        if out_format not in OUTPUT_FORMATS.keys():
            return response422(f"Unrecognized format requested: {out_format}")
        try:
            data_graph = rdflib.ConjunctiveGraph()
            data_format = flask.request.args["df"]
            data_url = flask.request.args["dg"]
            if data_format == "html":
                response = requests.get(data_url)
                if response.status_code != 200:
                    raise ValueError(
                        f"Bad response ({response.status_code}) from dg = {data_url}"
                    )
                json_content = getJsonLdFromHTML(response.text)
                for json_data in json_content:
                    data_graph.parse(
                        data=json.dumps(json_data), format="json-ld", publicID=data_url
                    )
            else:
                data_graph.parse(flask.request.args["dg"], format="json-ld")
        except KeyError as e:
            return response422("Data graph URL is required.")
        except Exception as e:
            return response422(str(e))
        try:
            shacl_graph = rdflib.ConjunctiveGraph()
            shacl_graph.parse(flask.request.args["sg"], format="turtle")
        except KeyError as e:
            return response422("SHACL shape graph URL is required.")
        except Exception as e:
            return response422(str(e))
        return self.doVerification(data_graph, shacl_graph, out_format)

    def post(self):
        """
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

        """
        app.logger.debug("POST on verify")
        data_graph = None
        shacl_graph = None
        out_format = flask.request.form.get("fmt", "human")
        app.logger.debug("out_format = %s", out_format)
        if out_format not in OUTPUT_FORMATS.keys():
            return response422(f"Unrecognized format requested: {out_format}")
        try:
            data_graph = rdflib.ConjunctiveGraph()
            data_graph.parse(flask.request.files["dg"], format="json-ld")
        except KeyError as e:
            return response422("Data graph file is required.")
        except Exception as e:
            return response422(str(e))
        try:
            shacl_graph = rdflib.ConjunctiveGraph()
            shacl_graph.parse(flask.request.files["sg"], format="turtle")
        except KeyError as e:
            return response422("SHACL shape graph file is required.")
        except Exception as e:
            return response422(str(e))
        return self.doVerification(data_graph, shacl_graph, out_format)


app.add_url_rule("/verify", view_func=VerifyView.as_view("verify"))


@app.route("/extract")
def getHtmlFromUrl():
    """
    Return json-ld extracted from a URL.

    Attempts to extract json-ld from the HTML at the provided URL. The response is an array of
    json-ld blocks that were discovered.
    ---
    produces:
      - application/ld+json
    parameters:
      - name: "url"
        in: "query"
        required: true
        type: string
        description: "URL of page to extract JSON-LD from"
    responses:
      422:
        description: "Something went wrong retrieving content from the URL"
      200:
        description: "Array of retrieved json-ld content"
    """
    url = flask.request.args["url"]
    app.logger.debug("requested url = %s", url)
    response = requests.get(url)
    if response.status_code == 200:
        return flask.Response(
            response=json.dumps(getJsonLdFromHTML(response.text)),
            mimetype=OUTPUT_FORMATS["json-ld"],
        )
    return response422(f"Bad response ({response.status_code}) from url = {url}")


@app.route("/so")
def getSchemaOrg():
    """
    Return the cached copy of schema.org RDF in Turtle format.

    A copy of the schema.org RDF with the namespace expressed in "https://schema.org/" is cached for
    verification operations. This method returns a copy of that document.
    ---
    produces:
      - text/turtle
    responses:
      200:
        description: The schema.org RDF in Turtle
    """
    so_turtle = getSchemaOrgTurtlePath()
    return flask.Response(
        open(so_turtle, "rb").read(), mimetype=OUTPUT_FORMATS["turtle"]
    )


@app.route("/")
def index():
    return flask.redirect("apidocs")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
