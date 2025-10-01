from scapy.all import PcapReader, UDP
from difi_context_v1_1 import difi_context_definition

# Example of parsing a packet
pcap_file = "../examples/Example1_1Msps_8bits.pcapng"
for packet in PcapReader(pcap_file):
    data = bytes(packet[UDP].payload)
    packet_type = data[0:4][0] >> 4
    if packet_type == 0x4:
        print("Found first context packet")
        break
# print(data)
if len(data) != difi_context_definition.sizeof(): raise Exception(f"Packet size {len(data)} does not match expected size {difi_context_definition.sizeof()}")
parsed = difi_context_definition.parse(data)
for key, value in parsed.items():
    print(f"{key}: {value}")

print("Validating packet...")
difi_context_definition.validate(parsed)
print("All validations passed") # any failed validations will raise an exception

