import os
from flask import Flask, abort, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from pyshacl import validate
import json
import rdflib
import requests
from rdflib import Graph, plugin
from rdflib.serializer import Serializer
from bs4 import BeautifulSoup
import urllib
import urllib.request

app = Flask(__name__,
            static_url_path='',
            static_folder='web/static',
            template_folder='web/templates')

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

# /validate 

@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # should try these too then error if not loadable to graph
        dg = request.files['datagraph']
        sg = request.files['shapegraph']
        try:
            f = request.form['format']
        except:
            f = 'robot'

        # Make some graphs and parse our uploads into them
        # How does python treat errors here?   trapped by Flask?  (see note about try above)
        s = rdflib.Graph()
        sr = s.parse(sg, format="ttl")
        d = rdflib.Graph()
        dr = d.parse(dg, format="json-ld")

        # call pySHACL
        conforms, v_graph, v_text = validate(dr, shacl_graph=sr,
                                             data_graph_format="json-ld",
                                             shacl_graph_format="ttl",
                                             inference='none', debug=False,
                                             serialize_report_graph=False)

        # I default to robot, but then never bother to test that  :(
        if f == 'human':
            return '{} {}'.format(conforms, v_text)
        else:
            # return v_graph.serialize(format="nt")
            skolemver = v_graph.skolemize(authority="http://ld.geoschemas.org")
            return skolemver.serialize(format="nt")

    if request.method == 'GET':
        render_template("index.html")

# @app.route('/')
# def hello_world():
#        return 'Tangram services are described at the GitHub Repo'
@app.route("/")
def index():

    ct = request.headers.get('Accept')

    if "text/html" in ct:
        return render_template("index.html")
    else:
        return render_template("index.txt")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
