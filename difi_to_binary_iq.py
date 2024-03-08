# Install on Ubuntu/Debian with:
#   sudo apt-get install libpcap-dev
#   pip3 install python-libpcap

# Notes:
#   Assumes UDP DIFI packets, e.g. from Kratos Digitizers
#   Even though the context packets (not parsed here) contain the sample rate and center freq, we'll assume it's already known, use wireshark if you need to find it
#   If you want to visualize the .cs8 file, which is binary IQ, install Inspectrum using https://github.com/miek/inspectrum/wiki/Build#building-on-debian-based-distros

from pylibpcap.pcap import rpcap # MUCH faster than scapy/dpkt

filename = "/path/to/your.pcap"
with open(filename + '.cs8', "wb") as out_file:
    for _, _, buf in rpcap(filename):
        payload = buf[42:] # Ethernet II header is 14 bytes, IP header is 20 bytes, UDP header is 8 bytes, rest is payload (DIFI)
        if payload[0:1].hex() == '18': # first byte must be 00011000 or 0x18 for data packets
            out_file.write(payload[28:]) # 7 words (each 4 bytes) of DIFI header, rest is IQ, we'll leave it in binary format
