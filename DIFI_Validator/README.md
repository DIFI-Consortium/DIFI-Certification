# Intro

This directory contains a **DIFI** validation tool to aid with interoperability of DIFI sources and sinks.  For an introduction to DIFI, please see the [DIFI 101 tutorial](https://github.com/DIFI-Consortium/DIFI-Certification/blob/main/DIFI_101_Tutorial.md).  Note that the official DIFI specification document is located [here](https://dificonsortium.org/standards/) behind an IEEE download/registration page.  DIFI is a specific implementation/subset of the VITA 49.2 framework, and as such, knowledge of VITA 49 is helpful, see VITA Radio Transport (VRT) Standard, VITA-49.2 – 2017.

This DIFI validation tool can be used as a stand-alone application that decodes and verifies whether packets in a packet stream are in compliance with the DIFI 1.0 or 1.1 standard, and can prepare and send DIFI compliant packets for testing purposes. The code consists of several Python modules, which you can import into your own scripts/applications.

The source code is split into the following files:

- drx.py - Receives and decodes packets
- dcs.py - Creates 'Standard Context' packets
- dvs.py - Creates 'Version Context' packets
- dds.py - Creates 'Data' packets
- app.py - Flask REST API/server code that makes a web UI out of the above functions

See the [Docker README](docker/README.md) for instructions on running app.py in a containerized manner.

# Running the Validator Web UI (app.py)

```
cd DIFI_Validator
sudo pip install -r requirements.txt
python app.py
```

Now open a browser to http://127.0.0.1:5000

# MOVE OR DELETE THE FOLLOWING

Below are several quick hint examples for reference purposes:

1) To send a 'Version Context Packet' (that's DIFI compliant illustrating  the fields in the packets as args)

```Python
import dvs
try:
    dvs.DESTINATION_IP = "10.1.1.1"   #it will send this version packet to this destination server address
    dvs.DESTINATION_PORT = 4991
    dvs.STREAM_ID = 1
    dvs.FIELDS["--pkt-type"] = "5"
    dvs.FIELDS["--clsid"] = "1"
    dvs.FIELDS["--rsvd"] = "0"
    dvs.FIELDS["--tsm"] = "1"
    dvs.FIELDS["--tsi"] = "1"
    dvs.FIELDS["--tsf"] = "2"
    dvs.FIELDS["--seqnum"] = "0"
    dvs.FIELDS["--pkt-size"] = "000b"
    dvs.FIELDS["--oui"] = "0012A2"
    dvs.FIELDS["--icc"] = "0001"
    dvs.FIELDS["--pcc"] = "0004"
    dvs.FIELDS["--integer-seconds-ts"] = "1"
    dvs.FIELDS["--fractional-seconds-ts"] = "1"
    dvs.FIELDS["--cif0"] = "80000002"
    dvs.FIELDS["--cif1"] = "0000000C"
    dvs.FIELDS["--v49-spec-version"] = "00000004"
    dvs.FIELDS["--year"] = "22"
    dvs.FIELDS["--day"] = "1"
    dvs.FIELDS["--revision"] = "0"
    dvs.FIELDS["--type"] = "1"
    dvs.FIELDS["--icd-version"] = "0"
    dvs.send_difi_compliant_version_context_packet()
except Exception as e:
    print(e)

```

(note:  dvs.py --help)   
print usage string which has more detail about each arg for 'Version Context' packet

(note:  dcs.py --help)   
print usage string which has more detail about each arg for 'Standard Context' packet

(note:  dds.py --help)   
print usage string which has more detail about each arg for 'Data' packet


2) To serialize/decode stream of bytes into DifiVersionContextPacket class instance, and then output instance as JSON string:
(note: use this when you're sure the byte stream contains a 'Version Context' packet inside)

```Python
import drx
import io
try:
    drx.DEBUG = False
    drx.VERBOSE = False

    b = bytearray(b'<put full packet byte data here>')
    stream = io.BytesIO(b)

    pkt = drx.DifiVersionContextPacket(stream)  #simply feed the byte stream into constructor, that's it.
    print(pkt)
    print(pkt.to_json())
    print(pkt.to_json(hex_values=True))

except drx.NoncompliantDifiPacket as e:
    print("error: ", e.message)
    print("--> not DIFI compliant, packet not decoded:\r\n%s" % e.difi_info.to_json())
except Exception as e:
    print("error: ", e)

```


3) To serialize/decode stream of bytes into DifiVersionContextPacket class instance, and then output instance as JSON string:
(note: use this when you're not sure which type of DIFI packet the byte stream contains inside, it's using the same main decode function this application uses internally)

