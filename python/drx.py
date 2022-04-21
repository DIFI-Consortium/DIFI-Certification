"""
# Copyright (C) 2022 Kratos Technology & Training Solutions, Inc.
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

# drx.py
#
# Script that runs as socket server listening on port for DIFI packets being sent from a device.
#
# (Supports: DIFI 1.0 spec - "IEEE-ISTO Std4900-2021: Digital IF Interoperability Standard Version 1.0 August 18,2021")
#
# Currently can run in three modes:
# 1) 'socket' -regular socket server listening (default if not supplied)
# 2) 'asyncio' -asyncio socket server listening
# 3) 'pcap' -pcap file decoder (this mode currently disabled)
#
# Can also supply port. (defaults to 4991 if not supplied)
#
# IP address automatically defaults to local machine's IP.
#   ->if '--net=host' supplied in docker run command:
#      -will be IP of host machine that's hosting docker container
#   ->if '--net=host' NOT supplied in docker run command:
#      -will be IP assigned to docker container when it started
#
#   [Example] docker run --net=host -i -t difi_one
#
#
# Was designed to run inside docker container as a VNF.
# [Example] docker build --no-cache --force-rm -f /sdk/DIFI/docker/Dockerfile -t difi_one .
#
# [Example] docker run --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=socket -i -t difi_one
# [Example] docker run --net=host -e DIFI_RX_PORT=4991 -e DIFI_RX_MODE=asyncio -i -t difi_one
#
# Can also be run as standalone script for troubleshooting purposes.
# [Example] python3 drx.py   (defaults to: port 4991, socket mode, verbose, save last good packet)
# [Example] python3 drx.py --port 4991
# [Example] python3 drx.py --port 4991 --mode asyncio
# [Example] python3 drx.py --port 4991 --mode socket --verbose True --debug True
#
# Saves results to files of whether packets received
# from device are DIFI compliant. Results in the files
# can then be retrieved via:
# 1) Flask server rest endpoints as the public API.
#     To get for 1 stream id:
#     [Example] http://<machine>:5000/api/v1/difi/compliant/standardcontext/00000001
#     [Example] http://<machine>:5000/api/v1/difi/compliant/versioncontext/00000001
#     [Example] http://<machine>:5000/api/v1/difi/compliant/data/00000001
#     [Example] http://<machine>:5000/api/v1/difi/compliant/count/00000001
#     [Example] http://<machine>:5000/api/v1/difi/noncompliant/00000001
#     [Example] http://<machine>:5000/api/v1/difi/noncompliant/count/00000001
#     To get list of all available stream id's:
#     [Example] http://<machine>:5000/api/v1/difi/compliant
#     [Example] http://<machine>:5000/api/v1/difi/noncompliant
#
# 2) Flask server web interface endpoints as html gui's.
#     [Example] http://<machine>:5000/web/v1/difi/compliant/standardcontext/00000001
#     [Example] http://<machine>:5000/web/v1/difi/compliant/versioncontext/00000001
#     [Example] http://<machine>:5000/web/v1/difi/compliant/data/00000001
#     [Example] http://<machine>:5000/web/v1/difi/compliant/count/00000001
#     [Example] http://<machine>:5000/web/v1/difi/noncompliant/00000001
#     [Example] http://<machine>:5000/web/v1/difi/noncompliant/count/00000001
#     [Example] http://<machine>:5000/web/v1/difi/help/api
#
# 3) tail command locally in console on any one of the result files.
#     [Example] tail -f difi-compliant-standard-context-00000001.dat
#     [Example] tail -f difi-compliant-standard-context-00000001.dat 2> >(grep -v truncated >&2)
#
#    (note: 00000001 is stream id)
#
# To look at drx.py output result files inside docker container
# at runtime (i.e. at the cmd prompt inside container):
# docker ps  (to get container id)
# docker exec -it 3f650613bf36 /bin/sh  (to get cmd prompt inside container)
#
# Can also import into other projects:
# [Example]
# import drx
# import sys
# import io
# from io import BytesIO
# try:
#     s = io.BytesIO()
#
#     #write a good packet header
#     #s.write((1231028251).to_bytes(4, byteorder='big'))
#     #s.write((3).to_bytes(4, byteorder='big'))
#     #s.seek(0)
#
#     #write a bad packet header
#     #s.write((1096810523).to_bytes(4, byteorder='big'))
#     #s.write((3).to_bytes(4, byteorder='big'))
#     #s.seek(0)
#
#     #write a good full data packet
#     #b = bytearray(b'<put full packet byte data here>')
#     #s.write(b)
#     #s.seek(0)
#
#     #decode the packet
#     #pkt = drx.decode_difi_vrt_packet(s)
#     #print(type(pkt).__name__)
#     #print(pkt)
#
#     #check if a packet header is valid
#     pkt = drx.DifiStandardContextPacket
#     #if pkt.is_difi10_standard_context_packet_header(pkt, packet_type=1, class_id=1, rsvd=0, tsm=1, tsf=2, packet_size=27) is True:
#     if pkt.is_difi10_standard_context_packet_header(pkt,
#         packet_type=drx.DIFI_STANDARD_FLOW_SIGNAL_CONTEXT,
#         class_id=drx.DIFI_CLASSID,
#         rsvd=drx.DIFI_RESERVED,
#         tsm=drx.DIFI_TSM_GENERAL_TIMING,
#         tsf=drx.DIFI_TSF_REALTIME_PICOSECONDS,
#         packet_size=drx.DIFI_STANDARD_FLOW_SIGNAL_CONTEXT_SIZE) is True:
#         print("valid...")
#     else:
#         print("not valid...")
#
#     #create a packet instance
#     #drx.DEBUG = False
#     #drx.VERBOSE = False
#     #drx.SAVE_LAST_GOOD_PACKET = False
#     #b = bytearray(b'<put full packet byte data here>')
#     #stream = io.BytesIO(b)
#     #pkt = drx.DifiDataPacket(stream)
#     #print(pkt)
#     #print(pkt.to_json())
#     #print(pkt.to_json(hex_values=True))
#
#     #delete any output files
#     #drx.delete_all_difi_files()
#
# except drx.NoncompliantDifiPacket as e:
#     print("error: ", e.message)
#     print("--> not DIFI compliant, packet not decoded:\r\n%s" % e.difi_info.to_json())
# except Exception as e:
#     print("error: ", e)
# sys.exit(2)
"""

#from pypacker import ppcap
#from pypacker.pypacker import byte2hex
#from pypacker.layer12 import ethernet
#from pypacker.layer3 import ip
#from pypacker.layer4 import tcp
#from pypacker.layer4 import udp

#takes care of forward declaration problem for type hints/annotations
#(so don't have to put quotes around types)
from __future__ import annotations
from typing import Union

#from time import  perf_counter, sleep
from datetime import timezone, datetime

import asyncio

import struct
import io
from io import BytesIO
#from io import BufferedReader

#import array
import sys
import json
#import numpy as np
#import pickle
import pprint
import socket
import getopt
import os
import threading


##########
#settings
##########
VERBOSE = True  #prints fully decoded packets to console
DEBUG = False  #prints packet data and additional debugging info to console
SAVE_LAST_GOOD_PACKET = True  #saves last decoded 'compliant' packet to file
JSON_AS_HEX = False  #converts applicable int fields in json doc to hex strings
SHOW_PKTS_PER_SEC = False  #outputs estimated packets p/sec to console for debugging purposes

DIFI_RECEIVER_ADDRESS = "0.0.0.0" #default
DIFI_RECEIVER_PORT = 4991 #default
#assign new port if passed in on docker run command
if os.getenv("DIFI_RX_PORT"):
    DIFI_RECEIVER_PORT = int(os.getenv("DIFI_RX_PORT"))
#assign address from docker container's ENV value
if os.getenv("DIFI_RX_HOST"):
    DIFI_RECEIVER_ADDRESS = os.getenv("DIFI_RX_HOST")

#modes
MODE_SOCKET = "socket"
MODE_ASYNCIO = "asyncio"
#MODE_PCAP = "pcap"
MODE = MODE_SOCKET #default
#assign new mode if passed in on docker run command
if os.getenv("DIFI_RX_MODE"):
    MODE = os.getenv("DIFI_RX_MODE")

#pcap mode is currently disabled
#PCAP_FILE = "difi-compliant.pcap"


###########
#DIFI constants
###########

#DIFI packet types
DIFI_STANDARD_FLOW_SIGNAL_CONTEXT = 0x4 #(DIF must be this)
DIFI_STANDARD_FLOW_SIGNAL_CONTEXT_SIZE = 27 #(DIFI must be this)
DIFI_VERSION_FLOW_SIGNAL_CONTEXT = 0x5 #(DIFI must be this)
DIFI_VERSION_FLOW_SIGNAL_CONTEXT_SIZE = 11 #(DIFI must be this)
DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID = 0x1 #(DIFI must be this)
DIFI_STANDARD_FLOW_SIGNAL_DATA_NO_STREAMID = 0x0

#class id
DIFI_CLASSID = 0x1 #01 (DIFI must be this)

#reserved
DIFI_RESERVED = 0x0 #00 (DIFI must be this)

#tsm - data packets
DIFI_TSM_DATA = 0x0 #00 (DIFI must be this)
#tsm - standard context / version context
DIFI_TSM_GENERAL_TIMING = 0x1 #01 (DIFI must be this)

#tsi
DIFI_TSI_NONE = 0x0  #00
DIFI_TSI_UTC = 0x1   #01 (default, but can be any)
DIFI_TSI_GPS = 0x2   #10
DIFI_TSI_OTHER = 0x3 #11

#tsf
DIFI_TSF_NONE = 0x0 #00
DIFI_TSF_SAMPLE_COUNT = 0x1 #01
DIFI_TSF_REALTIME_PICOSECONDS = 0x2 #10 (DIFI must be this)
DIFI_TSF_FREE_RUNNING_COUNT = 0x3 #11

#icc/pcc - version context
DIFI_INFORMATION_CLASS_CODE_VERSION_FLOW_CONTEXT = 0x1 #(DIFI must be this)
DIFI_PACKET_CLASS_CODE_VERSION_FLOW_CONTEXT = 0x4 #(DIFI must be this)

#cif0/cif1 - standard context
DIFI_CONTEXT_INDICATOR_FIELD_STANDARD_FLOW_CONTEXT = 0xBB98000 #(DIFI must be this, which is ignoring 1st nibble)
#cif0/cif1 - version context
DIFI_CONTEXT_INDICATOR_FIELD_0_VERSION_FLOW_CONTEXT = 0x0000002 #(DIFI must be this, which is ignoring 1st nibble)
DIFI_CONTEXT_INDICATOR_FIELD_1_VERSION_FLOW_CONTEXT = 0x0000000C #(DIFI must be this)

#v49 spec - version context
DIFI_V49_SPEC_VERSION_VERSION_FLOW_CONTEXT = 0x00000004 #(DIFI must be this)

#not required for DIFI anymore
#DIFI_REFERENCE_POINT = 0x00000064 #(DIFI must be this)

#state/event indicators - standard context
DIFI_STATE_EVENT_IND_FREQ_REF_LOCK_BIT = (1 << 17)
DIFI_STATE_EVENT_IND_CALIBRATED_TIME_BIT = (1 << 19)

