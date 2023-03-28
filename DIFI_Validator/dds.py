"""
# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT
#
# DIFI Data Packet Sender, DDS
#
# Sends DIFI 'Signal Data Packet' (packet type = 0x1) to IP and port specified.
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
# 2) can run in 'debug' mode (prints additional info to console for troubleshooting problems)
#    note: prints packet sent message to console by default
#
# Can also import into other projects:
# [Example]
# import dds
# import sys
# try:
#     dds.DESTINATION_IP = "10.1.1.1"
#     dds.DESTINATION_PORT = 4991
#     dds.STREAM_ID = 4
#     dds.FIELDS["--pcc"] = "1111"
#     dds.send_difi_compliant_data_packet()
# except Exception as e:
#     print(e)
# sys.exit(2)
"""

import sys
import socket
import time
import getopt
import asyncio

class InvalidArgs(Exception):
    pass

#   3                   2                   1                   0
# 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |Pckt T.|C|Indi.| T.|TSF|Seq Num|          Packet Size          |
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
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# +                                                               +
# |                                                               |
# +       Signal Data Payload Complex 4-16 bit signed N Words     +
# |                                                               |
# +                                                               +
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

# DIFI Data Packet Sender
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
DEBUG = False  #prints additional debugging info to the console

#send mode (must be either seconds or count, specifying both is not supported)
SECONDS_TO_SEND = None  #default is None, meaning only 1 packet will be sent
COUNT_TO_SEND = None  #default is None, meaning only 1 packet will be sent

SECONDS_BETWEEN_SENDS = 1  #default is 1 second if arg not supplied

#args supplying field values
FIELDS={}

# Sample packet
def sample_data(difi_packet: bytearray()):
    for _ in range(1, 2):
        difi_packet.extend(bytearray.fromhex('1de8fcd507ec1130192135f62d1009360a3b0f3605370439fd36e52ed914f0e203c015d029e61814002f06ee04c41deb3103f900c30dd81de6270a0737f90917df2b0b262b1e0bfbf8d006f807360209'))
        difi_packet.extend(bytearray.fromhex('fecae6d3dae4eef4072df439dc22db10f6d9f6dbde21f52c231a161ee0f2d9d1f8d001c3fabf06ca1dcc30e12e07241e0df0ffcf03130241ee2bd31fcb06dfd809e336fb2fe51fda0e05e42601123bfd'))
        difi_packet.extend(bytearray.fromhex('2219ff37093c0433ec1cd9e5d5d5dae0f4e51f1524340130ee27dff0ddc7f6d0fbc8e2d1e1ebff180a3a1e24291a1ffa22d012d504cd2be03d0239fa3aff3b0537fc1ee6fdcde6e4ca02cee7e1d4fcdf'))
        difi_packet.extend(bytearray.fromhex('33fe390f211e0817e3e3f2ec2323190900cc00c803d1fbdde413d22cda1fce20c509d205ef2b0b3719251f1c08ee02d20619fc3102e802c4fbcd0cc920ca26daffdbd9d5dfdae6dbecfefe39ec35d421'))
        difi_packet.extend(bytearray.fromhex('d02ad225d122d225d324d823f7142f0037f626e237e63c013c043a03200ae207c3fccf00cb01cd13da13f2dc06bfffccfbcfe4e9d1f50cde27dbf3dde1da1103262426f92bd82ce52ae020d10bd01af2'))
        difi_packet.extend(bytearray.fromhex('292827092ddf1b07fb3aef33da1fca09dede00d92b001ffce8d8f7df34002cf40aca06c609d0ffd9e30be21f22022c00efead9dfde10dd26051c1b27edfcd6d2d5efd0f7ffde2de7fd06d21cf2f609c5'))
        difi_packet.extend(bytearray.fromhex('ebccdddcf3fcfe32112232fe10fee4dc07df34091407d6f6e8fc2f051c07d0f8c5fbd0ffdefd0d1b102cd405cfe7f9da02cfd4eac5fbd2f6d1fde51e04321e17300af721cc21eb30f33add2ad41ef727'))
        difi_packet.extend(bytearray.fromhex('212a230626e50f07d921ff0e37060ef5e1d406d32ee610e6d4f1e6ef2fe538e830ff31ff15d414d8201d0e23f1e4e8c805d310dafe0fe838da05d5f3011d22311a29162311f50bc40dcd0ed708fdf138'))
        difi_packet.extend(bytearray.fromhex('dc15d2eaf3ea31e221d208c715cb10cbfec8e9cde1cfe9cee5cde9ccffd228dc2bdf11c81dd73501380331e819ece0f8dceb21e43ced2ffd3a0d36f42ede1ddb07d4eb01cd1fd013d219db29f035ed37'))
        difi_packet.extend(bytearray.fromhex('ee34ef3be834db1bc7f4cb01cd19d3f4e4cbe6cce8d10edd3109171bd712e80929f216f2d114dc0410d70de1f3230232'))
    difi_packet.extend(bytearray.fromhex('3a091b24f934e50c'))
    return difi_packet

