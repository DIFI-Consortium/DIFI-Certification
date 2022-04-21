# Copyright (C) 2022 Kratos Technology & Training Solutions, Inc.
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT
# syntax=docker/dockerfile:1
#
# cd to difi:
# [Example] sudo docker build --no-cache --force-rm -f docker/Dockerfile -t difi:latest .
#
# To run in console and write output to console:
# [Example] sudo docker run --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -i -t difi:latest
# [Example] sudo docker run --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=asyncio -i -t difi:latest
#
# To run as daemon:
# [Example] sudo docker run -d --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -i -t difi:latest
#
# To run in production (should add the restart on failure param):
# [Example] sudo docker run -d --net=host --restart=on-failure -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -i -t difi:latest
#
# To run in each of the three server deployment options for flask:
# DEV:
# [Example] sudo docker build --force-rm -f docker/Dockerfile -t difi_one .
# [Example] sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=dev difi_one
#    (note: will be listening on port 5000)
#
# PROD:
# [Example] sudo docker build --force-rm -f docker/Dockerfile -t difi_one .
# [Example] sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod difi_one
#    (note: will be listening on port 5000)
# OR with proxy server:
# [Example] sudo docker build --build-arg USER=nginx --build-arg GROUP=nginx --build-arg UID=2000 --build-arg GID=2000 --force-rm -f docker/Dockerfile -t difi_one .
# [Example] sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod difi_one
#    (note: will be listening on nginx port configured in nginx.conf, like port 80)
#
# PROD-GATEWAY (application-gateway):
# [Example] sudo docker build --build-arg USER=nginx --build-arg GROUP=nginx --build-arg UID=2000 --build-arg GID=2000 --force-rm -f docker/Dockerfile -t difi_one .
# [Example] sudo docker run -it --net=host -v /tmp:/tmp -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod-gateway difi_one
#    (note: will be listening on nginx port configured in nginx.conf, like port 80)
#
# To save the built docker container image as .tar.gz package:
# [Example] sudo docker save difi:latest|gzip > difi.tar.gz
#   (note: to see list of built images run: docker images)
#
# To look at console output inside docker container at runtime (i.e. at the cmd prompt inside container):
# sudo docker ps  (to get container id)
# sudo docker exec -it 3f650613bf36 /bin/sh  (to get cmd prompt inside container)
#
# To see container's user account and environment variables:
# sudo docker images  (to get container image id)
# sudo docker inspect c4f2dae2db1f
#


FROM python:3.7-alpine
# newer versions also work
#FROM python:3.9-alpine
#FROM python:3.10-alpine


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
ARG GROUP=cnfuser
ARG UID=1234
ARG GID=9876
ENV USER=$USER
ENV GROUP=$GROUP
ENV UID=$UID
ENV GID=$GID
# (important!!! if running container in a server deployment configuration option of 'application gateway' server like nginx (e.g. using unix domain socket)
# as the public facing server passing the http requests through to the flask app, then must pass in the USER/GROUP/UID/GID of
# the user account nginx is running under as build args in order for nginx to have permission to talk to the unix domain socket,
# instead of leaving as the default user)

# adds new non-root user and group to run docker container as
RUN addgroup -g $GID $GROUP; \
    adduser --disabled-password --gecos "" --home=/home/difi --ingroup $GROUP --uid $UID $USER


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
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
# change from default port 5000 to 6000
#ENV FLASK_RUN_PORT=6000


# install in docker container
RUN apk add --no-cache gcc musl-dev linux-headers ca-certificates bash;

# install additional utility programs in docker container
#RUN apk add --no-cache git curl unzip wget

# set working dir
ENV FOLDER=/code
WORKDIR $FOLDER
RUN chown -R $USER:$GROUP $FOLDER; \
    chmod 700 $FOLDER 

# switch to non-root user
USER $USER

# create python virtual environment, so can do pip installs of dependencies not as root 
ENV VIRTUAL_ENV=$FOLDER/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# upgrade pip
RUN python3 -m pip install --upgrade pip;

# DIFI receiver
COPY --chown=$USER:$GROUP python/drx.py drx.py
RUN chmod 700 drx.py

# DIFI senders
COPY --chown=$USER:$GROUP python/dcs.py dcs.py
COPY --chown=$USER:$GROUP python/dvs.py dvs.py
COPY --chown=$USER:$GROUP python/dds.py dds.py
COPY --chown=$USER:$GROUP python/dds_data.py dds_data.py
COPY --chown=$USER:$GROUP python/dificommon.py dificommon.py

# flask server
COPY --chown=$USER:$GROUP docker/input/app.py app.py

# flask html pages
COPY --chown=$USER:$GROUP docker/input/templates/*.html templates/

# copy all local files to docker container
#COPY --chown=$USER:$GROUP . .

# install python dependencies
COPY --chown=$USER:$GROUP docker/input/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# starts flask server app.py - listening for http calls for gui
# starts socket server drx.py - listening for difi packets from device
COPY --chown=$USER:$GROUP docker/input/start.sh start.sh
RUN chmod 700 start.sh
CMD ./start.sh $FLASK_DEPLOY_ENV $USER $GROUP


# syntax=docker/dockerfile:1
