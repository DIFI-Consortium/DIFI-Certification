# DIFI 101 Tutorial

## What is DIFI

The DIFI Packet Protocol, technically referred to as "IEEE-ISTO Std 4900-2021:  Digital IF Interoperability Standard", defines a data plane interface meant for transmitting and receive digitized IF data and corresponding metadata over standard IP networks. The DIFI interface is meant to be fully compliant with the VITA 49.2 standard, VITA 49 is a very flexible standard, and DIFI is a specific VITA 49 schema.  The primary use-case of DIFI packets is to create an interface between satellite ground station digitizers (transceivers) and software modems, enabling interoperability and combatting vendor lock-in that has plagued the satellite industry for decades.  The DIFI packet protocol can also be used for other purposes, including applications that don't involve hardware, such as streaming an RF signal between different software applications.

## Overview of the DIFI Specifications

There are three types of DIFI packets: signal data, signal context, and version context. 

The signal context packet includes fields such as timestamp, bandwidth, RF frequency, gain, sample rate, and the data format used within the signal data packets.  The version context packet is even shorter and is used to convey version information for the software/firmware sending the DIFI packets, as well as the DIFI spec version being used (currently there is just one option). Lastly, the signal data packets contain the actual signal, in the form of IQ samples, as well as a timestamp that includes both integer and fractional seconds, to mark the precise time of the first sample.  

Regarding the specific data type used for the IQ samples, DIFI uses fixed point signed integers, where each integer can be 4 through 16 bits (specified in the signal context packet).  DIFI does not use zero padding, so for bit depths other than 8 and 16, the integers essentially share bytes, and the samples per packet must lead to an integer number of 4-byte words.  

All DIFI packets also have a 4-bit sequence number that can be used to deal with out of order packets at the destination.  They also all have a stream ID which defaults to 0 but can be set to something else in order to have multiple independent streams over the same port.

The DIFI packet protocol defines the payload of UDP packets, although some vendors have implemented TCP versions as well, even though it's not actually part of the specifications.  Like any TCP/UDP packets, the max packet size (the Ethernet frame payload) is adjustable from 128 octets to 9000 octets, including overhead.


## Creating DIFI Packets in Python


## Dissecting a DIFI Packet in Wireshark


## Parsing DIFI Packets in Python