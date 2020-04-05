# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.7

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .

# Install production dependencies.
RUN pip install gunicorn
RUN pip install -e "git+https://github.com/RDFLib/rdflib.git#egg=rdflib"
# RUN pip install rdflib  # need the dev version above for skolemize with authority attribute
RUN pip install -e "git+https://github.com/RDFLib/rdflib-jsonld.git#egg=rdflib_jsonld"
RUN pip install -r requirements-web.txt
##RUN pip install owlrl
##RUN mv /usr/local/bin/owlrl.py /usr/local/bin/owlrl   # ref https://github.com/RDFLib/OWL-RL/issues/29

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
#CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 app:app