```Python

import drx
try:
    drx.DEBUG = False
    drx.VERBOSE = False

    stream = io.BytesIO()
    b = bytearray(b'<put full packet byte data here>')
    stream.write(b)
    stream.seek(0)

    pkt = drx.decode_difi_vrt_packet(stream)  #simply feed the byte stream into the main decode function, that's it.
    print(type(pkt).__name__)
    print(pkt)
    print(pkt.to_json())

except drx.NoncompliantDifiPacket as e:
    print("error: ", e.message)
    print("--> not DIFI compliant, packet not decoded:\r\n%s" % e.difi_info.to_json())
except Exception as e:
    print("error: ", e)

```

4) To check if header in packet is DIFI compliant:

```Python
import drx
try:
    pkt = drx.DifiVersionContextPacket
    
    if pkt.is_difi10_version_context_packet_header(pkt,
        packet_type=drx.DIFI_VERSION_FLOW_SIGNAL_CONTEXT,
        class_id=drx.DIFI_CLASSID,
        rsvd=drx.DIFI_RESERVED,
        tsm=drx.DIFI_TSM_GENERAL_TIMING,
        tsf=drx.DIFI_TSF_REALTIME_PICOSECONDS,
        packet_size=drx.DIFI_VERSION_FLOW_SIGNAL_CONTEXT_SIZE) is True:

        print("valid...")
    else:
        print("not valid...")

except Exception as e:
    print("error: ", e)
```

5) To check if packet contents are DIFI compliant (i.e. packet fields after the header):
```Python
import drx
try:
    pkt = drx.DifiVersionContextPacket
    
    if pkt.is_difi10_version_context_packet(pkt,
        icc=drx.DIFI_INFORMATION_CLASS_CODE_VERSION_FLOW_CONTEXT,
        pcc=drx.DIFI_PACKET_CLASS_CODE_VERSION_FLOW_CONTEXT,
        cif0=drx.DIFI_CONTEXT_INDICATOR_FIELD_0_VERSION_FLOW_CONTEXT,
        cif1=drx.DIFI_CONTEXT_INDICATOR_FIELD_1_VERSION_FLOW_CONTEXT,
        v49_spec=drx.DIFI_V49_SPEC_VERSION_VERSION_FLOW_CONTEXT) is True:

        print("valid...")
    else:
        print("not valid...")

except Exception as e:
    print("error: ", e)
```



Note: This application starts a UDP socket server that listens for DIFI packets from a device, and starts a Flask server that listens for HTTP requests for API endpoints and GUI. There are three server deployment options for Flask when building the Docker container:

1. Using Flask's built-in dev server, this is the simplest but not meant for production
2. Using a uWSGI server that runs the Flask app
3. Using a NGINX server proxying to the uWSGI server hosting flask app

```bash
[DEV]
sudo docker build --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=dev difi_one
```

(note: will be development flask server, listening on port 5000)

```bash
[PROD] (proxy server)
sudo docker build --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod difi_one
```

(note: will be uwsgi server hosting flask app, listening on port 5000)

with proxy server:
```bash
sudo docker build --build-arg USER=nginx --build-arg GROUP=nginx --build-arg UID=2000 --build-arg GID=2000 --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod difi_one
```

(note: will be nginx server proxying to uwsgi server hosting flask app, listening on port configured in nginx conf server block like port 80)

```
    example nginx server block:
    server {
        listen 80;
        server_name 10.1.1.1;

            client_max_body_size 64M;
            charset utf-8;
            error_log /etc/nginx/error.log;
            access_log /etc/nginx/access.log;

            location / {
                include proxy_params;
                proxy_pass http://10.1.1.1:5000;  #url to uwsgi/flask server
            }
    }
```

[PROD-GATEWAY] (application-gateway)
```bash
sudo docker build --build-arg USER=nginx --build-arg GROUP=nginx --build-arg UID=2000 --build-arg GID=2000 --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -v /tmp:/tmp -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod-gateway difi_one
```

(note: will be nginx server calling through application gateway unix domain socket to uwsgi server hosting flask app, listening on port configured in nginx conf server block like port 80)

```
    example nginx server block:
    server {
        listen 80;
        server_name 10.1.1.1;

            client_max_body_size 64M;
            charset utf-8;
            error_log /etc/nginx/error.log;
            access_log /etc/nginx/access.log;

            location / {
                include uwsgi_params;
                uwsgi_pass unix:/tmp/difi.sock;  #path to unix socket
            }
    }
```