#data packet payload format field - standard context
DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_PACKING_METHOD = 1 #(DIFI must be this)
DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_REAL_COMPLEX_TYPE = 1 #(DIFI must be this)
DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_DATA_ITEM_FORMAT = 0 #(DIFI must be this)
DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_SAMPLE_COMPONENT_REPEAT_IND = 0 #(DIFI must be this)
DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_EVENT_TAG_SIZE = 0 #(DIFI must be this)
DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_CHANNEL_TAG_SIZE = 0 #(DIFI must be this)

#protocol
UDP_PROTO = b'\x11' #(DIFI must be this)

#output files
DIFI_NONCOMPLIANT_FILE_PREFIX = "difi-noncompliant-"
DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX = "difi-noncompliant-count-"

DIFI_COMPLIANT_FILE_PREFIX = "difi-compliant-"
DIFI_STANDARD_CONTEXT = "standard-context-"
DIFI_VERSION_CONTEXT = "version-context-"
DIFI_DATA = "data-"
DIFI_COMPLIANT_COUNT_FILE_PREFIX = "difi-compliant-count-"

DIFI_FILE_EXTENSION = ".dat"


###################
#packet error types
###################
class InvalidDataReceived(Exception):
    pass

class InvalidPacketType(Exception):
    pass

class NoncompliantDifiPacket(Exception):
    def __init__(self, message, difi_info: DifiInfo=None):
        super().__init__()
        self.message = message
        self.difi_info = difi_info

    def __str__(self):
        return str(self.message)


###################
#command-line args error types
###################
class InvalidArgs(Exception):
    pass


###############
#write to files
###############
def truncate_all_difi_files():

    try:
        with os.scandir() as directory:
            for entry in directory:
                if entry.is_file():
                    if entry.name.startswith(DIFI_COMPLIANT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        os.truncate(entry.path, 0)
                    elif entry.name.startswith(DIFI_NONCOMPLIANT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        os.truncate(entry.path, 0)
    except Exception as e:
        print("error truncating DIFI output files -->")
        pprint.pprint(e)

    if DEBUG: print("truncated all difi output files...")


def delete_all_difi_files():

    try:
        with os.scandir() as directory:
            for entry in directory:
                if entry.is_file():
                    if entry.name.startswith(DIFI_COMPLIANT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        os.remove(entry.path)
                    elif entry.name.startswith(DIFI_NONCOMPLIANT_FILE_PREFIX) and entry.name.endswith(DIFI_FILE_EXTENSION):
                        os.remove(entry.path)
    except Exception as e:
        print("error deleting DIFI output files -->")
        pprint.pprint(e)

    if DEBUG: print("deleted all difi output files...")


def write_noncompliant_to_file(e: NoncompliantDifiPacket):

    #TODO: in the future switch to write to kafka or database here instead...

    try:
        if type(e.difi_info.stream_id) is str:
            fname = "%s%s%s" % (DIFI_NONCOMPLIANT_FILE_PREFIX, e.difi_info.stream_id, DIFI_FILE_EXTENSION)
        else:
            fname = "%s%08x%s" % (DIFI_NONCOMPLIANT_FILE_PREFIX, e.difi_info.stream_id, DIFI_FILE_EXTENSION)

        with open(fname, 'w', encoding="utf-8") as f:

            #last_modified = datetime.fromtimestamp(os.stat(fname).st_mtime, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')

            #add date timestamp to difi info object before writing to file
            now = datetime.now(timezone.utc).strftime("%m/%d/%Y %r %Z")
            setattr(e.difi_info, "archive_date", now)

            f.write(e.difi_info.to_json()+"\r\n")
    except Exception:
        print("error writing to non-compliant file [%s] -->" % fname)
        pprint.pprint(e)

    if DEBUG: print("added entry to '%s' [%s]\r\n%s" % (fname, e, e.difi_info.to_json()))


def write_noncompliant_count_to_file(stream_id: Union[int,str]):

    #TODO: in the future switch to write to kafka or database here instead...

    try:
        if type(stream_id) is str:
            fname = "%s%s%s" % (DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX, stream_id, DIFI_FILE_EXTENSION)
        else:
            fname = "%s%08x%s" % (DIFI_NONCOMPLIANT_COUNT_FILE_PREFIX, stream_id, DIFI_FILE_EXTENSION)
        with open(fname, 'a+', encoding="utf-8") as f:
            f.seek(0)
            c = 0
            buf = f.read()
            if buf:
                entry = buf.split("#", 1)
                c = int(entry[0])
            c = c + 1
            #add date timestamp when writing to file
            now = datetime.now(timezone.utc).strftime("%m/%d/%Y %r %Z")
            out = "%s#%s" % (str(c), now)
            f.seek(0)
            f.truncate()
            f.write(out)
    except Exception as e:
        print("error writing to non-compliant count file [%s] -->" % fname)
        pprint.pprint(e)

    if DEBUG: print("incremented entry in '%s'.\r\n" % (fname))


def write_compliant_to_file(packet: Union[DifiStandardContextPacket,DifiVersionContextPacket,DifiDataPacket]):

    if type(packet) not in (DifiStandardContextPacket, DifiVersionContextPacket, DifiDataPacket):
        print("packet type '%s' not allowed.\r\n" % (type(packet).__name__))
        return

    #TODO: in the future switch to write to kafka or database here instead...

    try:
        if type(packet) is DifiStandardContextPacket:
            fname = "%s%s%08x%s" % (DIFI_COMPLIANT_FILE_PREFIX, DIFI_STANDARD_CONTEXT, packet.stream_id, DIFI_FILE_EXTENSION)
        elif type(packet) is DifiVersionContextPacket:
            fname = "%s%s%08x%s" % (DIFI_COMPLIANT_FILE_PREFIX, DIFI_VERSION_CONTEXT, packet.stream_id, DIFI_FILE_EXTENSION)
        elif type(packet) is DifiDataPacket:
            fname = "%s%s%08x%s" % (DIFI_COMPLIANT_FILE_PREFIX, DIFI_DATA, packet.stream_id, DIFI_FILE_EXTENSION)
        else:
            raise Exception("context packet type unknown")

        with open(fname, 'w', encoding="utf-8") as f:

            #add date timestamp to packet object before writing to file
            now = datetime.now(timezone.utc).strftime("%m/%d/%Y %r %Z")
            setattr(packet, "archive_date", now)

            f.write(packet.to_json(JSON_AS_HEX)+"\r\n")
    except Exception as e:
        print("error writing to compliant file [%s] -->" % fname)
        pprint.pprint(e)

    if DEBUG: print("added last decoded '%s' to '%s'.\r\n" % (type(packet).__name__, fname))


def write_compliant_count_to_file(stream_id: int):

    #TODO: in the future switch to write to kafka or database here instead...

    try:
        fname = "%s%08x%s" % (DIFI_COMPLIANT_COUNT_FILE_PREFIX, stream_id, DIFI_FILE_EXTENSION)
        with open(fname, 'a+', encoding="utf-8") as f:
            f.seek(0)
            c = 0
            buf = f.read()
            if buf:
                entry = buf.split("#", 1)
                c = int(entry[0])
            c = c + 1
            #add date timestamp when writing to file
            now = datetime.now(timezone.utc).strftime("%m/%d/%Y %r %Z")
            out = "%s#%s" % (str(c), now)
            f.seek(0)
            f.truncate()
            f.write(out)
    except Exception as e:
        print("error writing to compliant file [%s] -->" % fname)
        pprint.pprint(e)

    if DEBUG: print("incremented entry in '%s'.\r\n" % (fname))



############
#class used to store non-compliance info for DIFI custom non-compliant exception and to write json object of info out to file
############
class DifiInfo():
    def __init__(self, packet_type:int, stream_id:int=None, packet_size=None, class_id=None, reserved=None, tsm=None, tsf=None, icc=None, pcc=None, cif0=None, cif1=None, v49_spec=None, data_payload_fmt_pk_mh=None, data_payload_fmt_real_cmp_type=None, data_payload_fmt_data_item_fmt=None, data_payload_fmt_rpt_ind=None, data_payload_fmt_event_tag_size=None, data_payload_fmt_channel_tag_size=None):

        #################
        #standard context
        #################
        if packet_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT:
            #stream id
            if stream_id is not None:
                self.stream_id = stream_id
            else:
                self.stream_id = "no-stream-id"
            #header
            self.packet_type = ("0x%1x" % packet_type)
            self.packet_type_display =  (("must be: 0x%1x, 0x%1x, 0x%1x -> was: 0x%1x" % (DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID, packet_type)), True)
            if packet_size is not None: self.packet_size = (("must be: %d -> was: %d" % (DIFI_STANDARD_FLOW_SIGNAL_CONTEXT_SIZE, packet_size)), DIFI_STANDARD_FLOW_SIGNAL_CONTEXT_SIZE==packet_size)
            if class_id is not None: self.class_id = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_CLASSID, class_id)), DIFI_CLASSID==class_id)
            if reserved is not None: self.reserved = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_RESERVED, reserved)), DIFI_RESERVED==reserved)
            if tsm is not None: self.tsm = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSM_GENERAL_TIMING, tsm)), DIFI_TSM_GENERAL_TIMING==tsm)
            if tsf is not None: self.tsf = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSF_REALTIME_PICOSECONDS, tsf)), DIFI_TSF_REALTIME_PICOSECONDS==tsf)
            #packet
            if cif0 is not None: self.context_indicator_field_0 = (("must be: 0x%07x -> was: 0x%07x" % (DIFI_CONTEXT_INDICATOR_FIELD_STANDARD_FLOW_CONTEXT, cif0)), DIFI_CONTEXT_INDICATOR_FIELD_STANDARD_FLOW_CONTEXT==cif0)
            if data_payload_fmt_pk_mh is not None: self.data_packet_payload_format_packing_method = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_PACKING_METHOD, data_payload_fmt_pk_mh)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_PACKING_METHOD==data_payload_fmt_pk_mh)
            if data_payload_fmt_real_cmp_type is not None: self.data_packet_payload_format_real_complex_type = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_REAL_COMPLEX_TYPE, data_payload_fmt_real_cmp_type)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_REAL_COMPLEX_TYPE==data_payload_fmt_real_cmp_type)
            if data_payload_fmt_data_item_fmt is not None: self.data_packet_payload_format_data_item_format = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_DATA_ITEM_FORMAT, data_payload_fmt_data_item_fmt)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_DATA_ITEM_FORMAT==data_payload_fmt_data_item_fmt)
            if data_payload_fmt_rpt_ind is not None: self.data_packet_payload_format_repeat_indicator = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_SAMPLE_COMPONENT_REPEAT_IND, data_payload_fmt_rpt_ind)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_SAMPLE_COMPONENT_REPEAT_IND==data_payload_fmt_rpt_ind)
            if data_payload_fmt_event_tag_size is not None: self.data_packet_payload_format_event_tag_size = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_EVENT_TAG_SIZE, data_payload_fmt_event_tag_size)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_EVENT_TAG_SIZE==data_payload_fmt_event_tag_size)
            if data_payload_fmt_channel_tag_size is not None: self.data_packet_payload_format_channel_tag_size = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_CHANNEL_TAG_SIZE, data_payload_fmt_channel_tag_size)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_CHANNEL_TAG_SIZE==data_payload_fmt_channel_tag_size)

        ################
        #version context
        ################
        elif packet_type == DIFI_VERSION_FLOW_SIGNAL_CONTEXT:
            #stream id
            if stream_id is not None:
                self.stream_id = stream_id
            else:
                self.stream_id = "no-stream-id"
            #header
            self.packet_type = ("0x%1x" % packet_type)
            self.packet_type_display =  (("must be: 0x%1x, 0x%1x, 0x%1x -> was: 0x%1x" % (DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID, packet_type)), True)
            if packet_size is not None: self.packet_size = (("must be: %d -> was: %d" % (DIFI_VERSION_FLOW_SIGNAL_CONTEXT_SIZE, packet_size)), DIFI_VERSION_FLOW_SIGNAL_CONTEXT_SIZE==packet_size)
            if class_id is not None: self.class_id = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_CLASSID, class_id)), DIFI_CLASSID==class_id)
            if reserved is not None: self.reserved = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_RESERVED, reserved)), DIFI_RESERVED==reserved)
            if tsm is not None: self.tsm = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSM_GENERAL_TIMING, tsm)), DIFI_TSM_GENERAL_TIMING==tsm)
            if tsf is not None: self.tsf = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSF_REALTIME_PICOSECONDS, tsf)), DIFI_TSF_REALTIME_PICOSECONDS==tsf)
            #packet
            if icc is not None: self.information_class_code = (("must be: 0x%04x -> was: 0x%04x" % (DIFI_INFORMATION_CLASS_CODE_VERSION_FLOW_CONTEXT, icc)), DIFI_INFORMATION_CLASS_CODE_VERSION_FLOW_CONTEXT==icc)
            if pcc is not None: self.packet_class_code = (("must be: 0x%04x -> was: 0x%04x" % (DIFI_PACKET_CLASS_CODE_VERSION_FLOW_CONTEXT, pcc)), DIFI_PACKET_CLASS_CODE_VERSION_FLOW_CONTEXT==pcc)
            if cif0 is not None: self.context_indicator_field_0 = (("must be: 0x%07x -> was: 0x%07x" % (DIFI_CONTEXT_INDICATOR_FIELD_0_VERSION_FLOW_CONTEXT, cif0)), DIFI_CONTEXT_INDICATOR_FIELD_0_VERSION_FLOW_CONTEXT==cif0)
            if cif1 is not None: self.context_indicator_field_1 = (("must be: 0x%08x -> was: 0x%08x" % (DIFI_CONTEXT_INDICATOR_FIELD_1_VERSION_FLOW_CONTEXT, cif1)), DIFI_CONTEXT_INDICATOR_FIELD_1_VERSION_FLOW_CONTEXT==cif1)
            if v49_spec is not None: self.v49_spec_version = (("must be: 0x%08x -> was: 0x%08x" % (DIFI_V49_SPEC_VERSION_VERSION_FLOW_CONTEXT, v49_spec)), DIFI_V49_SPEC_VERSION_VERSION_FLOW_CONTEXT==v49_spec)

        ############
        #data packet
        ############
        elif packet_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID:
            #stream id
            if stream_id is not None:
                self.stream_id = stream_id
            else:
                self.stream_id = "no-stream-id"
            #header
            self.packet_type = ("0x%1x" % packet_type)
            self.packet_type_display =  (("must be: 0x%1x, 0x%1x, 0x%1x -> was: 0x%1x" % (DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID, packet_type)), True)
            if class_id is not None: self.class_id = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_CLASSID, class_id)), DIFI_CLASSID==class_id)
            if reserved is not None: self.reserved = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_RESERVED, reserved)), DIFI_RESERVED==reserved)
            if tsm is not None: self.tsm = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSM_DATA, tsm)), DIFI_TSM_DATA==tsm)
            if tsf is not None: self.tsf = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSF_REALTIME_PICOSECONDS, tsf)), DIFI_TSF_REALTIME_PICOSECONDS==tsf)
            #packet

        ############
        #unknown packet type
        ############
        else:
            #stream id
            if stream_id is not None:
                self.stream_id = stream_id
            else:
                self.stream_id = "no-stream-id"
            #header
            self.packet_type = ("0x%1x" % packet_type)
            self.packet_type_display =  (("must be: 0x%1x, 0x%1x, 0x%1x -> was: 0x%1x" % (DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID, packet_type)), False)


    #json encoder to change stream id to hex string
    class DifiInfoJSONEncoder(json.JSONEncoder):

        def encode(self, o):
            d = o.copy()

            if type(d["stream_id"]) is int:
                d.update(stream_id = "0x%08x" % d["stream_id"])

            return json.JSONEncoder.encode(self, d)

    def to_json(self):
        return json.dumps(self.__dict__, indent=4, cls=self.DifiInfoJSONEncoder)
        #return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    def __str__(self):
        return self.to_json()




