# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT
# How to build and run docker image
## Build  (Note the period . at the end)

```bash
cd to difi:

sudo docker build --force-rm -f docker/Dockerfile -t difi .
```
OR not cached:
```bash
sudo docker build --no-cache --force-rm -f docker/Dockerfile -t difi .
```

There are three server deployment options for the flask server when building the docker container:

[DEV]
```bash
sudo docker build --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=dev difi_one
```
(note: will be development flask server, listening on port 5000)

[PROD] (proxy server)
```bash
sudo docker build --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod difi_one
```
(note: will be uwsgi server hosting flask app, listening on port 5000)

OR with proxy server:

```bash
sudo docker build --build-arg USER=nginx --build-arg GROUP=nginx --build-arg UID=2000 --build-arg GID=2000 --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod difi_one
```

(note: will be nginx server proxying to uwsgi server hosting flask app, listening on port configured in nginx conf server block like port 80)

[PROD-GATEWAY] (application-gateway)
```bash
sudo docker build --build-arg USER=nginx --build-arg GROUP=nginx --build-arg UID=2000 --build-arg GID=2000 --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -v /tmp:/tmp -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod-gateway difi_one
```

(note: will be nginx server calling through application gateway unix domain socket to uwsgi server hosting flask app, listening on port configured in nginx conf server block like port 80)

Note: this is how to add user on HOST machine to run nginx server under, then pass this new user in as USER/GROUP/UID/GID build args to the build command when building docker container, this will create that same user inside the docker container when it builds so when run container and /tmp volume maps, /tmp/difi.sock will have owner of nginx/nginx on both HOST and CONTAINER:
          
```bash
sudo addgroup -gid 2000 nginx
sudo adduser --system --home /var/www --uid 2000 --gid 2000 --disabled-login nginx
```

    When debugging and testing flask server running in 'application gateway' server option mode:

      'curl' doesn't work, because curl sends 'http' protocol packets to the unix socket (/tmp/difi.sock) that is expecting 'uwsgi' protocol packets:
```bash
        sudo curl -verbose --unix-socket /tmp/difi.sock http://10.1.1.1/api/v1/difi/help/api
```
        (note: it does work if you change the uwsgi server start parameter from '--socket /tmp/difi.sock \' to '--http-socket /tmp/difi.sock \',
        so it will change the underlying protocol from 'uwsgi' to 'http' protocol)

      'uwsgi_curl' works, because sends 'uwsgi' protocol packets:
```bash
        sudo pip install uwsgi-tools
        sudo uwsgi_curl /tmp/difi.sock http://10.1.1.1/api/v1/difi/help/api
        sudo pip uninstall uwsgi-tools
```

      'socat' to listen to nginx calls sent from the browser to the uwsgi server, acting as though we're taking the place of the uwsgi server:
```bash
        sudo apt install socat
        sudo socat UNIX-LISTEN:/tmp/difi.sock,fork,reuseaddr,unlink-early,user=www-data,group=www-data,mode=777 -
        sudo apt remove socat
```

(note: make sure to turn off uwsgi server running in docker container before starting socat, then run socat and call from browser)

## Save
To save the built docker container image as .tar.gz package:
```bash
sudo docker save difi|gzip > difi.tar.gz
```
(note: to see list of built images run: sudo docker images)

## Run
To run in console and write output to console:
```bash
sudo docker run --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -i -t difi
```
OR:
```bash
sudo docker run --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=asyncio -i -t difi
```
To run as daemon:
```bash
sudo docker run -d --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -i -t difi
```
To run in production (should add the restart on failure param):
```bash
sudo docker run -d --net=host --restart=on-failure -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -i -t difi
```
To run in each of the three server deployment options:

 [DEV]
 ```bash
 sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=dev difi_one
 ```
 (note: will be development flask server, listening on port 5000)

 [PROD] (proxy server)
 ```bash
 sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod difi_one
 ```
 (note: will be uwsgi server hosting flask app, listening on port 5000)
 OR with proxy server:
 (note: will be nginx server proxying to uwsgi server hosting flask app, listening on port configured in nginx conf server block like port 80)
 
 [PROD-GATEWAY] (application-gateway)
 ```bash
 sudo docker run -it --net=host -v /tmp:/tmp -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e 
 ```
 FLASK_DEPLOY_ENV=prod-gateway difi_one
 (note: will be nginx server calling through application gateway unix domain socket to uwsgi server hosting flask app, listening on port configured in nginx conf server block like port 80)

To look at console output inside docker container at runtime (i.e. at the cmd prompt inside container):
```bash
sudo docker ps  (to get container id)
sudo docker exec -it $DOCKER_ID /bin/sh  (to get cmd prompt inside container)
```
To see container's user account and environment variables:
```bash
sudo docker images  (to get container image id)
sudo docker inspect $IMAGE_ID
```

Note: docker run is equivalent to the API 
/containers/create 
/containers/(id)/start

<p>
The value in the REPOSITORY data is shown with the -t flag of the docker build command.
Docker tags can also be applied post build to an existing image. 
Tag images can use any nomenclature, but,
Docker will: 
    Use the tag as the registry location in a docker push or docker pull

Full form of a tag :
  [REGISTRYHOST/][USERNAME/]NAME[:TAG]. 
  
ubuntu example , REGISTRYHOST is inferred to be  
registry.hub.docker.com 
So if you plan on storing your image called difi_app in a registry at docker.example.com, that image docker.example.com/difi_app.   
The TAG column is just the [:TAG] part of the full tag. 

FULL TAG Syntax
    [REGISTRYHOST/][USERNAME/]NAME[:TAG]
And the TAG column displays the last part of the full tag.

