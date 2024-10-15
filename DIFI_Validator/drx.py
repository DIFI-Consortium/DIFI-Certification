"""
# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Copyright © `2023` `Microsoft Corporation`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT


Script that runs as socket server listening on port for DIFI packets being sent from a device.

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
import dpkt
import time
import yaml
import csv
from scapy.all import *

from difi_utils.difi_constants import *
from difi_utils.custom_error_types import *
from difi_utils.file_writing import *
from difi_utils.noncompliant_class import DifiInfo
from difi_utils.difi_data_packet_class import DifiDataPacket
if os.getenv("LEGACY_MODE"):
    print("Running in Legacy Mode!")
    time.sleep(1)
    from difi_utils.legacy_difi_context_packet_class import DifiStandardContextPacket
else:
    from difi_utils.difi_context_packet_class import DifiStandardContextPacket
from difi_utils.difi_version_packet_class import DifiVersionContextPacket

##########
# Settings
##########
VERBOSE = True  #prints fully decoded packets to console
DEBUG = False  #prints packet data and additional debugging info to console
LOG_PACKET = True  #saves decoded 'compliant' packet to file
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

PCAP_FILE = "example.pcap" # also include dir if its not in the dir you are currently running this script from
if os.getenv("PCAP_FILE"):
    PCAP_FILE = os.getenv("PCAP_FILE")

################
# Process packet received
################
def process_data(data: Union[bytes,BytesIO], timestamp=None, count=None):
    stream_id = ""
    if is_receive_enabled() == False:
        print("received packet while receive is disabled.")
        return
    if data is None:
        print("packet received, but data empty.")
        return
    try:
        if type(data) is bytes:
            stream = io.BytesIO(data)
        else:
            stream = data

        # packet type
        tmpbuf = stream.read1(4)
        if not tmpbuf:
            return None
        (value,) = struct.unpack(">I", tmpbuf)
        packet_type = (value >> 28) & 0x0f   #(bit 28-31)

        # stream id
        tmpbuf = stream.read1(4)
        (value,) = struct.unpack(">I", tmpbuf)
        stream_id = value

        stream.seek(0) #reset stream back to beginning

        # create instance of packet class for packet type and parse packet
        if packet_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT:
            pkt = DifiStandardContextPacket(stream) # parse
        elif packet_type == DIFI_VERSION_FLOW_SIGNAL_CONTEXT:
            pkt = DifiVersionContextPacket(stream)
        elif packet_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID:
            pkt = DifiDataPacket(stream)
        elif packet_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_NO_STREAMID: # DIFI doesnt support this type of packet
            raise NoncompliantDifiPacket("non-compliant DIFI data packet type [data packet without stream ID packet type: 0x%1x]  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (packet_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type=packet_type, stream_id=stream_id))
        else:
            raise NoncompliantDifiPacket("non-compliant DIFI packet type [0x%1x]  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (packet_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type, stream_id=stream_id))

        # Set timestamp
        pkt.packet_timestamp = timestamp
        pkt.pcap_index = count

        if VERBOSE or DEBUG: print("-----------------\r\n-- packet --\r\n-----------------\r\n%s\r\n\r\n%s" % (pkt.to_json(JSON_AS_HEX), str(pkt)))
        write_compliant_count_to_file(stream_id) # update 'compliant' archive files
        if LOG_PACKET:
            write_compliant_to_file(stream_id, pkt)

        return pkt # drx.py doesnt use the return but external uses of this function might

    except NoncompliantDifiPacket as e:
        write_noncompliant_to_file(stream_id, e) # update 'non-compliant' archive files
        if VERBOSE or DEBUG: print(e.message)
        if VERBOSE or DEBUG: print("--> not DIFI compliant, packet not decoded:\r\n%s" % e.difi_info.to_json())
        write_noncompliant_count_to_file(stream_id)
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


###############
# Recursive function to output estimated packets p/sec to console
##############
def estimate_pkts_per_sec(counts: list)->int:
    per_sec_count = counts[0][1] - counts[0][0] # curr count - prev count
    print("pkts p/sec: {}".format(per_sec_count))
    timer = threading.Timer(1.0, estimate_pkts_per_sec, [counts])
    counts[0][0] = counts[0][1] # change prev count to curr count
    timer.daemon = True #allows timer to stop when main thread exits
    timer.start()


#########################
# Asyncio UDP server mode
#########################
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
# Main loop for asyncio UDP server mode
################
async def asyncio_main_loop():
    print('starting asyncio UDP listener on {} port {}...'.format(DIFI_RECEIVER_ADDRESS, DIFI_RECEIVER_PORT))
    loop = asyncio.get_running_loop() # event loop
    on_connection_lost = loop.create_future()

    #creates one protocol instance to serve all clients
    transport, _ = await loop.create_datagram_endpoint(
        lambda: DifiProtocol(on_connection_lost),
        local_addr=(DIFI_RECEIVER_ADDRESS, DIFI_RECEIVER_PORT))
    try:
        await on_connection_lost
    finally:
        transport.close()


######################################
# Main/Entrypoint
######################################
def main():
    # pylint: disable=global-statement,global-variable-not-assigned

    #constants in settings section at beginning of file
    global VERBOSE
    global DEBUG
    global LOG_PACKET
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
                LOG_PACKET = (arg == "True")
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
    #print("save last good packet: ", LOG_PACKET)
    #print("json as hex: ", JSON_AS_HEX)
    #print("show pkts p/sec: ", SHOW_PKTS_PER_SEC)
    #sys.exit(0)

    #clear_all_difi_files() # clear out contents of all difi output files on startup
    delete_all_difi_files() # deleting feels cleaner, that way we can check if the file exists yet when writing a new item into it

    ##########
    # Asyncio udp socket server mode, listening for packets to decode
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
    # UDP socket server mode, listening for packets to decode
    ##########
    elif MODE == MODE_SOCKET:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # create UDP socket listener
        server_address = (DIFI_RECEIVER_ADDRESS, DIFI_RECEIVER_PORT) # bind to port
        print('starting UDP listener on {} port {}...'.format(*server_address))
        sock.bind(server_address)

        #if set, output estimated pkts p/sec to console for debug purposes
        if SHOW_PKTS_PER_SEC:
            prev_curr_count = [0,0]
            estimate_pkts_per_sec([prev_curr_count])

        # listen for packets
        recv_count = 0
        while True:
            print('waiting to receive packet data...')
            data, address = sock.recvfrom(9216) # max data packet 9000 bytes, per difi spec
            recv_count += 1
            if SHOW_PKTS_PER_SEC: prev_curr_count[1] = recv_count
            print('received {} bytes from {}. [count={}]'.format(len(data), address, recv_count))
            #print("packet data received: {}".format(data))
            process_data(data)


    ################
    # PCAP file mode
    ################
    elif MODE == MODE_PCAP:
        print("Reading in all packets, may take some time")
        count = 0
        for packet in PcapReader(PCAP_FILE):
            ts = float(packet.time)
            if UDP in packet:
                #print(packet[UDP].dport)
                #print(packet[UDP].sport)
                payload = bytes(packet[UDP].payload)
                process_data(payload, timestamp=ts, count=count)
                count += 1
            elif TCP in packet:
                pass # TODO

        # Pull results from files
        report = {} # gets dumped to yaml at the end as a form of report
        csv_data = []

        # Pull out counts from file
        report["compliant-count"] = 0
        if os.path.exists('difi-compliant-count.dat'):
            with open("difi-compliant-count.dat", 'r', encoding="utf-8") as f:
                buf = f.read()
                if len(buf) > 0:
                    report["compliant-count"] = int(buf.split("#", 1)[0])

        report["noncompliant-count"] = 0
        if os.path.exists("difi-noncompliant-count.dat"):
            with open("difi-noncompliant-count.dat", 'r', encoding="utf-8") as f:
                buf = f.read()
                if len(buf) > 0:
                    report["noncompliant-count"] = int(buf.split("#", 1)[0])

        ###################
        # Post-processing #
        ###################

        #time.sleep(10) # time to mess with log file

        # Check if sequence numbers were all in order for data packets
        print("Analyzing Sequence Numbers")
        report["data-packet-count"] = 0
        if os.path.exists('difi-compliant-data.dat'):
            with open('difi-compliant-data.dat') as f:
                data_packets = json.load(f)
            report["data-packet-count"] = len(data_packets)
            last_seq_num = -1
            error_count = 0
            for packet in data_packets:
                seq_num = packet.get("seq_num", -1)
                if last_seq_num != -1 and seq_num != (last_seq_num+1):
                    if not (seq_num == 0 and last_seq_num == 15):
                        error_count += 1
                last_seq_num = seq_num
                csv_data.append([packet.get("pcap_index", ""),
                                 packet.get("pkt_type", ""),
                                 packet.get("seq_num", ""),
                                 packet.get("packet_timestamp", ""),
                                 packet.get("integer_seconds_timestamp", ""),
                                 packet.get("fractional_seconds_timestamp", "")])
            print(error_count, "out of", len(data_packets), "packets had erroneous sequence numbers")

            # Analyze packet timestamps
            start_t = data_packets[0]["packet_timestamp"] # UTC seconds float
            time_log = []
            for packet in data_packets:
                packet_t = packet["packet_timestamp"]
                diff = (packet_t - start_t)*1e3 # ms
                time_log.append(diff)
            import matplotlib.pyplot as plt
            import numpy as np

            plt.figure(0)
            plt.hist(time_log, bins=20)
            plt.xlabel("Time Packets Arrived [ms]")
            plt.ylabel("Histogram")
            plt.savefig('packet_histogram.png', bbox_inches='tight')
            #plt.show()

            plt.figure(1)
            plt.hist(np.diff(time_log), bins=20)
            plt.xlabel("Time Between Packets [ms]")
            plt.ylabel("Histogram")
            plt.savefig('packet_diff_histogram.png', bbox_inches='tight')
            #plt.show()

        # Check context packets
        report["data-context-count"] = 0
        if os.path.exists('difi-compliant-context.dat'):
            with open('difi-compliant-context.dat') as f:
                context_packets = json.load(f)
            report["data-context-count"] = len(context_packets)

            # Find avg time between context packets
            start_t = context_packets[0]["packet_timestamp"] # UTC seconds float
            time_log = []
            for packet in context_packets:
                packet_t = packet["packet_timestamp"]
                diff = (packet_t - start_t)*1e3 # ms
                time_log.append(diff)
                csv_data.append([packet.get("pcap_index", ""),
                                 packet.get("pkt_type", ""),
                                 packet.get("seq_num", ""),
                                 packet.get("packet_timestamp", ""),
                                 packet.get("integer_seconds_timestamp", ""),
                                 packet.get("fractional_seconds_timestamp", "")])
            report["avg-time-betwee-context-packets-in-ms"] = float(np.mean(time_log))

        report["pass"] = (report["noncompliant-count"] == 0)

        print(report)
        with open('report.yaml', 'w+') as f:
            yaml.dump(report, f, allow_unicode=True)

        # Make CSV file
        with open('log.csv', 'w') as f:
            f.write('pcap index,packet type,seq num,packet timestamp,int seconds,frac seconds\n')
            writer = csv.writer(f)
            for row in csv_data:
                writer.writerow(row)



if __name__ == '__main__':
    main()