###########
# primary function
###########
def send_difi_compliant_data_packet(count: int = 0):

    #from netifaces import interfaces, ifaddresses, AF_INET
    #for ifaceName in interfaces():
    #    addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
    #    if not SILENT and DEBUG: print(' '.join(addresses))

    # create the socket
    udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    # prep  vita/difi payload
    difi_packet = bytearray()

    # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    # |Pckt T.|C|Indi.| T.|TSF|Seq Num|          Packet Size          |
    # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


    # 1st 16 bits of header in hex.  #1A61
    pkt_type = FIELDS["--pkt-type"] if "--pkt-type" in FIELDS else "1" #hex
    clsid = FIELDS["--clsid"] if "--clsid" in FIELDS else "1" #hex
    rsvd = FIELDS["--rsvd"] if "--rsvd" in FIELDS else "0" #hex
    tsm = FIELDS["--tsm"] if "--tsm" in FIELDS else "0" #hex
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
    packetchunk = bytearray.fromhex(first_half_header) #(1A61) #clsid=0x1,tsm=0x0,tsf=0x2
    difi_packet.extend(packetchunk)

    # 2nd 16 bits of header in hex, (Packet Size)
    packetchunk = bytearray.fromhex("00C9")
    #packetchunk = bytearray.fromhex("08C2")
    #packetchunk = bytearray.fromhex("016D")
    difi_packet.extend(packetchunk)

    # Context Header, size 27
    # Example "1A:61:22:94" in Binary
    #                  0001 1010 0110 0001 0010 0010 1001 0011

    # Extend each section of new packet into the 'difi_packet'

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

    # ------------------------------------
    # Auto Fill with 1's and zeros
    ####arr = bytearray(b'\x01')  * 8 * 10 ** 3
    #####arrlen = len(arr)
    #print (f"Length of empty byte array = {arrlen}")
    data_zeros=bytearray(b'\xFF\xFF')  # 16 bits of ones
    data_ones=bytearray(b'\x00\x00')  # 16 bits of zeros
    difi_packet_test = bytearray()
    for _ in range(0,2000):
        #packetchunkTest = bytearray.fromhex(data_zeros)
        difi_packet_test.extend(data_zeros)
        #packetchunkTest = bytearray.fromhex(data_ones)
        difi_packet_test.extend(data_ones)

    ####arrlentest = len(difi_packet_test)
    #print (f"Length of test byte array = {arrlentest}")

    difi_packet = sample_data(difi_packet)

    length = len(difi_packet)
    if not SILENT and DEBUG: print(f'Length of this bytes object is {length}')
    if not SILENT and DEBUG: print(f'DIFI packet length = {length}')

    for _ in range(1):
        # Send out the packet
        udp_socket.sendto(difi_packet,(DESTINATION_IP,DESTINATION_PORT))
        time.sleep(0.00000001)
        if not SILENT: print("DIFI Data Packet sent.")


async def _send_loop():
    count=0
    while True:
        send_difi_compliant_data_packet(count)
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
    except asyncio.TimeoutError:
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
        "fractional-seconds-ts="
        ])
    except getopt.GetoptError:
        print('usage: dds.py\
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
\r\n --pkt-type <0-f hex> (DIFI must be 1)\
\r\n    4=Standard Flow Signal Context Packet\
\r\n    5=Version Flow Signal Context Packet\
\r\n    1=Standard Flow Signal Data Packet\
\r\n --clsid <0-1> (DIFI must be 1)\
\r\n --rsvd <0-1> (DIFI must be 0)\
\r\n --tsm <0-1> (DIFI must be 0)\
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
\r\n --pkt-size <4 digit hex> (7 words + payload size in words)\
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
                        raise InvalidArgs()
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
                raise InvalidArgs()

        #check for required args
        if DESTINATION_IP is None:
            print("'--address' arg is required.")
            raise InvalidArgs()
        if DESTINATION_PORT is None:
            print("'--port' arg is required.")
            raise InvalidArgs()

    except InvalidArgs:
        print('usage: dds.py\
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
\r\n --pkt-type <0-f hex> (DIFI must be 1)\
\r\n    4=Standard Flow Signal Context Packet\
\r\n    5=Version Flow Signal Context Packet\
\r\n    1=Standard Flow Signal Data Packet\
\r\n --clsid <0-1> (DIFI must be 1)\
\r\n --rsvd <0-1> (DIFI must be 0)\
\r\n --tsm <0-1> (DIFI must be 0)\
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
\r\n --pkt-size <4 digit hex> (7 words + payload size in words)\
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
        send_difi_compliant_data_packet()


if __name__ == '__main__':
    main()



#thread pool version
#async def _send_loop():
#    count=0
#    while True:
#        send_difi_compliant_data_packet()
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