############################
#primary function that decodes DIFI packets
############################
def decode_difi_vrt_packet(stream: BytesIO) -> Union[DifiStandardContextPacket,DifiVersionContextPacket,DifiDataPacket]:
    """
    Read DIFI VRT packet from byte stream, decode it and return class object filled with its data.

    :param stream: raw data stream of bytes to decode
    """

    #get packet type
    tmpbuf = stream.read1(4)
    if not tmpbuf:
        return None
    (value,) = struct.unpack(">I", tmpbuf)
    packet_type = (value >> 28) & 0x0f   #(bit 28-31)

    #get stream id
    tmpbuf = stream.read1(4)
    (value,) = struct.unpack(">I", tmpbuf)
    stream_id = value

    stream.seek(0) #reset stream back to beginning

    #create instance of packet class for packet type (standard context, version context or data packet)
    if packet_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT:
        return DifiStandardContextPacket(stream)
    elif packet_type == DIFI_VERSION_FLOW_SIGNAL_CONTEXT:
        return DifiVersionContextPacket(stream)
    elif packet_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID:
        return DifiDataPacket(stream)

    #not valid data packet because no stream id
    elif packet_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_NO_STREAMID:
        raise NoncompliantDifiPacket("non-compliant DIFI data packet type [data packet without stream ID packet type: 0x%1x]  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (packet_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type=packet_type, stream_id=stream_id))
    #not valid DIFI packet
    else:
        raise NoncompliantDifiPacket("non-compliant DIFI packet type [0x%1x]  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (packet_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type, stream_id=stream_id))



##############################
#standard context packet class - object that is filled from the decoded standard context packet stream
##############################
class DifiStandardContextPacket():
    """
    DIFI Context Packet.
      -Standard Flow Signal Context Packet

    :param stream: raw data stream of bytes to decode
    """

    def __init__(self, stream: BytesIO):

        ##############################
        #decode 32bit header (4 bytes)
        ##############################
        hdrbuf = stream.read1(4)
        if not hdrbuf:
            return
        (hdr,) = struct.unpack(">I", hdrbuf)

        self.pkt_type = (hdr >> 28) & 0x0f     #(bit 28-31)
        self.class_id = (hdr >> 27) & 0x01     #(bit 27)
        self.reserved = (hdr >> 25) & 0x03     #(bit 25-26)
        self.tsm = (hdr >> 24) & 0x01          #(bit 24)
        self.tsi = (hdr >> 22) & 0x03          #(bit 22-23)
        self.tsf = (hdr >> 20) & 0x03          #(bit 20-21)
        self.seq_num = (hdr >> 16) & 0x0f      #(bit 16-19) #mod16 of pkt count (seqnum in difi spec)
        self.pkt_size = (hdr >> 0) & 0xffff    #(bit 0-15) #num 32bit words in pkt

        ##############################
        #decode stream id (4 bytes)
        ##############################
        idbuf = stream.read1(4)
        (value,) = struct.unpack(">I", idbuf)
        self.stream_id = value
        stream.seek(4) #backup to 4 to re-include stream id in data for decoding below

        if DEBUG: print("")
        if DEBUG: print("---")
        if DEBUG: print("DifiStandardContextPacket header data in constructor:")
        if DEBUG: print("Header: %s" % (hdrbuf.hex()))
        if DEBUG: print("Header: %d" % (int.from_bytes(hdrbuf, byteorder='big', signed=False)))
        if DEBUG: print(f"Header: {(int.from_bytes(hdrbuf, byteorder='big', signed=False)):032b}")
        if DEBUG: print("stream id: 0x%08x" % (self.stream_id))
        if DEBUG: print("pkt type: 0x%01x" % (self.pkt_type))
        if DEBUG: print("classid: 0x%01x" % (self.class_id))
        if DEBUG: print("reserved: 0x%01x" % (self.reserved))
        if DEBUG: print("tsm: 0x%01x" % (self.tsm))
        if DEBUG: print("tsi: 0x%01x" % (self.tsi))
        if DEBUG: print("tsf: 0x%01x" % (self.tsf))
        if DEBUG: print("pkt count (mod16): %d" % (self.seq_num))  #packet_count
        if DEBUG: print("pkt size: %d" % (self.pkt_size)) #packet_size
        if DEBUG: print("---")

        #only allow if standard context packet type
        if self.pkt_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT:

            #only decode if header is valid
            if self.is_difi10_standard_context_packet_header(self.pkt_type, self.pkt_size, self.class_id, self.reserved, self.tsm, self.tsf):
                packet_size_in_bytes = (self.pkt_size - 1) * 4  #less header (-1)
                context_data = stream.read1(packet_size_in_bytes)
                self._decode_standard_flow_signal_context(context_data)
            else:
                raise NoncompliantDifiPacket("non-compliant DIFI standard context packet header [packet type: 0x%1x]" % self.pkt_type, DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))
        else:
            raise NoncompliantDifiPacket("non-compliant packet type [0x%1x] for DIFI standard context packet  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (self.pkt_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))


    #function to decode standard context packet
    def _decode_standard_flow_signal_context(self, data):

        if DEBUG: print("Decoding.....")
        #print(data.hex())

        try:
            #only fully decode if DIFI compliant
            #  -check Context Indicator Field
            #  -check Data Payload Format Fields
            (cif,) = struct.unpack(">I", data[24:28])
            cif = (cif & 0x0FFFFFFF)
            (value1,value2) = struct.unpack(">II", data[96:104])
            data_payload_fmt_pk_mh = (value1 >> 31) & 0x01  #bit31
            data_payload_fmt_real_cmp_type = (value1 >> 29) & 0x03  #bit29-30
            data_payload_fmt_data_item_fmt = (value1 >> 24) & 0x1F  #bit24-28
            data_payload_fmt_rpt_ind = (value1 >> 23) & 0x01  #bit23
            data_payload_fmt_event_tag_size = (value1 >> 20) & 0x07  #bit20-22
            data_payload_fmt_channel_tag_size = (value1 >> 16) & 0x0F  #bit16-19
            if not self.is_difi10_standard_context_packet(cif, data_payload_fmt_pk_mh, data_payload_fmt_real_cmp_type, data_payload_fmt_data_item_fmt, data_payload_fmt_rpt_ind, data_payload_fmt_event_tag_size, data_payload_fmt_channel_tag_size):
                raise NoncompliantDifiPacket("non-compliant DIFI standard context packet.", DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf, cif0=cif, data_payload_fmt_pk_mh=data_payload_fmt_pk_mh, data_payload_fmt_real_cmp_type=data_payload_fmt_real_cmp_type, data_payload_fmt_data_item_fmt=data_payload_fmt_data_item_fmt, data_payload_fmt_rpt_ind=data_payload_fmt_rpt_ind, data_payload_fmt_event_tag_size=data_payload_fmt_event_tag_size, data_payload_fmt_channel_tag_size=data_payload_fmt_channel_tag_size))


            #######################
            #Stream ID (5.1.2)
            #######################
            if DEBUG: print(data[0:4].hex())
            #already unpacked in constructor __init__
            #(value,) = struct.unpack(">I", data[0:4])
            #if DEBUG: print(" Stream ID = 0x%08x (ID)" % (value))
            #self.stream_id = value
            if DEBUG: print(" Stream ID = 0x%08x (ID)" % (self.stream_id))

            ##########################
            #OUI (5.1.3)
            ##########################
            if DEBUG: print(data[4:8].hex())
            #h = b'\x00\x7C\x38\x6C'
            #h = b'\x00\x00\x12\xa2'
            (value,) = struct.unpack(">I", data[4:8])
            value = value & 0x00FFFFFF
            if DEBUG: print(" OUI = 0x%06x" % (value))
            self.oui = value

            #########################
            #Information Class Code / Packet Class Code (5.1.3)
            ########################
            if DEBUG: print(data[8:12].hex())
            #h = b'\x00\x00\x00\x80'
            #h = b'\x00\x00\xff\x80'
            #h = b'\x00\x00\x00\x01'
            #h = b'\x00\x00\xff\xff'
            (icc,pcc) = struct.unpack(">HH", data[8:12])
            if DEBUG: print(" Information Class Code = 0x%04x - Packet Class Code = 0x%04x" % (icc, pcc))
            self.information_class_code = icc
            self.packet_class_code = pcc

            #######################
            #Integer-seconds Timestamp (5.1.4 and 5.1.5)
            #######################
            if DEBUG: print(data[12:16].hex())
            (value,) = struct.unpack(">I", data[12:16])
            if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')))
            #if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')))
            self.integer_seconds_timestamp = value
            self.integer_seconds_timestamp_display = datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')

            #######################
            #Fractional-seconds Timestamp (5.1.4 and 5.1.5)
            #######################
            if DEBUG: print(data[16:24].hex())
            (value,) = struct.unpack(">Q", data[16:24])
            if DEBUG: print(" Fractional-seconds Timestamp (picoseconds past integer seconds) = %d" % (value))
            self.fractional_seconds_timestamp = value

            #######################
            #Context Indicator Field(CIF 0) (9)
            #######################
            if DEBUG: print(data[24:28].hex())
            (value,) = struct.unpack(">I", data[24:28])
            if DEBUG: print(" Context Indicator Field (CIF 0) = 0x%08x" % (value))
            self.context_indicator_field_cif0 = value

            #######################
            #Reference Point (9.2)
            #######################
            if DEBUG: print(data[28:32].hex())
            (value,) = struct.unpack(">I", data[28:32])
            if DEBUG: print(" Reference Point = 0x%08x (ID)" % (value))
            self.ref_point = value

            ###################
            #Bandwidth (9.5.1)
            ###################
            if DEBUG: print(data[32:40].hex())
            #h = b'\x00\x00\x00\x00\x00\x10\x00\x00'
            #h = b'\x00\x00\x00\x00\x00\x00\x00\x01'
            (value,) = struct.unpack(">Q", data[32:40])
            value /= 2.0 ** 20
            if DEBUG: print(" Bandwidth = %.8f (Hertz)" % value)
            self.bandwidth = value

            ################################
            #IF Reference Frequency (9.5.5)
            ################################
            if DEBUG: print(data[40:48].hex())
            #h = b'\x00\x00\x00\x00\x00\x10\x00\x00'
            #h = b'\xff\xff\xff\xff\xff\xf0\x00\x00'
            #h = b'\x00\x00\x00\x00\x00\x00\x00\x01'
            #h = b'\xff\xff\xff\xff\xff\xff\xff\xff'
            (value,) = struct.unpack(">q", data[40:48])
            value /= 2.0 ** 20
            if DEBUG: print(" IF Reference Frequency = %.8f (Hertz)" % (value))
            self.if_ref_freq = value

            #################################
            #RF Reference Frequency (9.5.10)
            #################################
            if DEBUG: print(data[48:56].hex())
            #h = b'\x00\x00\x00\x00\x00\x10\x00\x00'
            #h = b'\xff\xff\xff\xff\xff\xf0\x00\x00'
            #h = b'\x00\x00\x00\x00\x00\x00\x00\x01'
            #h = b'\xff\xff\xff\xff\xff\xff\xff\xff'
            (value,) = struct.unpack(">q", data[48:56])
            value /= 2.0 ** 20
            if DEBUG: print(" RF Reference Frequency = %.8f (Hertz)" % (value))
            self.rf_ref_freq = value

            ########################
            #IF Band Offset (9.5.4)
            #######################
            if DEBUG: print(data[56:64].hex())
            #h = b'\x00\x00\x00\x00\x00\x10\x00\x00'
            #h = b'\xff\xff\xff\xff\xff\xf0\x00\x00'
            #h = b'\x00\x00\x00\x00\x00\x00\x00\x01'
            #h = b'\xff\xff\xff\xff\xff\xff\xff\xff'
            (value,) = struct.unpack(">q", data[56:64])
            value /= 2.0 ** 20
            if DEBUG: print(" IF Band Offset = %.8f (Hertz)" % (value))
            self.if_band_offset = value

            #########################
            #Reference Level (9.5.9)
            ########################
            if DEBUG: print(data[64:68].hex())
            #h = b'\x00\x00\x00\x80'
            #h = b'\x00\x00\xff\x80'
            #h = b'\x00\x00\x00\x01'
            #h = b'\x00\x00\xff\xff'
            (r1,value) = struct.unpack(">hh", data[64:68])  # pylint: disable=unused-variable
            value /= 2.0 ** 7
            if DEBUG: print(" Reference Level = %.8f (dBm)" % (value))
            self.ref_level = value

            ##########################
            #Gain/Attenuation (9.5.3)
            ##########################
            if DEBUG: print(data[68:72].hex())
            #h = b'\x00\x80\x00\x80'
            #h = b'\xff\x80\xff\x80'
            #h = b'\x00\x01\x00\x01'
            #h = b'\xff\xff\xff\xff'
            (g2,g1) = struct.unpack(">hh", data[68:72])
            g2 /= 2.0 ** 7
            g1 /= 2.0 ** 7
            if DEBUG: print(" Stage1 Gain/Attenuation = %.8f (dB)" % (g1))
            if DEBUG: print(" Stage2 Gain/Attenuation = %.8f (dB)" % (g2))
            self.gain_attenuation = (g2, g1)

            ######################
            #Sample Rate (9.5.12)
            ######################
            if DEBUG: print(data[72:80].hex())
            #h = b'\x00\x00\x00\x00\x00\x10\x00\x00'
            #h = b'\x00\x00\x00\x00\x00\x00\x00\x01'
            (value,) = struct.unpack(">Q", data[72:80])
            value /= 2.0 ** 20
            if DEBUG: print(" Sample Rate = %.8f (Hertz)" % (value))
            self.sample_rate = value

            ############################################
            #Timestamp Adjustment (9.7.3.1)(rule 9.7-1)(9.7-2)
            ############################################
            if DEBUG: print(data[80:88].hex())
            (value,) = struct.unpack(">q", data[80:88])
            if DEBUG: print(" Timestamp Adjustment = %d (femtoseconds)" % (value))
            self.timestamp_adjustment = value

            ######################################
            #Timestamp Calibration Time (9.7.3.3)
            ######################################
            if DEBUG: print(data[88:92].hex())
            #h = b'\xff\xff\xff\xff'
            (value,) = struct.unpack(">I", data[88:92])
            if DEBUG: print(" Timestamp Calibration Time = %d (seconds)" % (value))
            self.timestamp_calibration_time = value

            #####################################
            #State and Event Indicators (9.10.8)
            #####################################
            #bit17 - Reference Lock Indicator
            #bit19 - Calibrated Time Indicator
            if DEBUG: print(data[92:96].hex())
            #h = b'\x00\x0A\x00\x00'
            (value,) = struct.unpack(">I", data[92:96])
            if DEBUG: print(" State and Event Indicators = %d" % (value))
            self.state_and_event_indicators = {
                    "raw_value" : value
                    ,"calibrated_time_indicator" : (value >> 19) & 0x01  #bit19
                    ,"valid_data_indicator" : (value >> 18) & 0x01  #bit18
                    ,"reference_lock_indicator" : (value >> 17) & 0x01  #bit17
                    ,"agc_mgc_indicator" : (value >> 16) & 0x01  #bit16
                    ,"detected_signal_indicator" : (value >> 15) & 0x01  #bit15
                    ,"spectral_inversion_indicator" : (value >> 14) & 0x01  #bit14
                    ,"over_range_indicator" : (value >> 13) & 0x01  #bit13
                    ,"sample_loss_indicator" : (value >> 12) & 0x01  #bit12
                    }
            if DEBUG: print("   Calibrated Time Indicator (bit 19) = %d" % (self.state_and_event_indicators["calibrated_time_indicator"]))
            if DEBUG: print("   Valid Data Indicator (bit 18) = %d" % (self.state_and_event_indicators["valid_data_indicator"]))
            if DEBUG: print("   Reference Lock Indicator (bit 17) = %d" % (self.state_and_event_indicators["reference_lock_indicator"]))
            if DEBUG: print("   AGC/MGC Indicator (bit 16) = %d" % (self.state_and_event_indicators["agc_mgc_indicator"]))
            if DEBUG: print("   Detected Signal Indicator (bit 15) = %d" % (self.state_and_event_indicators["detected_signal_indicator"]))
            if DEBUG: print("   Spectral Inversion Indicator (bit 14) = %d" % (self.state_and_event_indicators["spectral_inversion_indicator"]))
            if DEBUG: print("   Over-range Indicator (bit 13) = %d" % (self.state_and_event_indicators["over_range_indicator"]))
            if DEBUG: print("   Sample Loss Indicator (bit 12) = %d" % (self.state_and_event_indicators["sample_loss_indicator"]))

            #####################################
            #Data Packet Payload Format (9.13.3)(Figure B-37)
            #####################################
            if DEBUG: print(data[96:104].hex())
            #h = b'\x00\x00\x07\xDF\x00\x00\x00\x00'
            #h = b'\x00\x20\x02\x47\x00\x00\x00\x00'
            (value1,value2) = struct.unpack(">II", data[96:104])
            if DEBUG: print(" Data Packet Payload Format = %d (word1), %d (word2)" % (value1, value2))
            self.data_packet_payload_format = {
                    "raw_value_word1" : value1
                    ,"raw_value_word2" : value2
                    #--------
                    ,"packing_method" : (value1 >> 31) & 0x01  #bit31
                    ,"real_complex_type" : (value1 >> 29) & 0x03  #bit29-30
                    ,"data_item_format" : (value1 >> 24) & 0x1F  #bit24-28
                    ,"sample_component_repeat_indicator" : (value1 >> 23) & 0x01  #bit23
                    ,"event_tag_size" : (value1 >> 20) & 0x07  #bit20-22
                    ,"channel_tag_size" : (value1 >> 16) & 0x0F  #bit16-19
                    ,"data_item_fraction_size" : (value1 >> 12) & 0x0F  #bit12-15
                    ,"item_packing_field_size" : (value1 >> 6) & 0x3F  #bit6-11
                    ,"data_item_size" : (value1 >> 0) & 0x3F  #bit0-5
                    #--------
                    ,"repeat_count" : (value2 >> 16) & 0xFFFF  #bit16-31
                    ,"vector_size" : (value2 >> 0) & 0xFFFF  #bit0-15
                    }
            if DEBUG: print("   Packing Method (bit 31) = %d" % (self.data_packet_payload_format["packing_method"]))
            if DEBUG: print("   Real/Complex Type (bit 29-30) = %d" % (self.data_packet_payload_format["real_complex_type"]))
            if DEBUG: print("   Data Item Format (bit 24-28) = %d" % (self.data_packet_payload_format["data_item_format"]))
            if DEBUG: print("   Sample-Component Repeat Indicator (bit 23) = %d" % (self.data_packet_payload_format["sample_component_repeat_indicator"]))
            if DEBUG: print("   Event-Tag Size (bit 20-22) = %d" % (self.data_packet_payload_format["event_tag_size"]))
            if DEBUG: print("   Channel-Tag Size (bit 16-19) = %d" % (self.data_packet_payload_format["channel_tag_size"]))
            if DEBUG: print("   Data Item Fraction Size (bit 12-15) = %d" % (self.data_packet_payload_format["data_item_fraction_size"]))
            if DEBUG: print("   Item Packing Field Size (bit 6-11) = %d" % (self.data_packet_payload_format["item_packing_field_size"]))
            if DEBUG: print("   Data Item Size (bit 0-5) = %d" % (self.data_packet_payload_format["data_item_size"]))
            #--------
            if DEBUG: print("   Repeat Count (bit 16-31) = %d" % (self.data_packet_payload_format["repeat_count"]))
            if DEBUG: print("   Vector Size (bit 0-15) = %d" % (self.data_packet_payload_format["vector_size"]))

            #bit layout (value1 and value2)
            #[31]     Packing Method (1)
            #[30..29] Real/Complex Type (2)
            #[28..24] Data Item Format (5)
            #[23]     Sample-Component Repeat Indicator (1)
            #[22..20] Event-Tag Size (3)
            #[19..16] Channel-Tag Size (4)
            #[15..12] Data Item Fraction Size (4)
            #[11..6]  Item Packing Field Size (6)
            #[5..0]   Data Item Size (6)
            #--------
            #[31..16] Repeat Count (16)
            #[15..0]  Vector Size (16)
            #
            #
            #difi spec says only supports:
            #  complex Cartesian samples (I and Q)
            #  link-efficient packing
            #  signed fixed-point
            #  no event or channel tags
            #  sample sizes from 4 through 16 bits without sample component repeats and no unused bits
            #
            #"Packing Method" = 1 (for link-efficient packing)
            #  0 processing-efficient packing
            #  1 link-efficient packing
            #"Real/Complex Type" = 01 (for complex cartesian)
            #  00 Real
            #  01 Complex, Cartesian
            #  10 Complex, Polar
            #  11 Reserved
            #"Data Item Format" = 00000 (for signed fixed-point)
            #  00000 Signed Fixed-Point
            #  10000 Unsigned Fixed-Point
            #"Sample-Component Repeat Indicator" = 0 (for without sample component repeats)
            #  0 no Sample Component Repeating
            #  1 Sample Component Repeating
            #"Event-Tag Size" = 0 (for no event tag)
            #"Channel-Tag Size" = 0 (for no channel tag)

        except NoncompliantDifiPacket as e:
            raise e
        except Exception as e:
            raise e

        if DEBUG: print("Finished decoding.\r\n---\r\n")

        #debug
        #print("JSON dump object 'DifiStandardContextPacket'-standard flow:\r\n\r\n", self.to_json())
        #print("String dump object 'DifiStandardContextPacket'-standard flow:\r\n", str(self))


    #json encoder to change applicable int's to hex string
    class StandardContextPacketHexJSONEncoder(json.JSONEncoder):

        def encode(self, o):
            d = o.copy()
            if type(d["pkt_type"]) is int:
                d.update(pkt_type = "0x%1x" % d["pkt_type"])
            if type(d["class_id"]) is int:
                d.update(class_id = "0x%1x" % d["class_id"])
            if type(d["reserved"]) is int:
                d.update(reserved = "0x%1x" % d["reserved"])
            if type(d["tsm"]) is int:
                d.update(tsm = "0x%1x" % d["tsm"])
            if type(d["tsi"]) is int:
                d.update(tsi = "0x%1x" % d["tsi"])
            if type(d["tsf"]) is int:
                d.update(tsf = "0x%1x" % d["tsf"])
            if type(d["stream_id"]) is int:
                d.update(stream_id = "0x%08x" % d["stream_id"])
            if type(d["oui"]) is int:
                d.update(oui = "0x%06x" % d["oui"])
            if type(d["information_class_code"]) is int:
                d.update(information_class_code = "0x%04x" % d["information_class_code"])
            if type(d["packet_class_code"]) is int:
                d.update(packet_class_code = "0x%04x" % d["packet_class_code"])
            if type(d["context_indicator_field_cif0"]) is int:
                d.update(context_indicator_field_cif0 = "0x%08x" % d["context_indicator_field_cif0"])
            if type(d["ref_point"]) is int:
                d.update(ref_point = "0x%08x" % d["ref_point"])

            return json.JSONEncoder.encode(self, d)


    def to_json(self, hex_values=False):
        #s = json.dumps(self, default=vars, indent=4)
        #s = json.loads(zlib.decompress(data))
        if hex_values is True:
            return json.dumps(self.__dict__, indent=4, cls=self.StandardContextPacketHexJSONEncoder)
        else:
            return json.dumps(self, default=lambda o: o.__dict__, indent=4)


    def __str__(self):

        return ("Stream ID: 0x%08x (ID)\r\n\
OUI: 0x%06x\r\n\
Information Class Code: 0x%04x\r\n\
Packet Class Code: 0x%04x\r\n\
Integer-seconds Timestamp (seconds since epoch): %d (%s)\r\n\
Fractional-seconds Timestamp (picoseconds past integer-seconds): %d\r\n\
Context Indicator Field (CIF 0): 0x%08x\r\n\
Reference Point: 0x%08x (ID)\r\n\
Bandwidth: %.8f (Hertz)\r\n\
IF Reference Frequency: %.8f (Hertz)\r\n\
RF Reference Frequency: %.8f (Hertz)\r\n\
IF Band Offset: %.8f (Hertz)\r\n\
Reference Level: %.8f (dBm)\r\n\
Stage1 Gain/Attenuation: %.8f (dB)\r\n\
Stage2 Gain/Attenuation: %.8f (dB)\r\n\
Sample Rate: %.8f (Hertz)\r\n\
Timestamp Adjustment: %d (femtoseconds)\r\n\
Timestamp Calibration Time: %d (seconds)\r\n\
State and Event Indicators: %d\r\n\
  Calibrated Time Indicator (bit 19): %d\r\n\
  Valid Data Indicator (bit 18): %d\r\n\
  Reference Lock Indicator (bit 17): %d\r\n\
  AGC/MGC Indicator (bit 16): %d\r\n\
  Detected Signal Indicator (bit 15): %d\r\n\
  Spectral Inversion Indicator (bit 14): %d\r\n\
  Over-range Indicator (bit 13): %d\r\n\
  Sample Loss Indicator (bit 12): %d\r\n\
Data Packet Payload Format: %d (word1), %d (word2)\r\n\
  Packing Method (bit 31): %d\r\n\
  Real/Complex Type (bit 29-30): %d\r\n\
  Data Item Format (bit 24-28): %d\r\n\
  Sample-Component Repeat Indicator (bit 23): %d\r\n\
  Event-Tag Size (bit 20-22): %d\r\n\
  Channel-Tag Size (bit 16-19): %d\r\n\
  Data Item Fraction Size (bit 12-15): %d\r\n\
  Item Packing Field Size (bit 6-11): %d\r\n\
  Data Item Size (bit 0-5): %d\r\n\
  --------\r\n\
  Repeat Count (bit 16-31): %d\r\n\
  Vector Size (bit 0-15): %d\r\n\
" % (self.stream_id,
    self.oui,
    self.information_class_code,
    self.packet_class_code,
    self.integer_seconds_timestamp,
    datetime.fromtimestamp(self.integer_seconds_timestamp, tz=timezone.utc).strftime('%m/%d/%Y %r %Z'),
    self.fractional_seconds_timestamp,
    self.context_indicator_field_cif0,
    self.ref_point,
    self.bandwidth,
    self.if_ref_freq,
    self.rf_ref_freq,
    self.if_band_offset,
    self.ref_level,
    self.gain_attenuation[1],
    self.gain_attenuation[0],
    self.sample_rate,
    self.timestamp_adjustment,
    self.timestamp_calibration_time,
    self.state_and_event_indicators["raw_value"],
    self.state_and_event_indicators["calibrated_time_indicator"],
    self.state_and_event_indicators["valid_data_indicator"],
    self.state_and_event_indicators["reference_lock_indicator"],
    self.state_and_event_indicators["agc_mgc_indicator"],
    self.state_and_event_indicators["detected_signal_indicator"],
    self.state_and_event_indicators["spectral_inversion_indicator"],
    self.state_and_event_indicators["over_range_indicator"],
    self.state_and_event_indicators["sample_loss_indicator"],
    self.data_packet_payload_format["raw_value_word1"],
    self.data_packet_payload_format["raw_value_word2"],
    self.data_packet_payload_format["packing_method"],
    self.data_packet_payload_format["real_complex_type"],
    self.data_packet_payload_format["data_item_format"],
    self.data_packet_payload_format["sample_component_repeat_indicator"],
    self.data_packet_payload_format["event_tag_size"],
    self.data_packet_payload_format["channel_tag_size"],
    self.data_packet_payload_format["data_item_fraction_size"],
    self.data_packet_payload_format["item_packing_field_size"],
    self.data_packet_payload_format["data_item_size"],
    self.data_packet_payload_format["repeat_count"],
    self.data_packet_payload_format["vector_size"]))


    ##############################
    #DIFI packet validation checks
    ##############################

    #standard context packet header
    def is_difi10_standard_context_packet_header(self, packet_type, packet_size, class_id, rsvd, tsm, tsf):
        return (packet_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT
            and packet_size == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT_SIZE
            and class_id == DIFI_CLASSID
            and rsvd == DIFI_RESERVED
            and tsm == DIFI_TSM_GENERAL_TIMING
            and tsf == DIFI_TSF_REALTIME_PICOSECONDS)

    #standard context packet
    def is_difi10_standard_context_packet(self, cif, data_payload_fmt_pk_mh, data_payload_fmt_real_cmp_type, data_payload_fmt_data_item_fmt, data_payload_fmt_rpt_ind, data_payload_fmt_event_tag_size, data_payload_fmt_channel_tag_size):
        return (cif == DIFI_CONTEXT_INDICATOR_FIELD_STANDARD_FLOW_CONTEXT
            and data_payload_fmt_pk_mh == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_PACKING_METHOD
            and data_payload_fmt_real_cmp_type == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_REAL_COMPLEX_TYPE
            and data_payload_fmt_data_item_fmt == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_DATA_ITEM_FORMAT
            and data_payload_fmt_rpt_ind == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_SAMPLE_COMPONENT_REPEAT_IND
            and data_payload_fmt_event_tag_size == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_EVENT_TAG_SIZE
            and data_payload_fmt_channel_tag_size == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_CHANNEL_TAG_SIZE)



#############################
#version context packet class - object that is filled from the decoded version context packet stream
#############################
class DifiVersionContextPacket():
    """
    DIFI Context Packet.
      -Version Flow Signal Context Packet

    :param stream: raw data stream of bytes to decode
    """

    def __init__(self, stream: BytesIO):

        ##############################
        #decode 32bit header (4 bytes)
        ##############################
        hdrbuf = stream.read1(4)
        if not hdrbuf:
            return
        (hdr,) = struct.unpack(">I", hdrbuf)

        self.pkt_type = (hdr >> 28) & 0x0f     #(bit 28-31)
        self.class_id = (hdr >> 27) & 0x01     #(bit 27)
        self.reserved = (hdr >> 25) & 0x03     #(bit 25-26)
        self.tsm = (hdr >> 24) & 0x01          #(bit 24)
        self.tsi = (hdr >> 22) & 0x03          #(bit 22-23)
        self.tsf = (hdr >> 20) & 0x03          #(bit 20-21)
        self.seq_num = (hdr >> 16) & 0x0f      #(bit 16-19) #mod16 of pkt count (seqnum in difi spec)
        self.pkt_size = (hdr >> 0) & 0xffff    #(bit 0-15) #num 32bit words in pkt

        ##############################
        #decode stream id (4 bytes)
        ##############################
        idbuf = stream.read1(4)
        (value,) = struct.unpack(">I", idbuf)
        self.stream_id = value
        stream.seek(4) #backup to 4 to re-include stream id in data for decoding below

        if DEBUG: print("")
        if DEBUG: print("---")
        if DEBUG: print("DifiVersionContextPacket header data in constructor:")
        if DEBUG: print("Header: %s" % (hdrbuf.hex()))
        if DEBUG: print("Header: %d" % (int.from_bytes(hdrbuf, byteorder='big', signed=False)))
        if DEBUG: print(f"Header: {(int.from_bytes(hdrbuf, byteorder='big', signed=False)):032b}")
        if DEBUG: print("stream id: 0x%08x" % (self.stream_id))
        if DEBUG: print("pkt type: 0x%01x" % (self.pkt_type))
        if DEBUG: print("classid: 0x%01x" % (self.class_id))
        if DEBUG: print("reserved: 0x%01x" % (self.reserved))
        if DEBUG: print("tsm: 0x%01x" % (self.tsm))
        if DEBUG: print("tsi: 0x%01x" % (self.tsi))
        if DEBUG: print("tsf: 0x%01x" % (self.tsf))
        if DEBUG: print("pkt count (mod16): %d" % (self.seq_num))  #packet_count
        if DEBUG: print("pkt size: %d" % (self.pkt_size)) #packet_size
        if DEBUG: print("---")

        #only allow if version context packet type
        if self.pkt_type == DIFI_VERSION_FLOW_SIGNAL_CONTEXT:

            #only decode if header is valid
            if self.is_difi10_version_context_packet_header(self.pkt_type, self.pkt_size, self.class_id, self.reserved, self.tsm, self.tsf):
                packet_size_in_bytes = (self.pkt_size - 1) * 4  #less header (-1)
                context_data = stream.read1(packet_size_in_bytes)
                self._decode_version_flow_signal_context(context_data)
            else:
                raise NoncompliantDifiPacket("non-compliant DIFI version context packet header [packet type: 0x%1x]" % self.pkt_type, DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))
        else:
            raise NoncompliantDifiPacket("non-compliant packet type [0x%1x] for DIFI version context packet  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (self.pkt_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))


    #function to decode version context packet
    def _decode_version_flow_signal_context(self, data):

        if DEBUG: print("Decoding.....")
        #print(data.hex())

        try:
            #only fully decode if DIFI compliant
            #  -check Information Class Code/Packet Class Code
            #  -check Context Indicator Field 0
            #  -check Context Indicator Field 1
            #  -check V49 Spec Version
            (icc,pcc) = struct.unpack(">HH", data[8:12])
            (cif0,) = struct.unpack(">I", data[24:28])
            cif0 = (cif0 & 0x0fffffff)
            (cif1,) = struct.unpack(">I", data[28:32])
            (v49_spec,) = struct.unpack(">I", data[32:36])
            if not self.is_difi10_version_context_packet(icc, pcc, cif0, cif1, v49_spec):
                raise NoncompliantDifiPacket("non-compliant DIFI version context packet.", DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf, icc=icc, pcc=pcc, cif0=cif0, cif1=cif1, v49_spec=v49_spec))


            #######################
            #Stream ID (5.1.2)
            #######################
            if DEBUG: print(data[0:4].hex())
            #already unpacked in constructor __init__
            #(value,) = struct.unpack(">I", data[0:4])
            #if DEBUG: print(" Stream ID = 0x%08x (ID)" % (value))
            #self.stream_id = value
            if DEBUG: print(" Stream ID = 0x%08x (ID)" % (self.stream_id))

            ##########################
            #OUI (5.1.3)
            ##########################
            if DEBUG: print(data[4:8].hex())
            #h = b'\x00\x7C\x38\x6C'
            #h = b'\x00\x00\x12\xa2'
            (value,) = struct.unpack(">I", data[4:8])
            value = value & 0x00FFFFFF
            if DEBUG: print(" OUI = 0x%06x" % (value))
            self.oui = value

            #########################
            #Information Class Code / Packet Class Code (5.1.3)
            ########################
            if DEBUG: print(data[8:12].hex())
            #h = b'\x00\x00\x00\x80'
            #h = b'\x00\x00\xff\x80'
            #h = b'\x00\x00\x00\x01'
            #h = b'\x00\x00\xff\xff'
            (icc,pcc) = struct.unpack(">HH", data[8:12])
            if DEBUG: print(" Information Class Code = 0x%04x - Packet Class Code = 0x%04x" % (icc, pcc))
            self.information_class_code = icc
            self.packet_class_code = pcc

            #######################
            #Integer-seconds Timestamp (5.1.4 and 5.1.5)
            #######################
            if DEBUG: print(data[12:16].hex())
            (value,) = struct.unpack(">I", data[12:16])
            if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')))
            #if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')))
            self.integer_seconds_timestamp = value
            self.integer_seconds_timestamp_display = datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')

            #######################
            #Fractional-seconds Timestamp (5.1.4 and 5.1.5)
            #######################
            if DEBUG: print(data[16:24].hex())
            (value,) = struct.unpack(">Q", data[16:24])
            if DEBUG: print(" Fractional-seconds Timestamp (picoseconds past integer seconds) = %d" % (value))
            self.fractional_seconds_timestamp = value

            #######################
            #Context Indicator Field(CIF 0) (9)
            #######################
            if DEBUG: print(data[24:28].hex())
            (value,) = struct.unpack(">I", data[24:28])
            if DEBUG: print(" Context Indicator Field (CIF 0) = 0x%08x" % (value))
            self.context_indicator_field_cif0 = value

            #######################
            #Context Indicator Field(CIF 1) (9)
            #######################
            if DEBUG: print(data[28:32].hex())
            (value,) = struct.unpack(">I", data[28:32])
            if DEBUG: print(" Context Indicator Field (CIF 1) = 0x%08x" % (value))
            self.context_indicator_field_cif1 = value

            #######################
            #V49 Spec Version (9)
            #######################
            if DEBUG: print(data[32:36].hex())
            (value,) = struct.unpack(">I", data[32:36])
            if DEBUG: print(" V49 Spec Version = 0x%08x" % (value))
            self.v49_spec_version = value

            #######################
            #Year, Day, Revision, Type, ICD Version (9.10.4)
            #######################
            if DEBUG: print(data[36:40].hex())
            (value,) = struct.unpack(">I", data[36:40])
            self.year = (value >> 25) & 0x7f         #(bit 25-31)
            self.year+=2000
            self.day  = (value >> 16) & 0x1ff        #(bit 16-24)
            self.revision = (value >> 10) & 0x3f     #(bit 10-15)
            self.type = (value >> 6) & 0xf           #(bit 6-9)
            self.icd_version = (value >> 0) & 0x3f   #(bit 0-5)
            if DEBUG: print(" Year=%d - Day=%d - Revision=%d - Type=%d - ICDVersion=%d" % (self.year,self.day,self.revision,self.type,self.icd_version))

        except NoncompliantDifiPacket as e:
            raise e
        except Exception as e:
            raise e

        if DEBUG: print("Finished decoding.\r\n---\r\n")

        #debug
        #print("JSON dump object 'DifiVersionContextPacket'-version flow:\r\n\r\n", self.to_json())
        #print("String dump object 'DifiVersionContextPacket'-version flow:\r\n", str(self))


    #json encoder to change applicable int's to hex string
    class VersionContextPacketHexJSONEncoder(json.JSONEncoder):

        def encode(self, o):
            d = o.copy()
            if type(d["pkt_type"]) is int:
                d.update(pkt_type = "0x%1x" % d["pkt_type"])
            if type(d["class_id"]) is int:
                d.update(class_id = "0x%1x" % d["class_id"])
            if type(d["reserved"]) is int:
                d.update(reserved = "0x%1x" % d["reserved"])
            if type(d["tsm"]) is int:
                d.update(tsm = "0x%1x" % d["tsm"])
            if type(d["tsi"]) is int:
                d.update(tsi = "0x%1x" % d["tsi"])
            if type(d["tsf"]) is int:
                d.update(tsf = "0x%1x" % d["tsf"])
            if type(d["stream_id"]) is int:
                d.update(stream_id = "0x%08x" % d["stream_id"])
            if type(d["oui"]) is int:
                d.update(oui = "0x%06x" % d["oui"])
            if type(d["information_class_code"]) is int:
                d.update(information_class_code = "0x%04x" % d["information_class_code"])
            if type(d["packet_class_code"]) is int:
                d.update(packet_class_code = "0x%04x" % d["packet_class_code"])
            if type(d["context_indicator_field_cif0"]) is int:
                d.update(context_indicator_field_cif0 = "0x%08x" % d["context_indicator_field_cif0"])
            if type(d["context_indicator_field_cif1"]) is int:
                d.update(context_indicator_field_cif1 = "0x%08x" % d["context_indicator_field_cif1"])
            if type(d["v49_spec_version"]) is int:
                d.update(v49_spec_version = "0x%08x" % d["v49_spec_version"])

            return json.JSONEncoder.encode(self, d)


    def to_json(self, hex_values=False):
        #s = json.dumps(self, default=vars, indent=4)
        #s = json.loads(zlib.decompress(data))
        if hex_values is True:
            return json.dumps(self.__dict__, indent=4, cls=self.VersionContextPacketHexJSONEncoder)
        else:
            return json.dumps(self, default=lambda o: o.__dict__, indent=4)


    def __str__(self):

        return ("Stream ID: 0x%08x (ID)\r\n\
OUI: 0x%06x\r\n\
Information Class Code: 0x%04x\r\n\
Packet Class Code: 0x%04x\r\n\
Integer-seconds Timestamp (seconds since epoch): %d (%s)\r\n\
Fractional-seconds Timestamp (picoseconds past integer-seconds): %d\r\n\
Context Indicator Field (CIF 0): 0x%08x\r\n\
Context Indicator Field (CIF 1): 0x%08x\r\n\
V49 Spec Version: 0x%08x\r\n\
Year: %d\r\n\
Day: %d\r\n\
Revision: %d\r\n\
Type: %d\r\n\
ICD Version: %d\r\n\
" % (self.stream_id,
    self.oui,
    self.information_class_code,
    self.packet_class_code,
    self.integer_seconds_timestamp,
    datetime.fromtimestamp(self.integer_seconds_timestamp, tz=timezone.utc).strftime('%m/%d/%Y %r %Z'),
    self.fractional_seconds_timestamp,
    self.context_indicator_field_cif0,
    self.context_indicator_field_cif1,
    self.v49_spec_version,
    self.year,
    self.day,
    self.revision,
    self.type,
    self.icd_version))


    ##############################
    #DIFI packet validation checks
    ##############################

    #version context packet header
    def is_difi10_version_context_packet_header(self, packet_type, packet_size, class_id, rsvd, tsm, tsf):
        return (packet_type == DIFI_VERSION_FLOW_SIGNAL_CONTEXT
            and packet_size == DIFI_VERSION_FLOW_SIGNAL_CONTEXT_SIZE
            and class_id == DIFI_CLASSID
            and rsvd == DIFI_RESERVED
            and tsm == DIFI_TSM_GENERAL_TIMING
            and tsf == DIFI_TSF_REALTIME_PICOSECONDS)

    #version context packet
    def is_difi10_version_context_packet(self, icc, pcc, cif0, cif1, v49_spec):
        return (icc == DIFI_INFORMATION_CLASS_CODE_VERSION_FLOW_CONTEXT
            and pcc == DIFI_PACKET_CLASS_CODE_VERSION_FLOW_CONTEXT
            and cif0 == DIFI_CONTEXT_INDICATOR_FIELD_0_VERSION_FLOW_CONTEXT
            and cif1 == DIFI_CONTEXT_INDICATOR_FIELD_1_VERSION_FLOW_CONTEXT
            and v49_spec == DIFI_V49_SPEC_VERSION_VERSION_FLOW_CONTEXT)



