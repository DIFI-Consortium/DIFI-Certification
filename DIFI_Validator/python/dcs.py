"""
# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT
#
# DIFI Standard Context Packet Sender, DCS
#
#
# Sends DIFI 'Standard Flow Signal Context Packet' (packet type = 0x4) to IP and port specified.
#
# Options:
# 1) can send 1 packet
# 2) can send N count of packets (see --help for usage)
# 3) can send packets for specified duration (see --help for usage)
#    note: can also specify sleep time between sends (see --help for usage)
#
# Type of packet:
# 1) can send DIFI 'compliant' packets
# 2) can send DIFI 'non-compliant' packets (having field values not allowed by DIFI)
#
# Console output:
# 1) can run in 'silent' mode (for high speed sending, overrides debug mode)
# 2) can run in 'debug' mode (prints packet data and additional info to console for troubleshooting problems)
#    note: prints packet sent message to console by default
#
# Can also import into other projects:
# [Example]
# import dcs
# import sys
# try:
#     dcs.DESTINATION_IP = "10.1.1.1"
#     dcs.DESTINATION_PORT = 4991
#     dcs.STREAM_ID = 4
#     dcs.FIELDS["--bandwidth"] = "2.0"
#     dcs.send_difi_compliant_standard_context_packet()
# except Exception as e:
#     print(e)
# sys.exit(2)
"""

import sys
import socket
import time
import getopt
import asyncio

import dificommon

#   3                   2                   1                   0
# 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |Pckt T.|C|Indi.| T.|TSF|Packet.|          Packet Size          |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                           Stream ID                           |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |    Pad  |  Res|                      OUI                      |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |           Info Class          |          Packet Class         |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                      Integer Sec Timestamp                    |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# +                  Fractional-Seconds Timestamp                 +
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                       Context Indicators                      |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                         Reference Point                       |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# +                            Bandwidth                          +
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# +                     IF Reference Freqency                     +
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# +                       RF Reference Freq                       +
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# +                         IF Band Offset                        +
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                         Reference Level                       |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                       Gain & Attenuation                      |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# +                          Sample Rate                          +
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# +                      Timestamp Adjustment                     +
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                Timestamp Calibration Time (sec)               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                   State and Event Indicators                  |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# +                   Data Packet Payload Format                  +
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

# Data Types
# Use IEEE-754 floating point arithmetic,
# map Python floats to IEEE-754 “double precision”.
# 754 doubles contain 53 bits of precision, so on input the computer strives to
# convert 0.1 to the closest fraction it can of the form J/2**N where J is
# an integer containing exactly 53 bits.


###########
# settings
###########
DESTINATION_IP = None  #dest address to send packets to
DESTINATION_PORT = None  #dest port to send packets to
STREAM_ID = 0x00000001  #32bit int id of stream, defaults to 1 if arg not supplied

SILENT = False  #prints nothing to the console (for high-speed sending)
DEBUG = False  #prints packet data and additional debugging info to the console

#send mode (must be either seconds or count, specifying both is not supported)
SECONDS_TO_SEND = None  #default is None, meaning only 1 packet will be sent
COUNT_TO_SEND = None  #default is None, meaning only 1 packet will be sent

SECONDS_BETWEEN_SENDS = 1  #default is 1 second if arg not supplied

#args supplying field values
FIELDS={}



