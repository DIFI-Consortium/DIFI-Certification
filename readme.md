<strong><em>DIFI</em></strong>

**DIFI** verification to aid with interoperability of DIFI sources and sinks.

References:  
[DIFI Consortium](https://dificonsortium.org/)  

01 SEPTEMBER 2021
[IEEE difi-announcement](https://ieee-isto.org/press-releases/difi-announcement/)

Digital signal processing (DSP) revolutionized acquisition and reproduction of analog data.  One format for signal data is known as 'digital radio' data when the analog sources convey radio (and intermediate) frequency data it is required corresponding metadata also be communicated.  VITA defines the format for the digital format (packets) for transmission. The VITA 49.2 framework provides many options for packing digital IF data and allows multiple transports. This flexibility requires that an additional layer of documentation be provided in order to explain a manufacturer’s implementation of the standard.  DIFI leverages the flexibility of VITA to specify a subset of the CIF and CIF 0.


This **DIFI** standard provides two independent data flows:   
1. RF input to network output (RF-to-IP) 
2. Network input to RF output (IP-to-RF)

Both VITA and **DIFI** describe the data plane interface with the ability to transmit and receive digitized IF data and corresponding metadata over standard IP networks. DIFI is a specific framework implementation that is meant to interface in alignment with with the VITA 49.2 framework.

Knowledge of related documents is helpful.
___

▪ VITA Radio Transport (VRT) Standard, VITA-49.0 – 2015
▪ VITA Radio Transport (VRT) Standard, VITA-49.2 – 2017



Note: This application can be used as a stand-alone application that decodes and verifies whether packets in a packet stream are in compliance with the DIFI 1.0 standard, and can prepare and send DIFI compliant packets for testing purposes. It is also import-able into your own scripts/applications that can be customized to provide additional functionality not covered in this application. i.e. you can re-use the packet classes and validation functions stand-alone, completely independent of this application, for higher throughput scenario's.

drx.py - receiver that decodes packets
dcs.py - sends 'Standard Context' packet
dvs.py - sends 'Version Context' packet
dds.py - sends 'Data' packet
(all fields in all send packets are user-configurable\changeable into anything that fits application's needs, i.e. there's an arg for every field in the packet)

import drx - to decode packets in byte stream into instances of DifiStandardContextPacket, DifiVersionContextPacket, and DifiDataPacket classes that can be serialized to JSON
import dcs - to send 'Standard Context' packet
import dvs - to send 'Version Context' packet
import dds - to send 'Data' packet


Below are several quick hint examples for reference purposes:

1) To send a 'Version Context Packet' (that's DIFI compliant and is supplying all the fields in the packet):

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

(note:  dvs.py --help)   #will print usage string which has more detail about each arg for 'Version Context' packet
(note:  dcs.py --help)   #will print usage string which has more detail about each arg for 'Standard Context' packet
(note:  dds.py --help)   #will print usage string which has more detail about each arg for 'Data' packet


2) To serialize/decode stream of bytes into DifiVersionContextPacket class instance, and then output instance as JSON string:
(note: use this when you're sure the byte stream contains a 'Version Context' packet inside)

# Python

```

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

```

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


5) To check if packet contents are DIFI compliant (i.e. packet fields after the header):

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




Note: This application starts a UDP socket server that listens for DIFI packets from a device, and starts a Flask server that listens for HTTP requests for API endpoints and GUI. There are three server deployment options for Flask when building the Docker container:

[DEV]
sudo docker build --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=dev difi_one

    (note: will be development flask server, listening on port 5000)

[PROD] (proxy server)
sudo docker build --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod difi_one

    (note: will be uwsgi server hosting flask app, listening on port 5000)

with proxy server:
sudo docker build --build-arg USER=nginx --build-arg GROUP=nginx --build-arg UID=2000 --build-arg GID=2000 --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod difi_one

    (note: will be nginx server proxying to uwsgi server hosting flask app, listening on port configured in nginx conf server block like port 80)

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

[PROD-GATEWAY] (application-gateway)
sudo docker build --build-arg USER=nginx --build-arg GROUP=nginx --build-arg UID=2000 --build-arg GID=2000 --force-rm -f docker/Dockerfile -t difi_one .
sudo docker run -it --net=host -v /tmp:/tmp -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -e FLASK_DEPLOY_ENV=prod-gateway difi_one

    (note: will be nginx server calling through application gateway unix domain socket to uwsgi server hosting flask app, listening on port configured in nginx conf server block like port 80)

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
