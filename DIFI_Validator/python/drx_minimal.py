"""
This script is a copy of drx.py but was minimized to be suitable for tutorial purpose, and only works on data packets
"""


from __future__ import annotations
from typing import Union
from datetime import timezone, datetime
import struct
import io
from io import BytesIO
import json
import socket



##########
#settings
##########
VERBOSE = True  #prints fully decoded packets to console
DEBUG = False  #prints packet data and additional debugging info to console
SAVE_LAST_GOOD_PACKET = True  #saves last decoded 'compliant' packet to file
JSON_AS_HEX = False  #converts applicable int fields in json doc to hex strings
SHOW_PKTS_PER_SEC = False  #outputs estimated packets p/sec to console for debugging purposes

DIFI_RECEIVER_ADDRESS = "0.0.0.0" #default
DIFI_RECEIVER_PORT = 1234 #default
MODE_SOCKET = "socket"
MODE_ASYNCIO = "asyncio"
MODE = MODE_SOCKET

#DIFI packet types
DIFI_STANDARD_FLOW_SIGNAL_CONTEXT = 0x4
DIFI_VERSION_FLOW_SIGNAL_CONTEXT = 0x5
DIFI_STANDARD_FLOW_SIGNAL_DATA = 0x1

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


############################
#primary function that decodes DIFI packets
############################
def decode_difi_vrt_packet(stream: BytesIO):
    #get packet type
    tmpbuf = stream.read1(4)
    if not tmpbuf:
        return None
    (value,) = struct.unpack(">I", tmpbuf)
    packet_type = (value >> 28) & 0x0f   #(bit 28-31)
    print("packet type:", packet_type)

    #get stream id
    tmpbuf = stream.read1(4)
    (value,) = struct.unpack(">I", tmpbuf)
    stream_id = value
    print("stream id:", stream_id)

    stream.seek(0) #reset stream back to beginning

    if packet_type != DIFI_STANDARD_FLOW_SIGNAL_DATA:
        print("Packet type parsing not implemented")

    ##############################
    #decode 32bit header (4 bytes)
    ##############################
    hdrbuf = stream.read1(4)
    if not hdrbuf:
        return
    (hdr,) = struct.unpack(">I", hdrbuf)

    pkt_type = (hdr >> 28) & 0x0f     #(bit 28-31)
    class_id = (hdr >> 27) & 0x01     #(bit 27)
    reserved = (hdr >> 25) & 0x03     #(bit 25-26)
    tsm = (hdr >> 24) & 0x01          #(bit 24)
    tsi = (hdr >> 22) & 0x03          #(bit 22-23)
    tsf = (hdr >> 20) & 0x03          #(bit 20-21)
    seq_num = (hdr >> 16) & 0x0f      #(bit 16-19) #mod16 of pkt count (seqnum in difi spec)
    pkt_size = (hdr >> 0) & 0xffff    #(bit 0-15) #num 32bit words in pkt

    ##############################
    #decode stream id (4 bytes)
    ##############################
    idbuf = stream.read1(4)
    (value,) = struct.unpack(">I", idbuf)
    stream_id = value
    stream.seek(4) #backup to 4 to re-include stream id in data for decoding below

    print("")
    print("---")
    print("DifiDataPacket header data in constructor:")
    print("Header: %s" % (hdrbuf.hex()))
    print("Header: %d" % (int.from_bytes(hdrbuf, byteorder='big', signed=False)))
    print(f"Header: {(int.from_bytes(hdrbuf, byteorder='big', signed=False)):032b}")
    print("stream id: 0x%08x" % (stream_id))
    print("pkt type: 0x%01x" % (pkt_type))
    print("classid: 0x%01x" % (class_id))
    print("reserved: 0x%01x" % (reserved))
    print("tsm: 0x%01x" % (tsm))
    print("tsi: 0x%01x" % (tsi))
    print("tsf: 0x%01x" % (tsf))
    print("pkt count (mod16): %d" % (seq_num))  #packet_count
    print("pkt size: %d" % (pkt_size)) #packet_size
    print("---")

    packet_size_in_bytes = (pkt_size - 1) * 4  #less header (-1)
    context_data = stream.read1(packet_size_in_bytes)

    #######################
    #Stream ID (5.1.2)
    #######################
    print(context_data[0:4].hex())
    print(" Stream ID = 0x%08x (ID)" % (stream_id))

    ##########################
    #OUI (5.1.3)
    ##########################
    print(context_data[4:8].hex())
    #h = b'\x00\x7C\x38\x6C'
    #h = b'\x00\x00\x12\xa2'
    (value,) = struct.unpack(">I", context_data[4:8])
    value = value & 0x00FFFFFF
    print(" OUI = 0x%06x" % (value))
    oui = value

    #########################
    #Information Class Code / Packet Class Code (5.1.3)
    ########################
    print(context_data[8:12].hex())
    #h = b'\x00\x00\x00\x00'
    (icc,pcc) = struct.unpack(">HH", context_data[8:12])
    print(" Information Class Code = 0x%04x - Packet Class Code = 0x%04x" % (icc, pcc))
    information_class_code = icc
    packet_class_code = pcc

    #######################
    #Integer-seconds Timestamp (5.1.4 and 5.1.5)
    #######################
    print(context_data[12:16].hex())
    (value,) = struct.unpack(">I", context_data[12:16])
    print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')))
    #print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')))
    integer_seconds_timestamp = value
    integer_seconds_timestamp_display = datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')

    #######################
    #Fractional-seconds Timestamp (5.1.4 and 5.1.5)
    #######################
    print(context_data[16:24].hex())
    (value,) = struct.unpack(">Q", context_data[16:24])
    print(" Fractional-seconds Timestamp (picoseconds past integer seconds) = %d" % (value))
    fractional_seconds_timestamp = value

    #######################
    #Signal Data Payload
    #######################
    #payload size is size minus 28 bytes for difi headers
    # (7 words * 4 bytes per word) = 28 bytes
    #already removed 1st word of header earlier above
    # (28 bytes - 4 bytes) = 24 bytes
    payload_data_size_in_bytes = len(context_data) - 24
    payload_data_num_32bit_words = (len(context_data) - 24) / 4
    print(". . .")
    print(" Payload Data Size = %d (bytes), %d (32-bit words)" % (payload_data_size_in_bytes, payload_data_num_32bit_words))




######################################
# main script
######################################

#create UDP socket listener
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#bind to port
server_address = (DIFI_RECEIVER_ADDRESS, DIFI_RECEIVER_PORT)
print('starting UDP listener on {} port {}...'.format(*server_address))
sock.bind(server_address)

#listen for packets
recv_count = 0
while True:
    print('waiting to receive packet data...')
    data, address = sock.recvfrom(9216) # max data packet 9000 bytes, per difi spec
    recv_count+=1
    print('received {} bytes from {}. [count={}]'.format(len(data), address, recv_count))
    print("packet data received: {}".format(data))
    stream = io.BytesIO(data)
    decode_difi_vrt_packet(stream)

