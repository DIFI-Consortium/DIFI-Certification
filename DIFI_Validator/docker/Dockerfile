# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Copyright © `2023` `Microsoft Corporation`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT
# syntax=docker/dockerfile:1

ARG DISTRO=python:3.9-alpine

FROM $DISTRO

### Optional args that can be passed in on docker 'build' command:

# optional server deployment options for flask app
# (can be passed in as either 'build' arg or 'run' arg, will default to 'prod' server if no arg supplied):
# 1) dev  ->flask runs as the default flask web server, listening on port 5000, serving rest api/html pages directly
# 2) prod ->flask runs in uwsgi web server, listening on http socket on internal port 5000, communicating in
#           http protocol over the wire, flask can serve the rest api/html pages directly on port 5000 or can use
#           nginx running as a 'proxy' server on port 80 to contact flask/uwsgi's http server on the internal port 
#           5000 and serve all http rest api/html page calls on flask's behalf
# 3) prod-gateway ->flask runs in uwsgi web server, listening on unix domain file system socket, communicating in
#                   uwsgi protocol over the wire, flask does not serve rest api/html pages directly but uses nginx
#                   running as a 'application gateway' server to serve all http rest api/html page calls on flask's behalf
ARG FLASK_DEPLOY_ENV=prod

# non-root user and group to run docker container as
# (defaults to create a new user account in container with no login rights specifically for docker container use only)
ARG USER=cnfuser
ARG UID=1234
ENV USER=$USER
ENV UID=$UID
ARG DIFI_VERSION_MAJOR=1
ARG DIFI_VERSION_MINOR=1
ARG DIFI_VERSION_PATCH=0
ARG DIFI_VERSION_BUILD=0

# store local cache in /tmp
ENV DIFI_CACHE_HOME=/tmp

USER 0

# (important!!! if running container in a server deployment configuration option of 'application gateway' server like nginx (e.g. using unix domain socket)
# as the public facing server passing the http requests through to the flask app, then must pass in the USER/GROUP/UID/GID of
# the user account nginx is running under as build args in order for nginx to have permission to talk to the unix domain socket,
# instead of leaving as the default user)

### Optional args that can be passed in on docker 'run' command:

# optional server deployment options for flask app, see description above
ENV FLASK_DEPLOY_ENV=$FLASK_DEPLOY_ENV
# (important!!! don't change this to an 'application gateway' server deployment configuration option at runtime,
# unless the container was built with build args that changed the default USER/GROUP/UID/GID to the user account
# the 'application gateway' server like nginx is running under, the server will not function properly)

# difi receiver socket settings (if no value passed in on docker run command, it will use default values in code)
ENV DIFI_RX_PORT=
ENV DIFI_RX_MODE=
ENV DIFI_RX_HOST=0.0.0.0

# flask http server settings
ENV FLASK_APP=webgui.py
ENV FLASK_RUN_HOST=0.0.0.0

# install in docker container
RUN apk add --no-cache gcc g++ make musl-dev linux-headers ca-certificates bash && \
    adduser --disabled-password --gecos "" --home=/home/difi --uid $UID $USER

# set working dir
ENV FOLDER=/code
WORKDIR $FOLDER

# create python virtual environment, so can do pip installs of dependencies not as root
ENV VIRTUAL_ENV=$FOLDER/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt requirements.txt

# upgrade pip
RUN python3 -m pip install --upgrade pip && pip install -r requirements.txt

# python files
COPY --chown=0:0 dcs.py dvs.py dds.py webgui.py drx.py docker/start.sh difi_utils/ $FOLDER/

# add difi_utils library
COPY --chown=0:0 difi_utils difi_utils

# flask html pages
COPY --chown=0:0 templates/*.html templates/

# starts flask server webgui.py - listening for http calls for gui
# starts socket server drx.py - listening for difi packets from device
RUN chmod 555 start.sh drx.py && \
/bin/echo "{\"major\":$DIFI_VERSION_MAJOR,\"minor\":$DIFI_VERSION_MINOR,\"patch\":$DIFI_VERSION_PATCH,\"build\":\"$DIFI_VERSION_BUILD\"}" > /code/version-info.json
USER $UID
CMD ["./start.sh", "$FLASK_DEPLOY_ENV"]

