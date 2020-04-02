# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.7

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .

# Install production dependencies.
RUN pip install gunicorn
RUN pip install -e git+https://github.com/RDFLib/rdflib.git@af625d0bc48b656b614629b9ad56df63b88a0d17#egg=rdflib
# RUN pip install rdflib  # need the dev version above for skolemize with authority attribute
RUN pip install -e git+https://github.com/RDFLib/rdflib-jsonld.git@070d45cad067276e72df5d8f362aee65c158df40#egg=rdflib_jsonld
RUN pip install -r requirements.txt
#RUN pip install Flask gunicorn
#RUN pip install flask-cors
#RUN pip install pyshacl
#RUN pip install jsonify
#RUN pip install -e git+https://github.com/RDFLib/rdflib.git@af625d0bc48b656b614629b9ad56df63b88a0d17#egg=rdflib
## RUN pip install rdflib  # need the dev version above for skolemize with authority attribute
#RUN pip install -e git+https://github.com/RDFLib/rdflib-jsonld.git@070d45cad067276e72df5d8f362aee65c158df40#egg=rdflib_jsonld
#RUN pip install extruct
#RUN pip install beautifulsoup4
#RUN pip install flasgger
##RUN pip install owlrl
##RUN mv /usr/local/bin/owlrl.py /usr/local/bin/owlrl   # ref https://github.com/RDFLib/OWL-RL/issues/29

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
#CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 app:app

