# Tangram

## About

A test program using Google Gloud Run for doing shacl conversion via pyshacl.  

## Tangram:  Simple service example

The Tangram services is a web services  wrapper around the pySHACL
(https://github.com/RDFLib/pySHACL) package.  It allows you to send in JSON-LD data 
graphs to test against a Turtle (ttl) encoded shape graph.

Invoke the tool with something like:

With httpie client:

```bash
httpclient -f POST https://tangram.gleaner.io/uploader  datagraph@./datagraphs/dataset-minimal-BAD.json-ld  shapegraph@./shapegraphs/googleRecommended.ttl format=human

localhost
httpclient -f POST http://localhost:8080/uploader  datagraph@./datagraphs/dataset-minimal-BAD.json-ld  shapegraph@./shapegraphs/googleRecommended.ttl format=human

```

Or with good old curl (with format set to huam):

```bash
curl -F  'datagraph=@./datagraphs/dataset-minimal-BAD.json-ld'  -F  'shapegraph=@./shapegraphs/googleRecommended.ttl' -F 'format=human'  https://tangram.gleaner.io/uploader
```

## Tangram testing a web page

```bash
httpclient "https://tangram.gleaner.io/ucheck?url=http://opencoredata.org/doc/dataset/b8d7bd1b-ef3b-4b08-a327-e28e1420adf0&format=human&shape=required"
```

## Install

Local for testing. Requires rdflib and rdflib-jsonld from github.