###########
# primary function
###########
def send_difi_compliant_standard_context_packet(count: int = 0):

    # create the socket
    udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    # prep  vita/difi payload
    difi_packet = bytearray()

    # 1st 16 bits of header in hex.  #4B61
    pkt_type = FIELDS["--pkt-type"] if "--pkt-type" in FIELDS else "4" #hex
    clsid = FIELDS["--clsid"] if "--clsid" in FIELDS else "1" #hex
    rsvd = FIELDS["--rsvd"] if "--rsvd" in FIELDS else "0" #hex
    tsm = FIELDS["--tsm"] if "--tsm" in FIELDS else "1" #hex
    tsi = FIELDS["--tsi"] if "--tsi" in FIELDS else "1" #hex
    tsf = FIELDS["--tsf"] if "--tsf" in FIELDS else "2" #hex

    clsid_rsvd_tsm_tsi_tsf = "%02x" % (int("%s%s%s%s%s" % (
        "{0:01b}".format(int(clsid,16)),
        "{0:02b}".format(int(rsvd,16)),
        "{0:01b}".format(int(tsm,16)),
        "{0:02b}".format(int(tsi,16)),
        "{0:02b}".format(int(tsf,16))), 2))

    if "--seqnum" in FIELDS and FIELDS["--seqnum"] is not None:
        seqnum = FIELDS["--seqnum"] if "--seqnum" in FIELDS else "0" #hex
    else:
        seqnum = "%01x" % (count % 16)

    first_half_header = "%s%s%s" % (pkt_type, clsid_rsvd_tsm_tsi_tsf, seqnum)
    packetchunk = bytearray.fromhex(first_half_header) #(4B61) #clsid=0x1,tsm=0x1,tsf=0x2
    difi_packet.extend(packetchunk)

    # 2nd 16 bits of header in hex, (Packet Size) 001B = 27
    packetchunk = bytearray.fromhex("{0:04x}".format(int(FIELDS["--pkt-size"],16)) if "--pkt-size" in FIELDS else "001B")
    difi_packet.extend(packetchunk)

    # Context Header, size 27
    # Example "4B:61:00:1B" in Binary
    #                  0100 1011 0110 0001 0000 0000 0001 1011

    # Extend each section of new packet into the 'difi_packet' structure.

    # STREAM_ID = 1
    if type(STREAM_ID) is int:
        stream_id_int = STREAM_ID
    else:
        if str(STREAM_ID).lower().startswith("0x"):
            stream_id_int = int(STREAM_ID,16)
        else:
            stream_id_int = int(STREAM_ID,10)

    stream_hex_int = '0x{0:08X}'.format(stream_id_int)
    if not SILENT: print(f"STREAM_ID (hex) = {stream_hex_int}")
    #packetchunk = bytearray.fromhex(stream_hex_int)            # Stream ID
    a_bytes_big = stream_id_int.to_bytes(4, 'big')
    #packetchunk = bytearray.frombuffer(a_bytes_big)
    difi_packet.extend(a_bytes_big)

    # Vita OUI 00-12-A2
    packetchunk = bytearray.fromhex("00{0:06x}".format(int(FIELDS["--oui"],16)) if "--oui" in FIELDS else "000012A2")                 # XX:000012A2  XX:OUI for Vita
    #packetchunk = bytearray.fromhex("007C386C")                # XX:007c386c  XX:OUI Difi Default
    difi_packet.extend(packetchunk)

    packetchunk = bytearray.fromhex("%s%s" % ("{0:04x}".format(int(FIELDS["--icc"],16)) if "--icc" in FIELDS else "0000", "{0:04x}".format(int(FIELDS["--pcc"],16)) if "--pcc" in FIELDS else "0000"))                 # Info Class Code, Packet Class Code #icc=0x0000,pcc=0x0000
    difi_packet.extend(packetchunk)

    packet_timestamp = format(int(time.time()),'x')            # Timestamp
    difi_packet.extend(bytearray.fromhex("{0:08x}".format(int(FIELDS["--integer-seconds-ts"])) if "--integer-seconds-ts" in FIELDS else packet_timestamp))
    #difi_packet.extend(packetchunk)

    packetchunk = bytearray.fromhex("{0:016x}".format(int(FIELDS["--fractional-seconds-ts"])) if "--fractional-seconds-ts" in FIELDS else "0000000000000001")         # Fractional Timestamp
    difi_packet.extend(packetchunk)

    packetchunk = bytearray.fromhex("{0:08x}".format(int(FIELDS["--cif0"],16)) if "--cif0" in FIELDS else "FBB98000")                 # Context indicator field (context change) #cif0=0xBB98000
    # OR
    # packetchunk = bytearray.fromhex("7BB98000")                 # Context indicator field (No change) #cif0=0xBB98000
    difi_packet.extend(packetchunk)

    # arbitrary ID for point of reference (sub category of of stream id)
    packetchunk = bytearray.fromhex("{0:08x}".format(int(FIELDS["--ref-point"],16)) if "--ref-point" in FIELDS else "00000064")                 # Ref point
    difi_packet.extend(packetchunk)

    #  Bandwidth
    # 64-bit, two’s-complement
    # 0x0000 0000 0010 0000 represents a bandwidth of 1 Hz.
    # value /= 2.0 ** 20
    # bndwdth = 1
    # bndwdth_hex_int = '0x{0:08X}'.format(bndwdth)
    # 0x0000 0000 0000 0001 = 0.95 micro-Hertz
    packetchunk = bytearray.fromhex("{0:016x}".format(round(float(float(FIELDS["--bandwidth"]) * (2**20)))) if "--bandwidth" in FIELDS else "0000000000100000")         # Bandwidth
    # packetchunk = bytearray.fromhex(bndwdth)         # Bandwidth
    difi_packet.extend(packetchunk)

    # IF ref Freq
    # The spectral band described by the Bandwidth field is typically oriented
    # symmetrically about the IF Reference Frequency
    #packetchunk = bytearray.fromhex("0000000000100000")         # IF ref Freq 1 Hz
    packetchunk = bytearray.fromhex("{0:016x}".format(round(float(float(FIELDS["--if-ref-freq"]) * (2**20))) & (2**64-1)) if "--if-ref-freq" in FIELDS else "0000000000000000")         # IF ref Freq 0 Hz, as per spec.
    # note, was RF Ref freq in prev doc.
    difi_packet.extend(packetchunk)

    packetchunk = bytearray.fromhex("{0:016x}".format(round(float(float(FIELDS["--rf-ref-freq"]) * (2**20))) & (2**64-1)) if "--rf-ref-freq" in FIELDS else "0000000000200000")         # RF ref Freq
    difi_packet.extend(packetchunk)

    # The IF Band Offset ---------------------------------------------------------------------
    # field shall use the 64-bit, two’s-complement format, with an integer and
    # a fractional part, with the radix point to the right of bit 20 in the second 32-bit word
    # Band Offset field value of 0x0000 0000 0010 0000 is  a band offset of # +1 Hz.
    # Band Offset field value of 0xFFFF FFFF FFF0 0000  is (-) negative 1 Hz
    # Band Offset field value of 0x0000 0000 0000 0001 is a band offset of +0.95 micro-Hertz. An IF
    # Band Offset field value of 0xFFFF FFFF FFFF FFFF is  a band offset of (-)0.95 micro-Hertz.

    packetchunk = bytearray.fromhex("{0:016x}".format(round(float(float(FIELDS["--if-band-offset"]) * (2**20))) & (2**64-1)) if "--if-band-offset" in FIELDS else "FFFFFFFFFFF00000")         # IF band offset
    difi_packet.extend(packetchunk)

    # A Reference Level field value of 0x0000 0080 represents a reference level of +1 dBm.
    packetchunk = bytearray.fromhex("0000{0:04x}".format(round(float(float(FIELDS["--ref-level"]) * (2**7))) & (2**16-1)) if "--ref-level" in FIELDS else "00000080")                 # Ref Level
    difi_packet.extend(packetchunk)

    # gain 2 parts, radix at 7
    # 0x0000 FF80  = negative 1 hz
    # 0x0000 0080  = positive 1 hz
    packetchunk = bytearray.fromhex("%s%s" % ("{0:04x}".format(round(float(float(FIELDS["--gain-att-stage2"]) * (2**7))) & (2**16-1)) if "--gain-att-stage2" in FIELDS else "0000", "{0:04x}".format(round(float(float(FIELDS["--gain-att-stage1"]) * (2**7))) & (2**16-1)) if "--gain-att-stage1" in FIELDS else "FF80"))         # Gain  (+1 db)  # page 152 example  #0000FF80
    difi_packet.extend(packetchunk)

    # 0x0000 0000 0000 0001 represents a sample rate of 0.95 micro-Hertz
    packetchunk = bytearray.fromhex("{0:016x}".format(round(float(float(FIELDS["--sample-rate"]) * (2**20)))) if "--sample-rate" in FIELDS else "0000000000000003")         # Sample Rate "Sample/s"
    difi_packet.extend(packetchunk)

    # The Timestamp Adjustment
    # is the analog and digital processing delay from the location in the system
    # that the timestamp is generated to the location referred to by the Reference Point
    # Stream Identifier.
    # This adjustment can be a negative number (Rx chain) or a positive number (Tx Chain)
    # and when added to the packet timestamp indicates
    # the time the information in the Signal Data Packet from the Reference Point.
    # Timestamp Adjustment field shall use [Fractional Time] data type
    # The [Fractional Time] field definition is not the same as the Fractional Timestamp
    # definition.
    # [Fractional Time]      has an LSB of 1 femtosecond
    # [Fractional Timestamp] has an LSB of 1 picosecond
    # Fractional Time shall be a 64-bit two’s complement integer occupying two consecutive
    # 32-bit words in the packet as shown in Figure 9.7-3. The most significant 32 bits shall be in the first of
    # these two words. The lsb of each word shall be on the right
    # 0000 0000 0000 0001  = 1 ps
    packetchunk = bytearray.fromhex("{0:016x}".format(int(FIELDS["--ts-adjustment"])) if "--ts-adjustment" in FIELDS else "0000000000000004")         # Timestamp Adjustment 1&2
    difi_packet.extend(packetchunk)

    # RE-use packet_timestamp for calibration
    difi_packet.extend(bytearray.fromhex("{0:08x}".format(int(FIELDS["--ts-calibration"])) if "--ts-calibration" in FIELDS else packet_timestamp))

    # State and Event Indicator Bit Definitions
    # ___________________________________________________________________
    # Enable Bit |  Indicator Bit  | Indicator Name  | Period of Validity
    #  Position  |  Position       |                 |
    # ___________________________________________________________________
    # 31         | 19              |  Calibrated Time Indicator Persistent
    # 30         | 18              |  Valid Data Indicator Persistent
    # 29         | 17              |  Reference Lock Indicator Persistent
    # 28         | 16              |  AGC/MGC Indicator Persistent
    # 27         | 15              |  Detected Signal Indicator Persistent
    # 26         | 14              |  Spectral Inversion Indicator Persistent
    # 25         | 13              |  Over-range Indicator Single Data Packet
    # 24         | 12              |  Sample Loss Indicator Single Data Packet
    # [23..20] [11..8] Reserved N/A
    # Bit Position Function
    # [7..0] User-Defined User-Defined

    # 31 19 Calibrated Time Indicator
    # 29 17 Reference Lock Indicator
    # "000A0000"
    sei_bits = "000000000000%s%s%s%s%s%s%s%s000000000000" % (
            "1" if "--sei-bit19" in FIELDS else "0",
            "1" if "--sei-bit18" in FIELDS else "0",
            "1" if "--sei-bit17" in FIELDS else "0",
            "1" if "--sei-bit16" in FIELDS else "0",
            "1" if "--sei-bit15" in FIELDS else "0",
            "1" if "--sei-bit14" in FIELDS else "0",
            "1" if "--sei-bit13" in FIELDS else "0",
            "1" if "--sei-bit12" in FIELDS else "0")
    packetchunk = bytearray.fromhex("{0:08x}".format(int(sei_bits,2)) if sei_bits != "00000000000000000000000000000000" else "000A0000")
    # State and Event Indicators
    difi_packet.extend(packetchunk)

    # 0100 1011 0000 1110 0000 0000 0001 0010

    # Figure B-37 shows a specific Data Packet Payload Field for a real, 32-bit, signed, fixed-point payload.
    # This field contains the hexadecimal words 0x000007DF and 0x00000000.
    # 0A00 0000 0000 0000
    #packetchunk = bytearray.fromhex("000007DF00000000")         # Spec Ex Data Packet Payload Format 1&2
    #packetchunk = bytearray.fromhex("A00000C300000000")         # Data Packet Payload Format 1&2

    # Figure B-44 shows 14-bit real data / unsigned fixed pt  / link-efficient packing.
    # This field contains the hexadecimal words 0x9000034D and 0x00000000.
    ###packetchunk = bytearray.fromhex("9000034D00000000")

    # Figure B-47 shows real data / signed fixed pt / processing-efficient / 2 event tags.
    # This field contains the hexadecimal words 0x00200247 and 0x00000000.
    #packetchunk = bytearray.fromhex("0020024700000000")

    # Figure B-51 shows complex cartesian data / signed fixed pt / sample component repeating.
    # This field contains the hexadecimal words 0x208001C7 and 0x00030000.
    #packetchunk = bytearray.fromhex("208001C700030000")

    pk_mh = FIELDS["--dpf-pk-mh"] if "--dpf-pk-mh" in FIELDS else "1"
    real_cmp_type = FIELDS["--dpf-real-cmp-type"] if "--dpf-real-cmp-type" in FIELDS else "1"
    data_item_format = FIELDS["--dpf-data-item-format"] if "--dpf-data-item-format" in FIELDS else "0"
    rpt_ind = FIELDS["--dpf-rpt-ind"] if "--dpf-rpt-ind" in FIELDS else "0"
    event_tag_size = FIELDS["--dpf-event-tag-size"] if "--dpf-event-tag-size" in FIELDS else "0"
    channel_tag_size = FIELDS["--dpf-channel-tag-size"] if "--dpf-channel-tag-size" in FIELDS else "0"

    data_item_fraction_size = FIELDS["--dpf-data-item-fraction-size"] if "--dpf-data-item-fraction-size" in FIELDS else "0"
    item_packing_field_size = FIELDS["--dpf-item-packing-field-size"] if "--dpf-item-packing-field-size" in FIELDS else "13"
    data_item_size = FIELDS["--dpf-data-item-size"] if "--dpf-data-item-size" in FIELDS else "13"

    dpf_hex_1 = "%08x" % (int("%s%s%s%s%s%s%s%s%s" % (
        "{0:01b}".format(int(pk_mh,10)),
        "{0:02b}".format(int(real_cmp_type,10)),
        "{0:05b}".format(int(data_item_format,10)),
        "{0:01b}".format(int(rpt_ind,10)),
        "{0:03b}".format(int(event_tag_size,10)),
        "{0:04b}".format(int(channel_tag_size,10)),
        "{0:04b}".format(int(data_item_fraction_size,10)),
        "{0:06b}".format(int(item_packing_field_size,10)),
        "{0:06b}".format(int(data_item_size,10))), 2))

    repeat_count = FIELDS["--dpf-repeat-count"] if "--dpf-repeat-count" in FIELDS else "0"
    vector_size = FIELDS["--dpf-vector-size"] if "--dpf-vector-size" in FIELDS else "0"

    dpf_hex_2 = "%08x" % (int("%s%s" % (
        "{0:016b}".format(int(repeat_count,10)),
        "{0:016b}".format(int(vector_size,10))
        ), 2))

    dpf_hex = "%s%s" % (dpf_hex_1, dpf_hex_2)
    packetchunk = bytearray.fromhex(dpf_hex)
    #all values being zero is allowed
    #packetchunk = bytearray.fromhex(dpf_hex if dpf_hex != "0000000000000000" else "A000034D00000000")
    difi_packet.extend(packetchunk)


    # Send out the packet
    udp_socket.sendto(difi_packet,(DESTINATION_IP,DESTINATION_PORT))
    if not SILENT: print("DIFI Standard Context Packet sent.")


    # Debug output hex
    if not SILENT and DEBUG:
        a_string = difi_packet.hex()

        #split_strings = []
        n  = 8
        for index in range(0, len(a_string), n):
            print(a_string[index : index + n])
            #split_strings.append(a_string[index : index + n])

        # Debug Hex
        #print(split_strings)


