# <img src="./docs/tangram_square.svg" width="40px" /> Tangram

## About

Tangram applies [SHACL](https://www.w3.org/TR/shacl/) graphs to [schema.org
](https://schema.org) graphs 
to evaluate conformance with [ESIP Science-on-Schema.org](https://github.com/ESIPFed/science-on-schema.org) guidelines.

Tangram emerged from a combination of the original [`Tangram`](https://github.com/earthcubearchitecture-project418/tangram) 
by Doug Fils and [`so-tools`](https://github.com/datadavev/sotools) by Dave Vieglais with support of ESIP 
through a summer project activity. Tangram relies heavily on [RDFLib](https://github.com/RDFLib/rdflib) and 
[PySHACL](https://github.com/RDFLib/pySHACL) for logic, and the ESIP Science-on-Schema.org guidelines for 
validation rules which are implemented primarily as SHACL shape graphs.

Tangram is provided as a commandline application and a Flask web service that can be run locally, behind 
a web server such as Apache, as a Docker application, to Google Cloud Run, or as an AWS Lambda service.

The core operational workflow of Tangram takes as input a data graph and a shape graph and outputs a 
[SHACL validation report](https://www.w3.org/TR/shacl/#validation-report) in plain text or RDF.
 


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

### Local development install and run

This process is for local development, testing, and use. It is not suitable for a production deployment.
```bash
python -m venv env
. env/bin/activate
pip install -e git+https://github.com/RDFLib/rdflib.git@af625d0bc48b656b614629b9ad56df63b88a0d17#egg=rdflib
pip install -e git+https://github.com/RDFLib/rdflib-jsonld.git@070d45cad067276e72df5d8f362aee65c158df40#egg=rdflib_jsonld
pip install -r requirements.txt
python app.py
#Open http://localhost:8080 in a browser
```

### Docker build and run

Docker offers a simple path for deploying Tangram as a production service.

```bash
make docker
docker run run --publish 8080:8080 --name tangram fils/p418tangram:0.1.17
#Open http://localhost:8080 in a browser
```

### AWS Lambda

Deployment to AWS Lambda is managed by Zappa which works by packaging the virtual environment and deploying to 
Lambda in an environment described in zappa_settings.json. The included copy of zappa_settings will need to be 
adjusted to work with the AWS account being used to manage the deployment. In particular, adjust the `role_arn`
value to the role created for the deployment.

1. Setup virtual environment

A deployment to AWS Lambda needs to include all dependencies outsde the standard python libraries. Zappa creates
the deployment by examining the python environment and bundling up extra libraries. The simplest way to do this
is with a virtual environment.

```shell script
python -m venv lambda_env
. lambda_env/bin/activate
pip install -e "git+git://github.com/RDFLib/rdflib.git#egg=rdflib"
pip install -e "git+git://github.com/RDFLib/rdflib-jsonld.git#egg=rdflib_jsonld"
pip install -r aws_lambda/requirements.txt
```

2. Prepare AWS IAM role for running the task

```shell script
# cd to the folder that contains sosov_app.py
# Set this to the account ID
ACCOUNT_ID="77633809XXXX"

aws iam create-role \
    --role-name ZappaLambdaExecution \
    --assume-role-policy-document file://aws_lambda/policy.json

aws iam attach-role-policy \
    --role-name ZappaLambdaExecution \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

#Update the role policy with the account number
sed "s/__ACOUNT_ID__/${ACCOUNT_ID}/g" aws_lambda/role_policy_template.json > "role_policy_${ACCOUNT_ID}.json"

aws iam put-role-policy \
    --role-name ZappaLambdaExecution \
    --policy-name AWSLambdaBasicExecutionRole \
    --policy-document "file://role_policy_${ACCOUNT_ID}.json" 

#Create zappa_settings.json with the account id in the current folder
sed "s/__ACCOUNT_ID__/${ACCOUNT_ID}/g" aws_lambda/zappa_settings_template.json > zappa_settings.json
``` 

3. Deploy the Lambda

The following all assume `cwd` is the folder containing `sosov_app.py`.

```shell script
$ zappa deploy dev
...
Deploying API Gateway..
Deployment complete!: https://7qwcfov1fc.execute-api.us-east-1.amazonaws.com/dev
```

To update the deployment after changes:

```shell script
$ zappa update dev
```

To remove the Lambda operation

```shell script
$ zappa undeploy dev
```

