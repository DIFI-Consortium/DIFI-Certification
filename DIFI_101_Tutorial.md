# DIFI 101 Tutorial

## What is DIFI



The DIFI Packet Protocol, technically referred to as "IEEE-ISTO Std 4900-2021:  Digital IF Interoperability Standard", defines a data plane interface meant for transmitting and receive digitized IF data and corresponding metadata over standard IP networks. The DIFI interface is meant to be fully compliant with the VITA 49.2 standard, VITA 49 is a very flexible standard, and DIFI is a specific VITA 49 schema.  The primary use-case of DIFI packets is to create an interface between satellite ground station digitizers (transceivers) and software modems, enabling interoperability and combatting vendor lock-in that has plagued the satellite industry for decades.  The DIFI packet protocol can also be used for other purposes, including applications that don't involve hardware, such as streaming an RF signal between different software applications.

![](images/difi-consortium-logo.png)

## Overview of the DIFI Specifications

There are three types of DIFI packets: signal data, signal context, and version context. 

The signal context packet includes fields such as timestamp, bandwidth, RF frequency, gain, sample rate, and the data format used within the signal data packets.  The version context packet is even shorter and is used to convey version information for the software/firmware sending the DIFI packets, as well as the DIFI spec version being used (currently there is just one option). Lastly, the signal data packets contain the actual signal, in the form of IQ samples, as well as a timestamp that includes both integer and fractional seconds, to mark the precise time of the first sample.  

Regarding the specific data type used for the IQ samples, DIFI uses fixed point signed integers, where each integer can be 4 through 16 bits (specified in the signal context packet).  DIFI does not use zero padding, so for bit depths other than 8 and 16, the integers essentially share bytes, and the samples per packet must lead to an integer number of 4-byte words.  

All DIFI packets also have a 4-bit sequence number that can be used to deal with out of order packets at the destination.  They also all have a stream ID which defaults to 0 but can be set to something else in order to have multiple independent streams over the same port.

The DIFI packet protocol defines the payload of UDP packets, although some vendors have implemented TCP versions as well, even though it's not actually part of the specifications.  Like any TCP/UDP packets, the max packet size (the Ethernet frame payload) is adjustable from 128 octets to 9000 octets, including overhead.

## Creating DIFI Packets in Python

We will now create an example DIFI signal data packet in Python, without needing any dependencies other than numpy and matplotlib.

For reference, and because the DIFI specifications are behind a pay-wall, the signal data packet structure is depicted below, using 4 bytes per line:

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Pckt T.|C|Indi.| T.|TSF|Seq Num|          Packet Size          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Stream ID                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Pad  |  Res|                      OUI                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Info Class          |          Packet Class         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Integer Sec Timestamp                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  Fractional-Seconds Timestamp                 |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                                                               |
|                                                               |
|       Signal Data Payload Complex 4-16 bit signed N Words     |
|                                                               |
|                                                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

The following code creates a valid DIFI signal data packet, filled with 1's and 0's for the IQ samples.  In the later portion of this tutorial we will create code that can parse this packet, but first we will dissect it in Wireshark.

``` python
import socket
import time

DESTINATION_IP = '127.0.0.1'  # dest address to send packets to
DESTINATION_PORT = 1234  # dest port to send packets to
STREAM_ID = 0  # 32 bit int id of stream

# 1st 16 bits of header in hex
pkt_type = "1"

clsid = "1" # 1 bit
rsvd = "00" # 2 bits
tsm = "0" # 1 bit
tsi = "01" # 2 bits
tsf = "10" # 2 bits
clsid_rsvd_tsm_tsi_tsf_binary = clsid + rsvd + tsm + tsi + tsf # 10000110
clsid_rsvd_tsm_tsi_tsf_dec = int(clsid_rsvd_tsm_tsi_tsf_binary, 2) # decimal version
clsid_rsvd_tsm_tsi_tsf = "%02x" % clsid_rsvd_tsm_tsi_tsf_dec # hex version

seqnum = 0

# create the socket
udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

difi_packet = bytearray() # prep vita/difi payload

first_half_header = "%s%s%s" % (pkt_type, clsid_rsvd_tsm_tsi_tsf, seqnum)
packetchunk = bytearray.fromhex(first_half_header) #(1A61) #clsid=0x1,tsm=0x0,tsf=0x2
difi_packet.extend(packetchunk)

# 2nd 16 bits of header in hex, (Packet Size)
difi_packet.extend(bytearray.fromhex("00C9")) # C9 is 201 which tells us how many words are in the packet

difi_packet.extend(STREAM_ID.to_bytes(4, 'big'))
          
difi_packet.extend(bytearray.fromhex("000012A2")) # XX:000012A2  XX:OUI for Vita
             
difi_packet.extend(bytearray.fromhex("00000000")) # Info Class Code, Packet Class Code #icc=0x0000,pcc=0x0000

packet_timestamp = format(int(time.time()),'x') # Integer timestamp
difi_packet.extend(bytearray.fromhex(packet_timestamp))

difi_packet.extend(bytearray.fromhex("0000000000000001")) # Fractional Timestamp

for _ in range(0,201-7): # header is 7 words
    difi_packet.extend(bytearray(b'\xFF\xFF')) # 16 bits of ones
    difi_packet.extend(bytearray(b'\x00\x00')) # 16 bits of zeros

length = len(difi_packet)
print(f'Length of this bytes object is {length} bytes and {length/4} 32 bit words')

udp_socket.sendto(difi_packet, (DESTINATION_IP, DESTINATION_PORT))
```

## Dissecting a DIFI Packet in Wireshark


## Parsing DIFI Packets in Python

