"""
This script is a copy of dds.py but was minimized to be suitable for tutorial purpose
"""

import socket
import time
import numpy as np
import matplotlib.pyplot as plt

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

# Packet Size - 2nd 16 bits of header in hex
difi_packet.extend(bytearray.fromhex("00C9")) # C9 is 201 which tells us how many words are in the packet

difi_packet.extend(STREAM_ID.to_bytes(4, 'big'))
          
difi_packet.extend(bytearray.fromhex("007C386C")) # might also be 0x6A621E
             
difi_packet.extend(bytearray.fromhex("00000000")) # Info Class Code, Packet Class Code #icc=0x0000,pcc=0x0000

packet_timestamp = format(int(time.time()),'x') # Integer timestamp
difi_packet.extend(bytearray.fromhex(packet_timestamp))

difi_packet.extend(bytearray.fromhex("0000000000000001")) # Fractional Timestamp

'''
for _ in range(0,201-7): # header is 7 words
    difi_packet.extend(bytearray(b'\xFF\xFF')) # 16 bits of ones
    difi_packet.extend(bytearray(b'\x00\x00')) # 16 bits of zeros
'''

# Simulate a signal instead of 1's and 0's
N = 200 # number of IQ samples, which will equate to 4x as many bytes
f = 0.01
t = np.arange(N)
signal = 1000*np.exp(1j*2*np.pi*t*f)
if False:
    plt.plot(signal.real, '.-')
    plt.plot(signal.imag, '.-')
    plt.legend(['I','Q'])
    plt.show()
# Deinterleave the IQ so it's a bunch of ints in a row (IQIQIQIQ...)
deinterleaved_signal = np.zeros(len(signal)*2, dtype=np.int16)
deinterleaved_signal[::2] = signal.real
deinterleaved_signal[1::2] = signal.imag
signal_bytearray = bytearray(deinterleaved_signal)
difi_packet.extend(signal_bytearray) # add it to the packet
# Note that at this point, the Packet Size defined before should be updated, it's currently hardcoded

length = len(difi_packet)
print(f'Length of this bytes object is {length} bytes and {length/4} 32 bit words')

udp_socket.sendto(difi_packet, (DESTINATION_IP, DESTINATION_PORT))

