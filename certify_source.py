import argparse
import socket
from time import strftime
from scapy.all import PcapReader, UDP
from difi_context_v1_1 import difi_context_definition
from difi_data_v1_1 import difi_data_definition
from difi_version_v1_1 import difi_version_definition
import numpy as np
import matplotlib.pyplot as plt
from pn11 import gen_pn11_qpsk, process_pn11_qpsk, pn11_bits
import subprocess
import yaml


# holds packet statistics and state, these are intended to only be used internally
class PacketStats:
    def __init__(self):
        self.bit_depth = 8  # gets updated by context packet
        self.sample_rate = 1
        self.compliant_context_count = 0
        self.noncompliant_context_count = 0
        self.compliant_data_count = 0
        self.noncompliant_data_count = 0
        self.compliant_version_count = 0
        self.noncompliant_version_count = 0
        self.context_sequence_count = -1  # used to find gaps
        self.data_sequence_count = -1
        self.version_sequence_count = -1
        self.stream_id = -1  # stream ID can be 0 so we cant start it as None or 0
        self.context_timestamp = 0  # used to check monotonicity
        self.data_timestamp = 0
        self.version_timestamp = 0
        self.data_packet_size = 0  # in words
        self.most_recent_samples = np.array([], dtype=np.complex64)  # for plotting at the end


output_yaml_dict = {}

try:
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    output_yaml_dict["difi_cert_commit_hash"] = commit_hash
except Exception as e:
    output_yaml_dict["difi_cert_commit_hash"] = "unknown"