##################
#data packet class - object that is filled from the decoded data packet stream
##################
class DifiDataPacket():
    """
    DIFI Data Packet.
      -Standard Flow Signal Data Packet

    :param stream: raw data stream of bytes to decode
    """

    def __init__(self, stream: BytesIO):

        ##############################
        #decode 32bit header (4 bytes)
        ##############################
        hdrbuf = stream.read1(4)
        if not hdrbuf:
            return
        (hdr,) = struct.unpack(">I", hdrbuf)

        self.pkt_type = (hdr >> 28) & 0x0f     #(bit 28-31)
        self.class_id = (hdr >> 27) & 0x01     #(bit 27)
        self.reserved = (hdr >> 25) & 0x03     #(bit 25-26)
        self.tsm = (hdr >> 24) & 0x01          #(bit 24)
        self.tsi = (hdr >> 22) & 0x03          #(bit 22-23)
        self.tsf = (hdr >> 20) & 0x03          #(bit 20-21)
        self.seq_num = (hdr >> 16) & 0x0f      #(bit 16-19) #mod16 of pkt count (seqnum in difi spec)
        self.pkt_size = (hdr >> 0) & 0xffff    #(bit 0-15) #num 32bit words in pkt

        ##############################
        #decode stream id (4 bytes)
        ##############################
        idbuf = stream.read1(4)
        (value,) = struct.unpack(">I", idbuf)
        self.stream_id = value
        stream.seek(4) #backup to 4 to re-include stream id in data for decoding below

        if DEBUG: print("")
        if DEBUG: print("---")
        if DEBUG: print("DifiDataPacket header data in constructor:")
        if DEBUG: print("Header: %s" % (hdrbuf.hex()))
        if DEBUG: print("Header: %d" % (int.from_bytes(hdrbuf, byteorder='big', signed=False)))
        if DEBUG: print(f"Header: {(int.from_bytes(hdrbuf, byteorder='big', signed=False)):032b}")
        if DEBUG: print("stream id: 0x%08x" % (self.stream_id))
        if DEBUG: print("pkt type: 0x%01x" % (self.pkt_type))
        if DEBUG: print("classid: 0x%01x" % (self.class_id))
        if DEBUG: print("reserved: 0x%01x" % (self.reserved))
        if DEBUG: print("tsm: 0x%01x" % (self.tsm))
        if DEBUG: print("tsi: 0x%01x" % (self.tsi))
        if DEBUG: print("tsf: 0x%01x" % (self.tsf))
        if DEBUG: print("pkt count (mod16): %d" % (self.seq_num))  #packet_count
        if DEBUG: print("pkt size: %d" % (self.pkt_size)) #packet_size
        if DEBUG: print("---")

        #only allow if data packet type
        if self.pkt_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID:

            #only decode if header is valid
            if self.is_difi10_data_packet_header(self.pkt_type, self.class_id, self.reserved, self.tsm, self.tsf):
                packet_size_in_bytes = (self.pkt_size - 1) * 4  #less header (-1)
                context_data = stream.read1(packet_size_in_bytes)
                self._decode_standard_flow_signal_data_with_streamid(context_data)
            else:
                raise NoncompliantDifiPacket("non-compliant DIFI data packet header [packet type: 0x%1x]" % self.pkt_type, DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))
        else:
            raise NoncompliantDifiPacket("non-compliant packet type [0x%1x] for DIFI data packet  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (self.pkt_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))


    #function to decode data packet type
    def _decode_standard_flow_signal_data_with_streamid(self, data):

        if DEBUG: print("Decoding.....")
        #print(data.hex())

        try:
            #######################
            #Stream ID (5.1.2)
            #######################
            if DEBUG: print(data[0:4].hex())
            #already unpacked in constructor __init__
            #(value,) = struct.unpack(">I", data[0:4])
            #if DEBUG: print(" Stream ID = 0x%08x (ID)" % (value))
            #self.stream_id = value
            if DEBUG: print(" Stream ID = 0x%08x (ID)" % (self.stream_id))

            ##########################
            #OUI (5.1.3)
            ##########################
            if DEBUG: print(data[4:8].hex())
            #h = b'\x00\x7C\x38\x6C'
            #h = b'\x00\x00\x12\xa2'
            (value,) = struct.unpack(">I", data[4:8])
            value = value & 0x00FFFFFF
            if DEBUG: print(" OUI = 0x%06x" % (value))
            self.oui = value

            #########################
            #Information Class Code / Packet Class Code (5.1.3)
            ########################
            if DEBUG: print(data[8:12].hex())
            #h = b'\x00\x00\x00\x00'
            (icc,pcc) = struct.unpack(">HH", data[8:12])
            if DEBUG: print(" Information Class Code = 0x%04x - Packet Class Code = 0x%04x" % (icc, pcc))
            self.information_class_code = icc
            self.packet_class_code = pcc

            #######################
            #Integer-seconds Timestamp (5.1.4 and 5.1.5)
            #######################
            if DEBUG: print(data[12:16].hex())
            (value,) = struct.unpack(">I", data[12:16])
            if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')))
            #if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')))
            self.integer_seconds_timestamp = value
            self.integer_seconds_timestamp_display = datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')

            #######################
            #Fractional-seconds Timestamp (5.1.4 and 5.1.5)
            #######################
            if DEBUG: print(data[16:24].hex())
            (value,) = struct.unpack(">Q", data[16:24])
            if DEBUG: print(" Fractional-seconds Timestamp (picoseconds past integer seconds) = %d" % (value))
            self.fractional_seconds_timestamp = value

            #######################
            #Signal Data Payload
            #######################
            #payload size is size minus 28 bytes for difi headers
            # (7 words * 4 bytes per word) = 28 bytes
            #already removed 1st word of header earlier above
            # (28 bytes - 4 bytes) = 24 bytes
            self.payload_data_size_in_bytes = len(data) - 24
            self.payload_data_num_32bit_words = (len(data) - 24) / 4
            if DEBUG: print(". . .")
            if DEBUG: print(" Payload Data Size = %d (bytes), %d (32-bit words)" % (self.payload_data_size_in_bytes, self.payload_data_num_32bit_words))

            #TODO: should we include???????
            #self.payload_raw_data = data[24:]  #str(data[24:]) for json
            #self.payload_raw_hex_data = data[24:].hex()
            #words_list = [data[24:].hex()[i:i+8] for i in range(0,len(data[24:].hex()),8)]
            #print(type(words_list).__name__)
            #print(len(words_list))
            #print(words_list)
            #self.payload_raw_data_as_word_list = words_list
            #if DEBUG: print(" Payload Raw Data = %s" % (self.payload_raw_data))
            #if DEBUG: print(" Payload Raw Hex Data = %s" % (self.payload_raw_hex_data))
            #if DEBUG: print(" Payload Raw Data (list of words) = %s" % (self.payload_raw_data_as_word_list))

        except NoncompliantDifiPacket as e:
            raise e
        except Exception as e:
            raise e

        if DEBUG: print("Finished decoding.\r\n---\r\n")

        #debug
        #print("JSON dump object 'DifiDataPacket':\r\n\r\n", self.to_json())
        #print("String dump object 'DifiDataPacket':\r\n", str(self))


    #json encoder to change applicable int's to hex string
    class DataPacketHexJSONEncoder(json.JSONEncoder):

        def encode(self, o):
            d = o.copy()
            if type(d["pkt_type"]) is int:
                d.update(pkt_type = "0x%1x" % d["pkt_type"])
            if type(d["class_id"]) is int:
                d.update(class_id = "0x%1x" % d["class_id"])
            if type(d["reserved"]) is int:
                d.update(reserved = "0x%1x" % d["reserved"])
            if type(d["tsm"]) is int:
                d.update(tsm = "0x%1x" % d["tsm"])
            if type(d["tsi"]) is int:
                d.update(tsi = "0x%1x" % d["tsi"])
            if type(d["tsf"]) is int:
                d.update(tsf = "0x%1x" % d["tsf"])
            if type(d["stream_id"]) is int:
                d.update(stream_id = "0x%08x" % d["stream_id"])
            if type(d["oui"]) is int:
                d.update(oui = "0x%06x" % d["oui"])
            if type(d["information_class_code"]) is int:
                d.update(information_class_code = "0x%04x" % d["information_class_code"])
            if type(d["packet_class_code"]) is int:
                d.update(packet_class_code = "0x%04x" % d["packet_class_code"])
            return json.JSONEncoder.encode(self, d)


    def to_json(self, hex_values=False):
        #s = json.dumps(self, default=vars, indent=4)
        #s = json.loads(zlib.decompress(data))
        if hex_values is True:
            return json.dumps(self.__dict__, indent=4, cls=self.DataPacketHexJSONEncoder)
        else:
            return json.dumps(self, default=lambda o: o.__dict__, indent=4)


    def __str__(self):

        return ("Stream ID: 0x%08x (ID)\r\n\
OUI: 0x%06x\r\n\
Information Class Code: 0x%04x\r\n\
Packet Class Code: 0x%04x\r\n\
Integer-seconds Timestamp (seconds since epoch): %d (%s)\r\n\
Fractional-seconds Timestamp (picoseconds past integer-seconds): %d\r\n\
Payload Data Size: %d (bytes), %d (32-bit words)\r\n\
" % (self.stream_id,
    self.oui,
    self.information_class_code,
    self.packet_class_code,
    self.integer_seconds_timestamp,
    datetime.fromtimestamp(self.integer_seconds_timestamp, tz=timezone.utc).strftime('%m/%d/%Y %r %Z'),
    self.fractional_seconds_timestamp,
    self.payload_data_size_in_bytes,
    self.payload_data_num_32bit_words))

        #TODO: should we include RAW data fields in console output???????
        #Payload Raw Data: %s\r\n\
        #Payload Raw Hex Data: %s\r\n\
        #Payload Raw Data (list of words): %s\r\n\
        #self.payload_raw_data,
        #self.payload_raw_hex_data,
        #self.payload_raw_data_as_word_list


    ##############################
    #DIFI packet validation checks
    ##############################

    #data packet header
    def is_difi10_data_packet_header(self, packet_type, class_id, rsvd, tsm, tsf):
        return (packet_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID
            and class_id == DIFI_CLASSID
            and rsvd == DIFI_RESERVED
            and tsm == DIFI_TSM_DATA
            and tsf == DIFI_TSF_REALTIME_PICOSECONDS)



###############
#misc debugging-function to output roughly estimated packets p/sec to console
##############
def estimate_pkts_per_sec(counts: list)->int:

    #curr count - prev count
    per_sec_count = counts[0][1] - counts[0][0]
    print("pkts p/sec: {}".format(per_sec_count))
    timer = threading.Timer(1.0, estimate_pkts_per_sec, [counts])
    #change prev count to curr count
    counts[0][0] = counts[0][1]
    timer.daemon = True #allows timer to stop when main thread exits
    timer.start()



################
#function for processing data received from DIFI device
################
def process_data(data: Union[bytes,BytesIO]):

    if data is not None:

        try:
            if type(data) is bytes:
                stream = io.BytesIO(data)
            else:
                stream = data

            #parse data to create packet object
            pkt = decode_difi_vrt_packet(stream)
            #print("type: %s" % (type(pkt).__name__))

            #show resulting packet object in console
            if type(pkt) is DifiStandardContextPacket:
                if VERBOSE or DEBUG: print("\
-----------------------------\r\n\
-- standard context packet --\r\n\
-----------------------------\r\n\
%s\r\n\r\n%s" % (pkt.to_json(JSON_AS_HEX), str(pkt)))

                #update 'compliant' archive files
                write_compliant_count_to_file(pkt.stream_id)
                if SAVE_LAST_GOOD_PACKET:
                    write_compliant_to_file(pkt)

            elif type(pkt) is DifiVersionContextPacket:
                if VERBOSE or DEBUG: print("\
----------------------------\r\n\
-- version context packet --\r\n\
----------------------------\r\n\
%s\r\n\r\n%s" % (pkt.to_json(JSON_AS_HEX), str(pkt)))

                #update 'compliant' archive files
                write_compliant_count_to_file(pkt.stream_id)
                if SAVE_LAST_GOOD_PACKET:
                    write_compliant_to_file(pkt)

            elif type(pkt) is DifiDataPacket:
                if VERBOSE or DEBUG: print("\
-----------------\r\n\
-- data packet --\r\n\
-----------------\r\n\
%s\r\n\r\n%s" % (pkt.to_json(JSON_AS_HEX), str(pkt)))

                #update 'compliant' archive files
                write_compliant_count_to_file(pkt.stream_id)
                if SAVE_LAST_GOOD_PACKET:
                    write_compliant_to_file(pkt)
            else:
                #ignore if not standard context, version context or data packet
                pass

        except NoncompliantDifiPacket as e:
            #update 'non-compliant' archive files
            write_noncompliant_to_file(e)
            if VERBOSE or DEBUG: print(e.message)
            if VERBOSE or DEBUG: print("--> not DIFI compliant, packet not decoded:\r\n%s" % e.difi_info.to_json())
            write_noncompliant_count_to_file(e.difi_info.stream_id)
        except InvalidDataReceived as e:
            print("---------------")
            pprint.pprint(e)
            print("---------------")
        except InvalidPacketType as e:
            print("---------------")
            pprint.pprint(e)
            print("---------------")
        except Exception as e:
            print("---------------")
            print("packet decode error --> {}".format(e))
            print("---------------")
    else:
        print("packet received, but data empty.")



###################
#class to implement asyncio UDP server mode
###################
class DifiProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_connection_lost: asyncio.Future):
        super().__init__()
        self.on_connection_lost=on_connection_lost
        self.count=0
        self.q=asyncio.Queue()
        self.transport=None

    def connection_made(self, transport):
        self.transport = transport
        print('waiting to receive packet data...')

    def connection_lost(self, exc):
        self.on_connection_lost.set_result=True

    def datagram_received(self, data, addr):

        self.count+=1
        print('received {} bytes from {}. [count={}]'.format(len(data), addr, self.count))
        #print("packet data received: {}".format(data))

        #data = data.decode()

        #may want to put in queue instead and process data separately
        #self.q.put_nowait(data)
        #print("queue size: ", self.q.qsize())

        process_data(data)

        print('waiting to receive packet data...')

