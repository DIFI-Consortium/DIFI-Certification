
import argparse
import socket
from time import time, strftime
from scapy.all import PcapReader, UDP
from difi_context_v1_1 import difi_context_definition
from difi_data_v1_1 import difi_data_definition
from difi_version_v1_1 import difi_version_definition
import numpy as np

# Class to hold packet statistics and state
class PacketStats:
    def __init__(self):
        self.bit_depth = 8  # default, may be updated by context packet
        self.sample_rate = 1
        self.compliant_context_count = 0
        self.noncompliant_context_count = 0
        self.compliant_data_count = 0
        self.noncompliant_data_count = 0
        self.compliant_version_count = 0
        self.noncompliant_version_count = 0
        self.context_sequence_count = -1
        self.data_sequence_count = -1
        self.version_sequence_count = -1

def process_packet(data, packet_index, stats, error_log):
    bit_depth = stats.bit_depth
    sample_rate = stats.sample_rate
    packet_type = data[0:4][0] >> 4

    if packet_type == 0x4:
        if len(data) != difi_context_definition.sizeof():
            raise Exception(f"Packet size {len(data)} does not match expected size {difi_context_definition.sizeof()}")
        parsed = difi_context_definition.parse(data)
        errors = difi_context_definition.validate(parsed)
        if stats.context_sequence_count != -1 and parsed.header.seqNum != (stats.context_sequence_count + 1) % 16:
            errors.append(f"Context packet sequence count jumped from {stats.context_sequence_count} to {parsed.header.seqNum}")
        stats.context_sequence_count = parsed.header.seqNum
        if not errors:
            stats.compliant_context_count += 1
        else:
            print("Validation errors found:")
            stats.noncompliant_context_count += 1
            for error in errors:
                print(f" - {error}")
            with open(error_log, "a") as f:
                for error in errors:
                    for line in str(error).splitlines():
                        f.write(f"[Context][Packet {packet_index}] {line}\n")
        stats.bit_depth = parsed.dataPacketFormat.data_item_size + 1
        stats.sample_rate = parsed.sampleRate
        return

    if packet_type == 0x1 and bit_depth:
        parsed = difi_data_definition.parse(data)
        if bit_depth == 8:
            num_iq_samples = (parsed.header.pktSize - 7) * 4 // 2
            samples = np.frombuffer(parsed.payload, dtype=np.int8)
        elif bit_depth == 16:
            num_iq_samples = (parsed.header.pktSize - 7) * 4 // 4
            samples = np.frombuffer(parsed.payload, dtype=np.int16)
        else:
            raise Exception(f"Bit depth of {bit_depth} not supported for sample extraction")
        samples = samples.astype(np.float32)
        samples = samples[::2] + 1j * samples[1::2]
        if num_iq_samples != len(samples):
            raise Exception(f"Payload size doesnt match packet size, expected {num_iq_samples} IQ samples but got {len(samples)}")
        errors = difi_data_definition.validate(parsed)
        if stats.data_sequence_count != -1 and parsed.header.seqNum != (stats.data_sequence_count + 1) % 16:
            errors.append(f"Data packet sequence count jumped from {stats.data_sequence_count} to {parsed.header.seqNum}")
        stats.data_sequence_count = parsed.header.seqNum
        if not errors:
            stats.compliant_data_count += 1
        else:
            print("Validation errors found:")
            stats.noncompliant_data_count += 1
            for error in errors:
                print(f" - {error}")
            with open(error_log, "a") as f:
                for error in errors:
                    for line in str(error).splitlines():
                        f.write(f"[Data][Packet {packet_index}] {line}\n")
        return

    if packet_type == 0x5:
        if len(data) != difi_version_definition.sizeof():
            raise Exception(f"Packet size {len(data)} does not match expected size {difi_version_definition.sizeof()}")
        parsed = difi_version_definition.parse(data)
        errors = difi_version_definition.validate(parsed)
        if stats.version_sequence_count != -1 and parsed.header.seqNum != (stats.version_sequence_count + 1) % 16:
            errors.append(f"Version packet sequence count jumped from {stats.version_sequence_count} to {parsed.header.seqNum}")
        stats.version_sequence_count = parsed.header.seqNum
        if not errors:
            stats.compliant_version_count += 1
        else:
            print("Validation errors found:")
            stats.noncompliant_version_count += 1
            for error in errors:
                print(f" - {error}")
            with open(error_log, "a") as f:
                for error in errors:
                    for line in str(error).splitlines():
                        f.write(f"[Version][Packet {packet_index}] {line}\n")
        return
    
def main():
    parser = argparse.ArgumentParser(description="Parse DIFI packets from pcap or live UDP port.")
    parser.add_argument('--pcap', type=str, help='Path to pcap file to parse')
    parser.add_argument('--udp-port', type=int, help='UDP port to listen for live packets')
    parser.add_argument('--error-log', type=str, default='error_log.txt', help='Error log file')
    args = parser.parse_args()

    if not args.pcap and not args.udp_port:
        print("You must specify either --pcap or --udp-port.")
        return
    
    # Add the pcap filename or UDP port to top of error log file, as well as start time
    with open(args.error_log, "w") as f: # also clears the file
        if args.pcap:
            f.write(f"Parsing pcap file: {args.pcap}\n")
        if args.udp_port:
            f.write(f"Listening on UDP port: {args.udp_port}\n")
        f.write(f"Start time: {strftime('%Y-%m-%d %H:%M:%S')}\n")

    stats = PacketStats()
    packet_index = 0

    # PCAP Mode
    if args.pcap:
        for packet in PcapReader(args.pcap):
            data = bytes(packet[UDP].payload)
            process_packet(data, packet_index, stats, args.error_log)
            packet_index += 1

    # UDP Mode
    elif args.udp_port:
        print(f"Listening for UDP packets on port {args.udp_port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", args.udp_port))
        try:
            while True:
                data, addr = sock.recvfrom(4096)
                process_packet(data, packet_index, stats, args.error_log)
                packet_index += 1
        except KeyboardInterrupt:
            print("\nStopped listening.")
        finally:
            sock.close()

    with open(args.error_log, "a") as f:
        f.write(f"Total packets processed: {packet_index + 1}\n")
        
    print("compliant_context_count:", stats.compliant_context_count)
    print("noncompliant_context_count:", stats.noncompliant_context_count)
    print("compliant_data_count:", stats.compliant_data_count)
    print("noncompliant_data_count:", stats.noncompliant_data_count)
    print("compliant_version_count:", stats.compliant_version_count)
    print("noncompliant_version_count:", stats.noncompliant_version_count)
    if (stats.noncompliant_context_count == 0 and stats.noncompliant_data_count == 0 and stats.noncompliant_version_count == 0):
        print("Overall Result: PASS")
    else:
        print("Overall Result: FAIL")

if __name__ == "__main__":
    main()
