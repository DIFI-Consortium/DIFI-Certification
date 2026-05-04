# Parse pcap and counts Information Class Code and Packet Class Code

import argparse
from collections import Counter
from scapy.all import PcapReader, UDP

parser = argparse.ArgumentParser(description="Count DIFI Information / Packet Class codes in a pcap")
parser.add_argument("--pcap", required=True, help="Path to pcap file")
args = parser.parse_args()

info_class_counts = Counter()
pkt_class_counts = Counter()
pkt_type_counts = Counter()
total_difi = 0
total_skipped = 0

for packet in PcapReader(args.pcap):
    if UDP not in packet:
        total_skipped += 1
        continue
    data = bytes(packet[UDP].payload)
    if len(data) < 28:
        total_skipped += 1
        continue
    # bits 31-16 = Information Class Code, bits 15-0  = Packet Class Code
    pkt_type = data[0] >> 4
    info_class = int.from_bytes(data[12:14], "big")
    pkt_class = int.from_bytes(data[14:16], "big")
    pkt_type_counts[pkt_type] += 1
    info_class_counts[info_class] += 1
    pkt_class_counts[pkt_class] += 1
    total_difi += 1

print(f"DIFI packets parsed: {total_difi}")

print("Packet Type counts (Word 1 bits 31-28):")
for code, count in sorted(pkt_type_counts.items()):
    print(f"  0x{code:X}: {count}")

print("Information Class Code counts (Word 4 bits 31-16):")
for code, count in sorted(info_class_counts.items()):
    print(f"  0x{code:04X}: {count}")

print("Packet Class Code counts (Word 4 bits 15-0):")
for code, count in sorted(pkt_class_counts.items()):
    print(f"  0x{code:04X}: {count}")