################
#main loop for asyncio UDP server mode
################
async def asyncio_main_loop():

    print('starting asyncio UDP listener on {} port {}...'.format(DIFI_RECEIVER_ADDRESS, DIFI_RECEIVER_PORT))

    #event loop
    loop = asyncio.get_running_loop()

    on_connection_lost = loop.create_future()

    #creates one protocol instance to serve all clients
    transport, protocol = await loop.create_datagram_endpoint(  # pylint: disable=unused-variable
        lambda: DifiProtocol(on_connection_lost),
        local_addr=(DIFI_RECEIVER_ADDRESS, DIFI_RECEIVER_PORT))

    try:
        await on_connection_lost
    finally:
        transport.close()



######################################
# main script
######################################

def main():
    # pylint: disable=global-statement,global-variable-not-assigned

    #constants in settings section at beginning of file
    global VERBOSE
    global DEBUG
    global SAVE_LAST_GOOD_PACKET
    global JSON_AS_HEX
    global SHOW_PKTS_PER_SEC
    global DIFI_RECEIVER_ADDRESS
    global DIFI_RECEIVER_PORT
    global MODE_SOCKET
    global MODE_ASYNCIO
    #global MODE_PCAP
    global MODE
    #global PCAP_FILE

    #debug - print command-line args
    #print("arguments: ", len(sys.argv))
    #print("argument list: ", str(sys.argv))

    #command-line args
    try:
        opts, args = getopt.getopt(sys.argv[1:],"",["ip=","port=","mode=","verbose=","save-last-packet=","json-as-hex=","debug="])  # pylint: disable=unused-variable
    except getopt.GetoptError:
        print("usage: drx.py\
    \r\n --port <port to listen on> (defaults to 4991)\
    \r\n --mode <%s or %s> (defaults to %s)\
    \r\n\r\n [options]\
    \r\n --verbose <True/False> (outputs the fully decoded packets to console)\
    \r\n --save-last-good-packet <True/False> (saves last decoded 'compliant' packet to file)\
    \r\n --json-as-hex <True/False> (converts applicable int fields in json doc to hex strings)\
    \r\n --debug <True/False> (outputs packet data and additional debugging info to console at runtime)" % (MODE_SOCKET, MODE_ASYNCIO, MODE_SOCKET))
        sys.exit(2)

    try:
        for opt, arg in opts:
            if opt == "--port":
                if len(arg) > 0:
                    DIFI_RECEIVER_PORT = int(arg)
            elif opt == "--mode":
                if arg not in (MODE_SOCKET, MODE_ASYNCIO):
                    raise InvalidArgs()
                MODE = arg
            elif opt == "--verbose":
                VERBOSE = (arg == "True")
            elif opt == "--save-last-good-packet":
                SAVE_LAST_GOOD_PACKET = (arg == "True")
            elif opt == "--json-as-hex":
                JSON_AS_HEX = (arg == "True")
            elif opt == "--debug":
                DEBUG = (arg == "True")
            elif opt == "--help":
                raise InvalidArgs()

    except InvalidArgs:
        print("usage: drx.py\
    \r\n --port <port to listen on> (defaults to 4991)\
    \r\n --mode <%s or %s> (defaults to %s)\
    \r\n\r\n [options]\
    \r\n --verbose <True/False> (outputs the fully decoded packets to console)\
    \r\n --save-last-good-packet <True/False> (saves last decoded 'compliant' packet to file)\
    \r\n --json-as-hex <True/False> (converts applicable int fields in json doc to hex strings)\
    \r\n --debug <True/False> (outputs packet data and additional debugging info to console at runtime)" % (MODE_SOCKET, MODE_ASYNCIO, MODE_SOCKET))
        sys.exit(2)

    #print("port: ", DIFI_RECEIVER_PORT)
    #print("mode: ", MODE)
    #print("verbose: ", VERBOSE)
    #print("debug: ", DEBUG)
    #print("save last good packet: ", SAVE_LAST_GOOD_PACKET)
    #print("json as hex: ", JSON_AS_HEX)
    #print("show pkts p/sec: ", SHOW_PKTS_PER_SEC)
    #sys.exit(0)



    #truncate all difi output files on startup
    truncate_all_difi_files()
    #TODO: should we change to delete instead of truncate???????
    #delete all difi output files on startup
    #delete_all_difi_files()


    ##########
    #asyncio udp socket server mode, listening for packets to decode
    ##########
    if MODE == MODE_ASYNCIO:

        #run async server
        print("entering asyncio.run...")
        asyncio.run(asyncio_main_loop())
        print("exited asyncio.run.")

        #print("entering asyncio.run...")
        #loop = asyncio.get_event_loop()
        #t = loop.create_datagram_endpoint(DifiProtocol, local_addr=(DIFI_RECEIVER_ADDRESS, DIFI_RECEIVER_PORT))
        #loop.run_until_complete(t) #starts listening
        #loop.run_forever()
        #print("exited asyncio.run.")



    ##########
    #udp socket server mode, listening for packets to decode
    ##########
    elif MODE == MODE_SOCKET:

        #create UDP socket listener
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #bind to port
        server_address = (DIFI_RECEIVER_ADDRESS, DIFI_RECEIVER_PORT)
        print('starting UDP listener on {} port {}...'.format(*server_address))
        sock.bind(server_address)

        #if set, output estimated pkts p/sec to console for debug purposes
        if SHOW_PKTS_PER_SEC:
            prev_curr_count = [0,0]
            estimate_pkts_per_sec([prev_curr_count])

        recv_count = 0

        #listen for packets
        while True:

            print('waiting to receive packet data...')
            data, address = sock.recvfrom(9216) #max data packet 9000 bytes, per difi spec

            recv_count+=1
            if SHOW_PKTS_PER_SEC: prev_curr_count[1] = recv_count
            print('received {} bytes from {}. [count={}]'.format(len(data), address, recv_count))
            #print("packet data received: {}".format(data))

            process_data(data)



    #pcap mode is currently disabled
    ##########
    #decode pcap file mode
    ##########
    #elif MODE == MODE_PCAP:
    #    preader = ppcap.Reader(filename=PCAP_FILE)
    #
    #    for ts, buf in preader:
    #
    #        eth = ethernet.Ethernet(buf)
    #
    #        if eth[ethernet.Ethernet,ip.IP] is not None:
    #
    #            #print("packet src\dest:  %s -> %s  [ts=%d]" % (eth[ip.IP].src_s, eth[ip.IP].dst_s, ts))
    #            #print("full packet: %s" % (eth.bin().hex()))
    #
    #            b = eth.bin()
    #            stream = io.BytesIO(b)
    #            eth_ip_udp_header = stream.read1(42)  #jump past: eth frame/ip hdr/udp hdr (42 bytes)
    #            try:
    #                #print("proto: ", eth_ip_udp_header[23:24])
    #                #only UDP packets
    #                if eth_ip_udp_header[23:24] == UDP_PROTO:
    #                    process_data(stream)
    #            except Exception as e:
    #                pprint.pprint(e)


if __name__ == '__main__':
    main()
