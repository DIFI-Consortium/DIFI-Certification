#!/bin/sh

# Copyright (C) 2022 Kratos Technology & Training Solutions, Inc.

# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

#set -e


# start difi receiver server
python3 drx.py &


#start flask server (in one of threee modes: dev, prod (proxy), prod-gateway)
#echo $1 #FLASK_DEPLOY_ENV
#echo $2 #USER
#echo $3 #GROUP
if [ $1 = "prod-gateway" ]; then

    #echo "running 'prod-gateway' uwsgi flask server -> application gateway mode (unix domain file system socket)"

    # runs flask inside uwsgi server (like in a production environment) that basically makes flask app only visible as a unix socket
    # (essentially all the flask endpoints can no longer be called directly, but now have to be called by an application gateway server like nginx listening on public port 80 that passes the http requests through to flask on the unix socket as uwsgi protocol)
    # (important!!! must supply build args on the container's 'build' command that change the default USER/GROUP/UID/GID to the user account
    # the 'application gateway' server like nginx is running under, or nginx will not have permission to talk to the unix socket and the server will not function properly)
    uwsgi --socket /tmp/difi.sock \
    --chmod-socket=600 \
    --chown-socket=$2:$3 \
    --mount /=app:app \
    --uid=$2 \
    --gid=$3 \
    --master \
    --processes=5 \
    --manage-script-name \
    --vacuum \
    --die-on-term

    # to make underlying protocol for unix socket = http protocol
    #--http-socket /tmp/difi.sock \

    # to make underlying protocol for unix socket = uwsgi protocol
    #--socket /tmp/difi.sock \

    # to change buffer size, default buffer size is 4096
    #--buffer-size=65536 \

    # can also use number for user/group
    # note: be careful when doing so because the container's difi.sock file will end up being owned by the container's user 33
    # (which is the 'xfs' user that came with the container's FROM image in this case),
    # while the host's difi.sock file will end up being owned by the host's user 33
    # (which ends up being the 'www-data' user installed by nginx on the host in this case)
    # --chown-socket=33:33 \
    # which will require less secure permissions because you have to give the 'everyone else' 3rd digit a 6 instead of 0 to operate properly
    # --chmod-socket=606 \

elif [ $1 = "prod" ]; then

    #echo "running 'prod' uwsgi flask server -> production mode / http proxy server mode"

    # runs flask inside uwsgi server (like in a production environment) that listens on internal port 5000,
    # and can also use a proxy server like nginx listening on public port 80 to proxy/pass http protocol requests through to it
    # ('--http-socket 0.0.0.0:5000' arg has http on front to switch to talk http protocol instead of uwsgi protocol and to listen on an ip socket (not unix domain socket) because of ip address)
    # (essentially all the flask endpoints can now be called on an internal port 5000, or by calling the endpoint in a proxy server like nginx listening on public port 80 that will proxy/pass http protocol request through to flask)
    uwsgi --http-socket 0.0.0.0:5000 \
    --chmod-socket=600 \
    --chown-socket=$2:$3 \
    --mount /=app:app \
    --uid=$2 \
    --gid=$3 \
    --master \
    --processes=5 \
    --manage-script-name \
    --vacuum \
    --die-on-term

else
    #echo "running default 'dev' flask server"

    flask run &   #if run this way it will use the flask environment variables in the Dockerfile to run the flask server
    #python3 app.py &   #if run this way it will use the settings in the "if __name__ == '__main__':" block at bottom of app.py file to run the flask server
fi



# To debug and test flask server running in 'application gateway' server option mode::
#
# 'curl' doesn't work, because curl sends 'http' protocol packets to the unix socket (/tmp/difi.sock) that is expecting 'uwsgi' protocol packets:
#   sudo curl -verbose --unix-socket /tmp/difi.sock http://10.1.1.1/api/v1/difi/help/api
#   (note: it does work if you change the uwsgi server start parameter from '--socket /tmp/difi.sock \' to '--http-socket /tmp/difi.sock \',
#   so it will change the underlying protocol from 'uwsgi' to 'http' protocol)
#
# 'uwsgi_curl' works, because sends 'uwsgi' protocol packets:
#   sudo pip install uwsgi-tools
#   sudo uwsgi_curl /tmp/difi.sock http://10.1.1.1/api/v1/difi/help/api
#   sudo pip uninstall uwsgi-tools
#
# 'socat' to listen to nginx calls sent from the browser to the uwsgi server, acting as though we're taking the place of the uwsgi server:
#   sudo apt install socat
#   sudo socat UNIX-LISTEN:/tmp/difi.sock,fork,reuseaddr,unlink-early,user=www-data,group=www-data,mode=777 -
#   sudo apt remove socat
#   (note: make sure to turn off uwsgi server running in docker container before starting socat, then run socat and call from browser)



wait -n
