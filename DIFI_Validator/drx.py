"""
# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Copyright © `2023` `Microsoft Corporation`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT


Script that runs as socket server listening on port for DIFI packets being sent from a device.

(Supports: DIFI 1.0 spec - "IEEE-ISTO Std4900-2021: Digital IF Interoperability Standard Version 1.0 August 18,2021")

Currently can run in three modes:
1) 'socket' -regular socket server listening (default if not supplied)
2) 'asyncio' -asyncio socket server listening
3) 'pcap' -pcap file decoder (this mode currently disabled)

Run using:
    python3 drx.py   (defaults to: port 4991, local machine's IP, socket mode, verbose, save last good packet)
    python3 drx.py --port 4991
    python3 drx.py --port 4991 --mode asyncio
    python3 drx.py --port 4991 --mode socket --verbose True --debug True

It saves results of packets received to files, including compliant and metadata. 
Tail command locally in console on any one of the result files:
    tail -f difi-compliant-standard-context-00000001.dat
    tail -f difi-compliant-standard-context-00000001.dat 2> >(grep -v truncated >&2)
    (note: 00000001 is stream id in these examples)

This code is structured so that functionality can also be imported into other Python scripts.
"""

from __future__ import annotations

from typing import Union
import asyncio
import struct
import io
from io import BytesIO
import sys
import pprint
import socket
import getopt
import os
import threading

from utils.difiConstants import *
from utils.customErrorTypes import *
from utils.fileWriting import *
from utils.nonCompliantClass import DifiInfo
from utils.difiDataPacketClass import DifiDataPacket
from utils.difiContextPacketClass import DifiStandardContextPacket
from utils.difiVersionPacketClass import DifiVersionContextPacket

##########
# Settings
##########
VERBOSE = True  #prints fully decoded packets to console
DEBUG = False  #prints packet data and additional debugging info to console
SAVE_LAST_GOOD_PACKET = True  #saves last decoded 'compliant' packet to file
JSON_AS_HEX = False  #converts applicable int fields in json doc to hex strings
SHOW_PKTS_PER_SEC = False  #outputs estimated packets p/sec to console for debugging purposes

DIFI_RECEIVER_ADDRESS = "0.0.0.0"
DIFI_RECEIVER_PORT = 4991
if os.getenv("DIFI_RX_HOST"):
    DIFI_RECEIVER_ADDRESS = os.getenv("DIFI_RX_HOST")
if os.getenv("DIFI_RX_PORT"):
    DIFI_RECEIVER_PORT = int(os.getenv("DIFI_RX_PORT"))

# Modes
MODE_SOCKET = "socket"   # constant
MODE_ASYNCIO = "asyncio" # constant
MODE_PCAP = "pcap"       # constant. pcap mode is currently disabled

MODE = MODE_SOCKET # Define mode here (or through env var)
if os.getenv("DIFI_RX_MODE"):
    MODE = os.getenv("DIFI_RX_MODE")

#PCAP_FILE = "difi-compliant.pcap"


############################
# primary function that decodes DIFI packets
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


###############
# misc debugging-function to output roughly estimated packets p/sec to console
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
# function for processing data received from DIFI device
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
# class to implement asyncio UDP server mode
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
# main loop for asyncio UDP server mode
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
    
    #delete all difi output files on startup
    #delete_all_difi_files()


    ##########
    # asyncio udp socket server mode, listening for packets to decode
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
    # udp socket server mode, listening for packets to decode
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
    #from pypacker import ppcap
    #from pypacker.pypacker import byte2hex
    #from pypacker.layer12 import ethernet
    #from pypacker.layer3 import ip
    #from pypacker.layer4 import tcp
    #from pypacker.layer4 import udp
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
