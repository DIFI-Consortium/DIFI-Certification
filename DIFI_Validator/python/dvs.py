"""
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT
#
# DIFI Version Context Packet Sender, DVS
#
#
# Sends DIFI 'Version Flow Signal Context Packet' (packet type = 0x5) to IP and port specified.
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
# import dvs
# import sys
# try:
#     dvs.DESTINATION_IP = "10.1.1.1"
#     dvs.DESTINATION_PORT = 4991
#     dvs.STREAM_ID = 4
#     dvs.FIELDS["--year"] = "30"
#     dvs.send_difi_compliant_version_context_packet()
# except Exception as e:
#     print(e)
# sys.exit(2)
"""

import sys
import socket
import time
from datetime import datetime
import getopt
import asyncio

import dificommon

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
# |                       Context Indicators                      |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                        V49 Spec Version                       |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |     Year    |        Day      |     Rev   | Type | ICD Version|
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


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


def bitstring_to_bytes(s, handle_empty=False):
    v = int(s, 2)
    b = bytearray()
    if handle_empty is True and v == 0:
        if len(s) >= 8:
            return (0).to_bytes(int(len(s)/8), byteorder='big')
    else:
        while v:
            b.append(v & 0xff)
            v >>= 8
    return bytes(b[::-1])

###########
# primary function
###########
def send_difi_compliant_version_context_packet(count: int = 0):

    # create the socket
    udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    # prep  vita/difi payload
    difi_packet = bytearray()

    #  3                   2                   1                   0
    #  1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
    # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    # |Pckt T.|C|Indi.| T.|TSF|Seq Num|          Packet Size          |
    # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    #+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    #| 0   1   0   1 | 1 | 0  0/1? 1 |  TSI  | 1   0 |    SeqNum     |                            Packet Size (11 words)             |
    #+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    # 5961 DEC = = 0101 1001 0110 0001 Binary
    # 5D61 DEC = = 0101 1101 0110 0001 Binary
    # 5B61 DEC = = 0101 1011 0110 0001 Binary

    # 1st 16 bits of header in hex.  #5B61
    pkt_type = FIELDS["--pkt-type"] if "--pkt-type" in FIELDS else "5" #hex
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
    packetchunk = bytearray.fromhex(first_half_header) #(5B61) #clsid=0x1,tsm=0x1,tsf=0x2
    difi_packet.extend(packetchunk)

    # 2nd 16 bits of header in hex, (Packet Size) 000B = 11
    packetchunk = bytearray.fromhex("{0:04x}".format(int(FIELDS["--pkt-size"],16)) if "--pkt-size" in FIELDS else "000B")
    difi_packet.extend(packetchunk)

    # Context Header, size 11
    # Example "5B:61:00:0B" in Binary
    #                  0101 1011 0110 0001 0000 0000 0000 1011

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

    packetchunk = bytearray.fromhex("%s%s" % ("{0:04x}".format(int(FIELDS["--icc"],16)) if "--icc" in FIELDS else "0001", "{0:04x}".format(int(FIELDS["--pcc"],16)) if "--pcc" in FIELDS else "0004"))                 # Info Class Code, Packet Class Code #icc=0x0001,pcc=0x0004
    difi_packet.extend(packetchunk)

    packet_timestamp = format(int(time.time()),'x')            # Timestamp
    difi_packet.extend(bytearray.fromhex("{0:08x}".format(int(FIELDS["--integer-seconds-ts"])) if "--integer-seconds-ts" in FIELDS else packet_timestamp))
    #difi_packet.extend(packetchunk)

    packetchunk = bytearray.fromhex("{0:016x}".format(int(FIELDS["--fractional-seconds-ts"])) if "--fractional-seconds-ts" in FIELDS else "0000000000000001")         # Fractional Timestamp
    difi_packet.extend(packetchunk)

    packetchunk = bytearray.fromhex("{0:08x}".format(int(FIELDS["--cif0"],16)) if "--cif0" in FIELDS else "80000002")                 # Context indicator field (context change) #cif0=0x0000002
        # OR
        # packetchunk = bytearray.fromhex("00000002")                 # Context indicator field (No change) #cif0=0x0000002
    difi_packet.extend(packetchunk)

    packetchunk = bytearray.fromhex("{0:08x}".format(int(FIELDS["--cif1"],16)) if "--cif1" in FIELDS else "0000000C")                 # Context indicator field 1 #cif1=0x0000000C
    difi_packet.extend(packetchunk)

    packetchunk = bytearray.fromhex("{0:08x}".format(int(FIELDS["--v49-spec-version"],16)) if "--v49-spec-version" in FIELDS else "00000004")                 # VITA49 Spec Version #v49-spec=0x00000004
    difi_packet.extend(packetchunk)

    # Bit                   Field           Sub-field       Name Meaning
    # 31-25 Year Year the software/firmware was compiled.   The value increments linearly starting from the year 2000. The range is 2000 to 2127.
    # 24-16 Day Is the day within the year? A value of 1 is Jan 1. The numbers increment linearly to 366. The values of 0 and greater than 366 are not valid.
    # 15-10 Revision The revision number can be used to account for which version created on the  same year and day is being used. It is a six-bit field and thus allows for 64 different versions to be made on a single day.
    # 9-0 User Defined
    # User defined information associated with the build. It can be used as a means
    # to convey different options included in the build.
    #     DIFI spec:
    #     9-6 Type
    #     5-0 ICD Version

    today = datetime.now()

    ver_footer_year = "{0:07b}".format(int(FIELDS["--year"],10)) if "--year" in FIELDS else "{0:07b}".format(int(today.strftime("%y")))  # 7 of 32 bits
    #ver_footer_year = "0010110"  # 7 of 32 bits, 2022
    if not SILENT and DEBUG: print(f" year = {int(today.strftime('%y')) + 2000}")
    if not SILENT and DEBUG: print(f" ver footer year = {ver_footer_year}")
    # The range for the year is 2000 to 2127.
    packetchunk = bitstring_to_bytes(ver_footer_year)
    if not SILENT and DEBUG: print (' packetchunk start')
    if not SILENT and DEBUG: print (' ', packetchunk)
    if not SILENT and DEBUG: print (' packetchunk end')

    day_of_year = (today - datetime(today.year, 1, 1)).days + 1
    #The values of 0 and greater than 366 are not valid.
    if day_of_year == 0:
        day_of_year = 1
    if day_of_year >= 366:
        day_of_year = 365
    if not SILENT and DEBUG: print(f" day of year = {day_of_year}")

    ver_footer_day = "{0:09b}".format(int(FIELDS["--day"],10)) if "--day" in FIELDS else "{0:09b}".format(day_of_year)  # 9 of 32 bits
    # 1 0101 0101
    if not SILENT and DEBUG: print(f" ver footer day = {ver_footer_day}")
    #ver_footer_day = "010101010"

    ver_footer_rev = "{0:06b}".format(int(FIELDS["--revision"],10)) if "--revision" in FIELDS else "000001"     # 6 of 32 bits
    #ver_footer_UD = "1010101010"  # 10 of 32 bits  # day 347
    ver_footer_type = "{0:04b}".format(int(FIELDS["--type"],10)) if "--type" in FIELDS else "0001"  # 4 of 32 bits
    ver_footer_icd_version = "{0:06b}".format(int(FIELDS["--icd-version"],10)) if "--icd-version" in FIELDS else "000000"  # 6 of 32 bits
    bitstring = ver_footer_year + ver_footer_day + ver_footer_rev + ver_footer_type + ver_footer_icd_version

    packetchunk = bitstring_to_bytes(bitstring, handle_empty=True)
    if not SILENT and DEBUG: print (' bitstring start')
    if not SILENT and DEBUG: print (' ', bitstring)
    if not SILENT and DEBUG: print (' bitstring end')
    difi_packet.extend(packetchunk)

    # Send out the packet
    udp_socket.sendto(difi_packet,(DESTINATION_IP,DESTINATION_PORT))
    if not SILENT: print("DIFI Version Context Packet sent.")

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
        send_difi_compliant_version_context_packet(count)
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
        "fractional-seconds-ts=",
        "cif0=",
        "cif1=",
        "v49-spec-version=",
        "year=","day=","revision=","type=","icd-version="
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
\r\n --pkt-type <0-f hex> (DIFI must be 5)\
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
\r\n --pkt-size <4 digit hex> (DIFI must be 000b (11 words))\
\r\n    Standard Context Packet=001b (27 words)\
\r\n    Version Context Packet=000b (11 words)\
\r\n    Signal Data Packet=???? (7 words + payload size in words)\
\r\n --oui <6 digit hex>\
\r\n --icc <4 digit hex> (DIFI must be 0001)\
\r\n    Standard Context Packet=0000\
\r\n    Version Context Packet=0001\
\r\n    Signal Data Packet=0000\
\r\n --pcc <4 digit hex> (DIFI must be 0004)\
\r\n    Standard Context Packet=0000\
\r\n    Version Context Packet=0004\
\r\n    Signal Data Packet=0000\
\r\n --integer-seconds-ts <0-4294967296 (32bit unsigned int)> (seconds since epoch)\
\r\n --fractional-seconds-ts <0-18446744073709551616 (64bit unsigned int)> (picoseconds past integer-seconds)\
\r\n --cif0 <8 digit hex> (DIFI must be 0000002 (ignores first hex character which is changed indicator))\
\r\n    Standard Context Packet=fbb98000 (change) or 7bb98000 (no change)\
\r\n    Version Context Packet=80000002 (change) or 00000002 (no change)\
\r\n --cif1 <8 digit hex> (DIFI must be 0000000C)\
\r\n --v49-spec-version <8 digit hex> (DIFI must be 00000004)\
\r\n --year <0-127> (code automatically adds +2000 to year arg value)\
\r\n --day <1-366> (day of the year)\
\r\n --revision <0-63>\
\r\n --type <0-1> (type of device)\
\r\n    0=Narrowband\
\r\n    1=Wideband\
\r\n    remaining=reserved\
\r\n --icd-version <0> (version of the data plane standard)\
\r\n    0=Version 1\
\r\n    remaining=reserved\
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
\r\n --pkt-type <0-f hex> (DIFI must be 5)\
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
\r\n --pkt-size <4 digit hex> (DIFI must be 000b (11 words))\
\r\n    Standard Context Packet=001b (27 words)\
\r\n    Version Context Packet=000b (11 words)\
\r\n    Signal Data Packet=???? (7 words + payload size in words)\
\r\n --oui <6 digit hex>\
\r\n --icc <4 digit hex> (DIFI must be 0001)\
\r\n    Standard Context Packet=0000\
\r\n    Version Context Packet=0001\
\r\n    Signal Data Packet=0000\
\r\n --pcc <4 digit hex> (DIFI must be 0004)\
\r\n    Standard Context Packet=0000\
\r\n    Version Context Packet=0004\
\r\n    Signal Data Packet=0000\
\r\n --integer-seconds-ts <0-4294967296 (32bit unsigned int)> (seconds since epoch)\
\r\n --fractional-seconds-ts <0-18446744073709551616 (64bit unsigned int)> (picoseconds past integer-seconds)\
\r\n --cif0 <8 digit hex> (DIFI must be 0000002 (ignores first hex character which is changed indicator))\
\r\n    Standard Context Packet=fbb98000 (change) or 7bb98000 (no change)\
\r\n    Version Context Packet=80000002 (change) or 00000002 (no change)\
\r\n --cif1 <8 digit hex> (DIFI must be 0000000C)\
\r\n --v49-spec-version <8 digit hex> (DIFI must be 00000004)\
\r\n --year <0-127> (code automatically adds +2000 to year arg value)\
\r\n --day <1-366> (day of the year)\
\r\n --revision <0-63>\
\r\n --type <0-1> (type of device)\
\r\n    0=Narrowband\
\r\n    1=Wideband\
\r\n    remaining=reserved\
\r\n --icd-version <0> (version of the data plane standard)\
\r\n    0=Version 1\
\r\n    remaining=reserved\
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
        send_difi_compliant_version_context_packet()


if __name__ == '__main__':
    main()



#thread pool version
# async def _send_loop():
#     count=0
#     while True:
#         send_difi_compliant_version_context_packet()
#         count+=1
#         if not SILENT and DEBUG: print("sent packet...[%d]" % count)
#         await asyncio.sleep(SECONDS_BETWEEN_SENDS)
#
# async def _call_send():
#     loop = asyncio.get_running_loop()
#     with ThreadPoolExecutor() as pool:
#         func = functools.partial(_send_loop)
#         result = await loop.run_in_executor(pool, func)
#         await asyncio.wait_for(result, timeout=SECONDS_TO_SEND)
#
# def main():
#     try:
#         asyncio.run(_call_send())
#     except asyncio.TimeoutError as e:
#         if not SILENT: print("done.")
#
#
# if __name__ == '__main__':
#     main()