async def _send_loop():
    count=0
    while True:
        send_difi_compliant_standard_context_packet(count)
        count+=1
        if not SILENT and DEBUG: print("sent packet...[%d]" % count)
        if COUNT_TO_SEND is not None:
            if count >= COUNT_TO_SEND:
                break
        await asyncio.sleep(SECONDS_BETWEEN_SENDS)

async def _call_send_loop(apply_timeout: bool=True):
    try:
        if apply_timeout is True:
            await asyncio.wait_for(_send_loop(), timeout=SECONDS_TO_SEND)
        else:
            await _send_loop()
    except asyncio.TimeoutError :
        if not SILENT: print("done.")


######################################
# main script
######################################

def main():
    # pylint: disable=global-statement,global-variable-not-assigned

    #constants in settings section at beginning of file
    global DESTINATION_IP
    global DESTINATION_PORT
    global STREAM_ID
    global SILENT
    global DEBUG
    global SECONDS_TO_SEND
    global COUNT_TO_SEND
    global SECONDS_BETWEEN_SENDS
    global FIELDS

    #command-line args
    try:
        opts, args = getopt.getopt(sys.argv[1:],"",[  # pylint: disable=unused-variable
        "address=","port=","stream-id=",
        "silent=","debug=",
        "seconds-to-send=","count-to-send=",
        "seconds-between-sends=",
        "pkt-type=","clsid=","rsvd=","tsm=","tsi=","tsf=","seqnum=","pkt-size=",
        "oui=",
        "icc=","pcc=",
        "integer-seconds-ts=",
        "fractional-seconds-ts=",
        "cif0=",
        "ref-point=",
        "bandwidth=",
        "if-ref-freq=",
        "rf-ref-freq=",
        "if-band-offset=",
        "ref-level=",
        "gain-att-stage1=","gain-att-stage2=",
        "sample-rate=",
        "ts-adjustment=",
        "ts-calibration=",
        "sei-bit12=","sei-bit13=","sei-bit14=","sei-bit15=","sei-bit16=","sei-bit17=","sei-bit18=","sei-bit19=",
        "dpf-pk-mh=","dpf-real-cmp-type=","dpf-data-item-format=","dpf-rpt-ind=","dpf-event-tag-size=","dpf-channel-tag-size=","dpf-data-item-fraction-size=","dpf-item-packing-field-size=","dpf-data-item-size=","dpf-repeat-count=","dpf-vector-size="
        ])
    except getopt.GetoptError:
        print('usage: dcs.py\
\r\n --address <destination address to send packets to>\
\r\n --port <destination port to send packets to>\
\r\n --stream-id <id of the stream> (32bit int or 8 digit hex starting with 0x, i.e. 1 or 0x00000001, defaults to 0x00000001 if not specified)\
\r\n\r\n   note: sends 1 packet to address/port and exits by default\
\
\r\n\r\n [optional args]\
\r\n\r\n --seconds-to-send <seconds> (sends packets for a duration of the number of seconds specified, if specified \'count-to-send\' will be disabled)\
\r\n --count-to-send <count> (sends number of packets specified, if specified \'seconds-to-send\' will be disabled)\
\
\r\n\r\n --seconds-between-sends <seconds> (time to sleep between each send, partial seconds allowed i.e. .1,.01,etc.)\
\
\r\n\r\n --silent <True/False> (outputs nothing to the console, overrides debug)\
\r\n --debug <True/False> (outputs packet data and additional debugging info to the console at runtime)\
\
\r\n\r\n Packet field values:\
\r\n --pkt-type <0-f hex> (DIFI must be 4)\
\r\n    4=Standard Flow Signal Context Packet\
\r\n    5=Version Flow Signal Context Packet\
\r\n    1=Standard Flow Signal Data Packet\
\r\n --clsid <0-1> (DIFI must be 1)\
\r\n --rsvd <0-1> (DIFI must be 0)\
\r\n --tsm <0-1> (DIFI must be 1)\
\r\n --tsi <1-3>\
\r\n    0=not allowed\
\r\n    1=(UTC) with epoch Jan 1, 1970\
\r\n    2=GPS with epoch Jan 6, 1980\
\r\n    3=POSIX time with epoch Jan 1, 1970\
\r\n --tsf <0-3> (DIFI must be 2)\
\r\n    0=No Fractional-seconds Timestamp field included\
\r\n    1=Sample Count Timestamp\
\r\n    2=Real-Time (Picoseconds) Timestamp\
\r\n    3=Free Running Count Timestamp\
\r\n --seqnum <0-f hex> (value is mod 16 of packet count)\
\r\n --pkt-size <4 digit hex> (DIFI must be 001b (27 words))\
\r\n    Standard Context Packet=001b (27 words)\
\r\n    Version Context Packet=000b (11 words)\
\r\n    Signal Data Packet=???? (7 words + payload size in words)\
\r\n --oui <6 digit hex>\
\r\n --icc <4 digit hex> (DIFI must be 0000)\
\r\n    Standard Context Packet=0000\
\r\n    Version Context Packet=0001\
\r\n    Signal Data Packet=0000\
\r\n --pcc <4 digit hex> (DIFI must be 0000)\
\r\n    Standard Context Packet=0000\
\r\n    Version Context Packet=0004\
\r\n    Signal Data Packet=0000\
\r\n --integer-seconds-ts <0-4294967296 (32bit unsigned int)> (seconds since epoch)\
\r\n --fractional-seconds-ts <0-18446744073709551616 (64bit unsigned int)> (picoseconds past integer-seconds)\
\r\n --cif0 <8 digit hex> (DIFI must be bb98000 (ignores first hex character which is changed indicator))\
\r\n    Standard Context Packet=fbb98000 (change) or 7bb98000 (no change)\
\r\n    Version Context Packet=80000002 (change) or 00000002 (no change)\
\r\n --ref-point <8 digit hex> (location in the system that the digital samples are conveying information about)\
\r\n --bandwidth <float representing Hertz> (can be 0.00 to 8.79 terahertz)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    0.00000095\
\r\n --if-ref-freq <float representing Hertz> (can be -8.79 terahertz to +8.79 terahertz)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n    0.00000095\
\r\n    -0.00000095\
\r\n --rf-ref-freq <float representing Hertz> (can be -8.79 terahertz to +8.79 terahertz)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n    0.00000095\
\r\n    -0.00000095\
\r\n --if-band-offset <float representing Hertz> (can be -8.79 terahertz to +8.79 terahertz)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n    0.00000095\
\r\n    -0.00000095\
\r\n --ref-level <float representing dBm> (can be -256 dBm to +256 dBm)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n    0.0078125\
\r\n    -0.0078125\
\r\n --gain-att-stage1 <float representing dB> (can be -256 dB to +256 dB)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n --gain-att-stage2 <float representing dB> (can be -256 dB to +256 dB)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n --sample-rate <float representing Hertz> (can be 0.00 to 8.79 terahertz)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    0.00000095\
\r\n --ts-adjustment <-9223372036854775808 - +9223372036854775808 (64bit signed int) representing femtoseconds> (negative number (Rx chain) or positive number (Tx Chain))\
\r\n --ts-calibration <0-4294967296 (32bit unsigned int) representing seconds>\
\
\r\n\r\n State and Event Indicators packet field values:\
\r\n --sei-bit19 <1=indicated, 0=not indicated> (Calibrated Time Indicator)\
\r\n --sei-bit18 <1=indicated, 0=not indicated> (Valid Data Indicator)\
\r\n --sei-bit17 <1=indicated, 0=not indicated> (Reference Lock Indicator)\
\r\n --sei-bit16 <1=indicated, 0=not indicated> (AGC/MGC Indicator)\
\r\n --sei-bit15 <1=indicated, 0=not indicated> (Detected Signal Indicator)\
\r\n --sei-bit14 <1=indicated, 0=not indicated> (Spectral Inversion Indicator)\
\r\n --sei-bit13 <1=indicated, 0=not indicated> (Over-range Indicator)\
\r\n --sei-bit12 <1=indicated, 0=not indicated> (Sample Loss Indicator)\
\r\n   note: bit17 and bit19 default to indicated if none are supplied\
\
\r\n\r\n Data Packet Payload Format packet field values:\
\r\n --dpf-pk-mh <0-1> (Packing Method)\
\r\n    0=processing-efficient packing\
\r\n    1=link-efficient packing\
\r\n    note: defaults 1 if arg not supplied\
\r\n --dpf-real-cmp-type <0-2> (Real/Complex Type)\
\r\n    0=Real\
\r\n    1=Complex Cartesian\
\r\n    2=Complex Polar\
\r\n    3=Reserved\
\r\n --dpf-data-item-format <0-23> (Data Item Format)\
\r\n    0=Signed Fixed-Point\
\r\n    1=Signed VRT 1-bit exponent\
\r\n    2=Signed VRT 2-bit exponent\
\r\n    3=Signed VRT 3-bit exponent\
\r\n    4=Signed VRT 4-bit exponent\
\r\n    5=Signed VRT 5-bit exponent\
\r\n    6=Signed VRT 6-bit exponent\
\r\n    7=Signed Fixed-Point Non-Normalized\
\r\n    8-12=Reserved\
\r\n    13=IEEE-754 Half-Precision Floating-Point\
\r\n    14=IEEE-754 Single-Precision Floating-Point\
\r\n    15=IEEE-754 Double-Precision Floating-Point\
\r\n    16=Unsigned Fixed-Point\
\r\n    17=Unsigned VRT 1-bit exponent\
\r\n    18=Unsigned VRT 2-bit exponent\
\r\n    19=Unsigned VRT 3-bit exponent\
\r\n    20=Unsigned VRT 4-bit exponent\
\r\n    21=Unsigned VRT 5-bit exponent\
\r\n    22=Unsigned VRT 6-bit exponent\
\r\n    23=Unsigned Fixed-Point Non-Normalized\
\r\n    24-31=Reserved\
\r\n    note: defaults 16 if arg not supplied\
\r\n --dpf-rpt-ind <0-1> (Sample-Component Repeat Indicator)\
\r\n    0=Sample Component Repeating not in use\
\r\n    1=Sample Component Repeating in use\
\r\n --dpf-event-tag <0-7> (Event-Tag Size)\
\r\n --dpf-channel-tag-size <0-15> (Channel-Tag Size)\
\r\n --dpf-data-item-fraction-size <0-15> (Data Item Fraction Size)\
\r\n --dpf-item-packing-field-size <0-63> (Item Packing Field Size)\
\r\n   note: defaults 13 if arg not supplied\
\r\n --dpf-data-item-size <0-63> (Data Item Size)\
\r\n   note: defaults 13 if arg not supplied\
\r\n --dpf-repeat-count <0-65535> (Repeat Count)\
\r\n --dpf-vector-size <0-65535> (Vector Size)\
    ')
        sys.exit(2)

    # pylint: disable=too-many-nested-blocks
    try:
        for opt, arg in opts:
            FIELDS[opt] = arg
        for opt, arg in opts:
            if opt == "--address":
                if len(arg) > 0:
                    DESTINATION_IP = arg
            elif opt == "--port":
                if len(arg) > 0:
                    DESTINATION_PORT = int(arg)
            elif opt == "--stream-id":
                if len(arg) > 0:
                    try:
                        if arg.lower().startswith("0x"):
                            STREAM_ID = int(arg,16) #base16
                        else:
                            STREAM_ID = int(arg,10) #base10
                    except ValueError:
                        raise dificommon.InvalidArgs()  # pylint: disable=raise-missing-from
            elif opt == "--silent":
                SILENT = (arg == "True")
            elif opt == "--debug":
                DEBUG = (arg == "True" and not SILENT)

            elif opt == "--seconds-to-send":
                if len(arg) > 0:
                    SECONDS_TO_SEND = int(arg)
                    COUNT_TO_SEND = None #either count or seconds, not both
            elif opt == "--count-to-send":
                if len(arg) > 0:
                    COUNT_TO_SEND = int(arg)
                    SECONDS_TO_SEND = None #either count or seconds, not both

            elif opt == "--seconds-between-sends":
                if len(arg) > 0:
                    SECONDS_BETWEEN_SENDS = float(arg)

            elif opt == "--help":
                raise dificommon.InvalidArgs()

        #check for required args
        if DESTINATION_IP is None:
            print("'--address' arg is required.")
            raise dificommon.InvalidArgs()
        if DESTINATION_PORT is None:
            print("'--port' arg is required.")
            raise dificommon.InvalidArgs()

    except dificommon.InvalidArgs:
        print('usage: dcs.py\
\r\n --address <destination address to send packets to>\
\r\n --port <destination port to send packets to>\
\r\n --stream-id <id of the stream> (32bit int or 8 digit hex starting with 0x, i.e. 1 or 0x00000001, defaults to 0x00000001 if not specified)\
\r\n\r\n   note: sends 1 packet to address/port and exits by default\
\
\r\n\r\n [optional args]\
\r\n\r\n --seconds-to-send <seconds> (sends packets for a duration of the number of seconds specified, if specified \'count-to-send\' will be disabled)\
\r\n --count-to-send <count> (sends number of packets specified, if specified \'seconds-to-send\' will be disabled)\
\
\r\n\r\n --seconds-between-sends <seconds> (time to sleep between each send, partial seconds allowed i.e. .1,.01,etc.)\
\
\r\n\r\n --silent <True/False> (outputs nothing to the console, overrides debug)\
\r\n --debug <True/False> (outputs packet data and additional debugging info to the console at runtime)\
\
\r\n\r\n Packet field values:\
\r\n --pkt-type <0-f hex> (DIFI must be 4)\
\r\n    4=Standard Flow Signal Context Packet\
\r\n    5=Version Flow Signal Context Packet\
\r\n    1=Standard Flow Signal Data Packet\
\r\n --clsid <0-1> (DIFI must be 1)\
\r\n --rsvd <0-1> (DIFI must be 0)\
\r\n --tsm <0-1> (DIFI must be 1)\
\r\n --tsi <1-3>\
\r\n    0=not allowed\
\r\n    1=(UTC) with epoch Jan 1, 1970\
\r\n    2=GPS with epoch Jan 6, 1980\
\r\n    3=POSIX time with epoch Jan 1, 1970\
\r\n --tsf <0-3> (DIFI must be 2)\
\r\n    0=No Fractional-seconds Timestamp field included\
\r\n    1=Sample Count Timestamp\
\r\n    2=Real-Time (Picoseconds) Timestamp\
\r\n    3=Free Running Count Timestamp\
\r\n --seqnum <0-f hex> (value is mod 16 of packet count)\
\r\n --pkt-size <4 digit hex> (DIFI must be 001b (27 words))\
\r\n    Standard Context Packet=001b (27 words)\
\r\n    Version Context Packet=000b (11 words)\
\r\n    Signal Data Packet=???? (7 words + payload size in words)\
\r\n --oui <6 digit hex>\
\r\n --icc <4 digit hex> (DIFI must be 0000)\
\r\n    Standard Context Packet=0000\
\r\n    Version Context Packet=0001\
\r\n    Signal Data Packet=0000\
\r\n --pcc <4 digit hex> (DIFI must be 0000)\
\r\n    Standard Context Packet=0000\
\r\n    Version Context Packet=0004\
\r\n    Signal Data Packet=0000\
\r\n --integer-seconds-ts <0-4294967296 (32bit unsigned int)> (seconds since epoch)\
\r\n --fractional-seconds-ts <0-18446744073709551616 (64bit unsigned int)> (picoseconds past integer-seconds)\
\r\n --cif0 <8 digit hex> (DIFI must be bb98000 (ignores first hex character which is changed indicator))\
\r\n    Standard Context Packet=fbb98000 (change) or 7bb98000 (no change)\
\r\n    Version Context Packet=80000002 (change) or 00000002 (no change)\
\r\n --ref-point <8 digit hex> (location in the system that the digital samples are conveying information about)\
\r\n --bandwidth <float representing Hertz> (can be 0.00 to 8.79 terahertz)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    0.00000095\
\r\n --if-ref-freq <float representing Hertz> (can be -8.79 terahertz to +8.79 terahertz)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n    0.00000095\
\r\n    -0.00000095\
\r\n --rf-ref-freq <float representing Hertz> (can be -8.79 terahertz to +8.79 terahertz)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n    0.00000095\
\r\n    -0.00000095\
\r\n --if-band-offset <float representing Hertz> (can be -8.79 terahertz to +8.79 terahertz)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n    0.00000095\
\r\n    -0.00000095\
\r\n --ref-level <float representing dBm> (can be -256 dBm to +256 dBm)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n    0.0078125\
\r\n    -0.0078125\
\r\n --gain-att-stage1 <float representing dB> (can be -256 dB to +256 dB)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n --gain-att-stage2 <float representing dB> (can be -256 dB to +256 dB)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    -1\
\r\n --sample-rate <float representing Hertz> (can be 0.00 to 8.79 terahertz)\
\r\n    Sample values from vita spec:\
\r\n    1\
\r\n    0.00000095\
\r\n --ts-adjustment <-9223372036854775808 - +9223372036854775808 (64bit signed int) representing femtoseconds> (negative number (Rx chain) or positive number (Tx Chain))\
\r\n --ts-calibration <0-4294967296 (32bit unsigned int) representing seconds>\
\
\r\n\r\n State and Event Indicators packet field values:\
\r\n --sei-bit19 <1=indicated, 0=not indicated> (Calibrated Time Indicator)\
\r\n --sei-bit18 <1=indicated, 0=not indicated> (Valid Data Indicator)\
\r\n --sei-bit17 <1=indicated, 0=not indicated> (Reference Lock Indicator)\
\r\n --sei-bit16 <1=indicated, 0=not indicated> (AGC/MGC Indicator)\
\r\n --sei-bit15 <1=indicated, 0=not indicated> (Detected Signal Indicator)\
\r\n --sei-bit14 <1=indicated, 0=not indicated> (Spectral Inversion Indicator)\
\r\n --sei-bit13 <1=indicated, 0=not indicated> (Over-range Indicator)\
\r\n --sei-bit12 <1=indicated, 0=not indicated> (Sample Loss Indicator)\
\r\n   note: bit17 and bit19 default to indicated if none are supplied\
\
\r\n\r\n Data Packet Payload Format packet field values:\
\r\n --dpf-pk-mh <0-1> (Packing Method)\
\r\n    0=processing-efficient packing\
\r\n    1=link-efficient packing\
\r\n    note: defaults 1 if arg not supplied\
\r\n --dpf-real-cmp-type <0-2> (Real/Complex Type)\
\r\n    0=Real\
\r\n    1=Complex Cartesian\
\r\n    2=Complex Polar\
\r\n    3=Reserved\
\r\n --dpf-data-item-format <0-23> (Data Item Format)\
\r\n    0=Signed Fixed-Point\
\r\n    1=Signed VRT 1-bit exponent\
\r\n    2=Signed VRT 2-bit exponent\
\r\n    3=Signed VRT 3-bit exponent\
\r\n    4=Signed VRT 4-bit exponent\
\r\n    5=Signed VRT 5-bit exponent\
\r\n    6=Signed VRT 6-bit exponent\
\r\n    7=Signed Fixed-Point Non-Normalized\
\r\n    8-12=Reserved\
\r\n    13=IEEE-754 Half-Precision Floating-Point\
\r\n    14=IEEE-754 Single-Precision Floating-Point\
\r\n    15=IEEE-754 Double-Precision Floating-Point\
\r\n    16=Unsigned Fixed-Point\
\r\n    17=Unsigned VRT 1-bit exponent\
\r\n    18=Unsigned VRT 2-bit exponent\
\r\n    19=Unsigned VRT 3-bit exponent\
\r\n    20=Unsigned VRT 4-bit exponent\
\r\n    21=Unsigned VRT 5-bit exponent\
\r\n    22=Unsigned VRT 6-bit exponent\
\r\n    23=Unsigned Fixed-Point Non-Normalized\
\r\n    24-31=Reserved\
\r\n    note: defaults 16 if arg not supplied\
\r\n --dpf-rpt-ind <0-1> (Sample-Component Repeat Indicator)\
\r\n    0=Sample Component Repeating not in use\
\r\n    1=Sample Component Repeating in use\
\r\n --dpf-event-tag <0-7> (Event-Tag Size)\
\r\n --dpf-channel-tag-size <0-15> (Channel-Tag Size)\
\r\n --dpf-data-item-fraction-size <0-15> (Data Item Fraction Size)\
\r\n --dpf-item-packing-field-size <0-63> (Item Packing Field Size)\
\r\n   note: defaults 13 if arg not supplied\
\r\n --dpf-data-item-size <0-63> (Data Item Size)\
\r\n   note: defaults 13 if arg not supplied\
\r\n --dpf-repeat-count <0-65535> (Repeat Count)\
\r\n --dpf-vector-size <0-65535> (Vector Size)\
    ')
        sys.exit(2)

    #print(FIELDS)


    if not SILENT: print("DIFI Packet Send Utility")

    if SECONDS_TO_SEND is not None:
        #send packets for specified duration
        asyncio.run(_call_send_loop(apply_timeout=True))
    elif COUNT_TO_SEND is not None:
        #send number of packets specified
        asyncio.run(_call_send_loop(apply_timeout=False))
    else:
        #send 1 packet
        send_difi_compliant_standard_context_packet()


if __name__ == '__main__':
    main()



#thread pool version
#async def _send_loop():
#    count=0
#    while True:
#        send_difi_compliant_standard_context_packet()
#        count+=1
#        if not SILENT and DEBUG: print("sent packet...[%d]" % count)
#        await asyncio.sleep(SECONDS_BETWEEN_SENDS)
#
#async def _call_send():
#    loop = asyncio.get_running_loop()
#    with ThreadPoolExecutor() as pool:
#        func = functools.partial(_send_loop)
#        result = await loop.run_in_executor(pool, func)
#        await asyncio.wait_for(result, timeout=SECONDS_TO_SEND)
#
# def main():
#    try:
#        asyncio.run(_call_send())
#    except asyncio.TimeoutError as e:
#        if not SILENT: print("done.")
#
#
# if __name__ == '__main__':
#     main()