def process_packet(data, packet_index, stats, error_log, plot_psd=False):
    bit_depth = stats.bit_depth
    sample_rate = stats.sample_rate
    packet_type = data[0:4][0] >> 4

    # Context Packet
    if packet_type == 0x4:
        if len(data) != difi_context_definition.sizeof():
            raise Exception(f"Packet size {len(data)} does not match expected size {difi_context_definition.sizeof()}")
        parsed = difi_context_definition.parse(data)
        errors = difi_context_definition.validate(parsed)
        if stats.context_sequence_count != -1 and parsed.header.seqNum != (stats.context_sequence_count + 1) % 16:
            errors.append(f"Context packet sequence count jumped from {stats.context_sequence_count} to {parsed.header.seqNum}")
        stats.context_sequence_count = parsed.header.seqNum
        if stats.stream_id == -1:
            stats.stream_id = parsed.streamId
        elif parsed.streamId != stats.stream_id:
            errors.append(f"Stream ID changed from {stats.stream_id} to {parsed.streamId}")
        timestamp = parsed.intSecsTimestamp + parsed.fracSecsTimestamp / 1e12
        if timestamp <= stats.context_timestamp:  # might want just a < but TBD
            errors.append(f"Context packet timestamp went backwards from {stats.context_timestamp} to {timestamp}")
        stats.context_timestamp = timestamp
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
        return None

    # Data Packet
    if packet_type == 0x1 and bit_depth:
        parsed = difi_data_definition.parse(data)
        if bit_depth == 8:
            num_iq_samples = (parsed.header.pktSize - 7) * 4 // 2
            samples = np.frombuffer(parsed.payload, dtype=np.int8)
            samples = samples / 128.0  # normalize to -1.0 to 1.0
        elif bit_depth == 16:
            num_iq_samples = (parsed.header.pktSize - 7) * 4 // 4
            samples = np.frombuffer(parsed.payload, dtype=np.int16)
            samples = samples / 32768.0  # normalize to -1.0 to 1.0
        else:
            raise Exception(f"Bit depth of {bit_depth} not supported for sample extraction")
        samples = samples.astype(np.float32)
        samples = samples[::2] + 1j * samples[1::2]
        stats.most_recent_samples = samples  # for plotting at the end
        if plot_psd:
            plt.ion()
            PSD = 10 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples))) ** 2)
            f = np.linspace(-sample_rate / 2, sample_rate / 2, len(PSD))
            if not hasattr(process_packet, "fig") or process_packet.fig is None:
                process_packet.fig, process_packet.axs = plt.subplots(3, 1, figsize=(8, 10))
            fig, axs = process_packet.fig, process_packet.axs
            # PSD subplot
            axs[0].cla()
            axs[0].plot(f / 1e6, PSD)
            axs[0].set_xlabel("Frequency (MHz)")
            axs[0].set_ylabel("Power Spectral Density (dB/Hz)")
            axs[0].set_ylim(-30, 30)
            axs[0].grid()
            # IQ scatter subplot
            axs[1].cla()
            axs[1].plot(samples.real, samples.imag, ".", markersize=5)
            axs[1].set_xlabel("I")
            axs[1].set_ylabel("Q")
            axs[1].grid()
            # I/Q vs Time subplot
            axs[2].cla()
            axs[2].plot(samples.real)
            axs[2].plot(samples.imag)
            axs[2].set_xlabel("Time")
            axs[2].set_ylabel("Sample Value")
            axs[2].grid()
            fig.tight_layout()
            fig.canvas.draw()
            fig.canvas.flush_events()
        if num_iq_samples != len(samples):
            raise Exception(f"Payload size doesnt match packet size, expected {num_iq_samples} IQ samples but got {len(samples)}")
        errors = difi_data_definition.validate(parsed)
        if stats.data_sequence_count != -1 and parsed.header.seqNum != (stats.data_sequence_count + 1) % 16:
            errors.append(f"Data packet sequence count jumped from {stats.data_sequence_count} to {parsed.header.seqNum}")
        stats.data_sequence_count = parsed.header.seqNum
        if stats.stream_id == -1:
            stats.stream_id = parsed.streamId
        elif parsed.streamId != stats.stream_id:
            errors.append(f"Stream ID changed from {stats.stream_id} to {parsed.streamId}")
        timestamp = parsed.intSecsTimestamp + parsed.fracSecsTimestamp / 1e12
        if timestamp <= stats.data_timestamp:
            errors.append(f"Data packet timestamp went backwards from {stats.data_timestamp} to {timestamp}")
        stats.data_timestamp = timestamp
        if not stats.data_packet_size:
            stats.data_packet_size = parsed.header.pktSize  # in words
            output_yaml_dict["data_packet_size_in_words"] = stats.data_packet_size
        elif parsed.header.pktSize != stats.data_packet_size:
            errors.append(f"Data packet size changed from {stats.data_packet_size} to {parsed.header.pktSize}")
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
        return samples

    # Version Packet
    if packet_type == 0x5:
        if len(data) != difi_version_definition.sizeof():
            raise Exception(f"Packet size {len(data)} does not match expected size {difi_version_definition.sizeof()}")
        parsed = difi_version_definition.parse(data)
        errors = difi_version_definition.validate(parsed)
        if stats.version_sequence_count != -1 and parsed.header.seqNum != (stats.version_sequence_count + 1) % 16:
            errors.append(f"Version packet sequence count jumped from {stats.version_sequence_count} to {parsed.header.seqNum}")
        stats.version_sequence_count = parsed.header.seqNum
        if stats.stream_id == -1:
            stats.stream_id = parsed.streamId
        elif parsed.streamId != stats.stream_id:
            errors.append(f"Stream ID changed from {stats.stream_id} to {parsed.streamId}")
        timestamp = parsed.intSecsTimestamp + parsed.fracSecsTimestamp / 1e12
        if timestamp <= stats.version_timestamp:
            errors.append(f"Version packet timestamp went backwards from {stats.version_timestamp} to {timestamp}")
        stats.version_timestamp = timestamp
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
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse DIFI packets from pcap or live UDP port.")
    parser.add_argument("--pcap", type=str, help="Path to pcap file to parse")
    parser.add_argument("--udp-port", type=int, help="UDP port to listen for live packets")
    parser.add_argument("--error-log", type=str, default="error_log.txt", help="Error log file")
    parser.add_argument("--plot-psd", action="store_true", help="Plot the Power Spectral Density (PSD)")
    parser.add_argument("--pn11", action="store_true", help="Run PN11 receiver and report BER")
    parser.add_argument("--company", type=str, default="Fillmein", help="Company name")
    parser.add_argument("--product-name", type=str, default="Fillmein", help="Product name")
    parser.add_argument("--product-version", type=str, default="0.0", help="Product version")
    args = parser.parse_args()

    if not args.pcap and not args.udp_port:
        print("You must specify either --pcap or --udp-port.")
        exit()

    # Add the pcap filename or UDP port to top of error log file, as well as start time
    with open(args.error_log, "w") as f:  # also clears the file
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
            process_packet(data, packet_index, stats, args.error_log, plot_psd=args.plot_psd)
            packet_index += 1

    # UDP Mode
    elif args.udp_port:
        print(f"Listening for UDP packets on port {args.udp_port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", args.udp_port))
        try:
            samples_buffer = np.array([], dtype=np.complex64)
            while True:
                data, addr = sock.recvfrom(4096)
                samples = process_packet(data, packet_index, stats, args.error_log, plot_psd=args.plot_psd)
                if samples is not None and args.pn11:
                    samples_buffer = np.concatenate((samples_buffer, samples))
                    # Process PN11 in chunks of 2048 samples
                    if len(samples_buffer) >= 4092 * 2:  # 2 sequences worth, so we know there's 1 full sequence in the middle
                        demod_bits = process_pn11_qpsk(samples_buffer)
                        BER = sum([demod_bits[i] != pn11_bits[i] for i in range(len(pn11_bits))]) / len(pn11_bits)
                        print("BER:", BER)
                        # for now just clear buffer after each processing, in theory we could keep leftover samples though
                        samples_buffer = np.array([], dtype=np.complex64)
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
    if stats.noncompliant_context_count == 0 and stats.noncompliant_data_count == 0 and stats.noncompliant_version_count == 0:
        print("Overall Result: PASS")
        output_yaml_dict["overall_result"] = "PASS"
    else:
        print("Overall Result: FAIL")
        output_yaml_dict["overall_result"] = "FAIL"

    # Always plot the last PSD at the end
    samples = stats.most_recent_samples
    PSD = 10 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples))) ** 2)
    f = np.linspace(-stats.sample_rate / 2, stats.sample_rate / 2, len(PSD))
    plt.plot(f / 1e6, PSD)
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Power Spectral Density (dB/Hz)")
    plt.grid()
    plt.savefig("final_data_packet_psd.png")

    output_yaml_dict["company"] = args.company
    output_yaml_dict["product_name"] = args.product_name
    output_yaml_dict["product_version"] = args.product_version
    output_yaml_dict["bit_depth"] = stats.bit_depth
    output_yaml_dict["sample_rate_hz"] = stats.sample_rate
    timestamp_str = strftime("%Y%m%d_%H%M%S")
    output_yaml_filename = f"certify_source_summary_{timestamp_str}.yaml"
    with open(output_yaml_filename, "w") as f:
        yaml.dump(output_yaml_dict, f)

# TODO CREATE REQUIREMENTS.TXT
