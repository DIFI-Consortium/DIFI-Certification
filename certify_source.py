import argparse
import socket
from time import strftime
from scapy.all import PcapReader, UDP
import numpy as np
import matplotlib.pyplot as plt
from packet_definitions.pn11 import process_pn11_qpsk, pn11_bits
import subprocess
import yaml
import os
import json
import time
import struct
from profiles import (
    available_profiles,
    load_profile,
    validate_profile_command,
    validate_profile_context,
    validate_profile_data,
    validate_profile_version,
)

# Per-version packet-definition modules
from packet_definitions.difi_context_v1_1 import difi_context_definition as difi_context_v1_1
from packet_definitions.difi_data_v1_1 import difi_data_definition as difi_data_v1_1
from packet_definitions.difi_version_v1_1 import difi_version_definition as difi_version_v1_1
from packet_definitions.difi_context_v1_2_1 import difi_context_definition as difi_context_v1_2_1
from packet_definitions.difi_data_v1_2_1 import difi_data_definition as difi_data_v1_2_1
from packet_definitions.difi_version_v1_2_1 import difi_version_definition as difi_version_v1_2_1
from packet_definitions.difi_command_v1_2_1 import difi_command_definition as difi_command_v1_2_1

SUPPORTED_DIFI_VERSIONS = ("1.1", "1.2.1")

# This script certifies a DIFI source, i.e., a device/software that generates DIFI packets; this script parses and verifies them
# It is not intended to run in realtime, you either process a pcap, or you can use this script to temporarily record a pcap that then gets processed
# Intended to run on Linux (eg Ubuntu 24)

# holds packet statistics and state, these are intended to only be used internally not saved to a file
class PacketStats:
    def __init__(self):
        self.bit_depth = None  # gets updated by context packet
        self.sample_rate = 1
        self.rf_freq = 0
        self.compliant_context_count = 0
        self.noncompliant_context_count = 0
        self.compliant_data_count = 0
        self.noncompliant_data_count = 0
        self.compliant_version_count = 0
        self.noncompliant_version_count = 0
        self.compliant_command_count = 0
        self.noncompliant_command_count = 0
        self.context_sequence_count = -1  # used to find gaps
        self.data_sequence_count = -1
        self.version_sequence_count = -1
        self.command_sequence_count = -1
        self.stream_id = -1  # stream ID can be 0 so we cant start it as None or 0
        self.context_timestamp = 0  # used to check monotonicity
        self.data_timestamp = 0
        self.version_timestamp = 0
        self.command_timestamp = 0
        self.data_packet_size = 0  # in words
        self.most_recent_samples = np.array([], dtype=np.complex64)  # for plotting at the end

output_yaml_dict = {}

try:
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    output_yaml_dict["difi_cert_commit_hash"] = commit_hash
except Exception:
    output_yaml_dict["difi_cert_commit_hash"] = "unknown"


def get_definitions(difi_version):
    if difi_version == "1.1":
        return {
            "version": "1.1",
            "context": difi_context_v1_1,
            "data": difi_data_v1_1,
            
            "version_pkt_types": (0x5,), # In v1.1 the version-flow packet is its own pktType (0x5)
            "version_pkt": difi_version_v1_1,
            "command_pkt": None,  # no command packets defined in v1.1
        }
    if difi_version == "1.2.1":
        return {
            "version": "1.2.1",
            "context": difi_context_v1_2_1,
            "data": difi_data_v1_2_1,
            # v1.2.1 spec moves version flow under Context (pktType 0x4) with packet class 0x0004, but real-world emitters frequently still use
            # the legacy v1.1 pktType 0x5; accept either.
            "version_pkt_types": (0x5, 0x4),
            "version_pkt": difi_version_v1_2_1,
            "command_pkt": difi_command_v1_2_1,
        }
    raise ValueError(f"Unsupported DIFI version: {difi_version}")


def process_packet(data, packet_index, stats, error_log, defs, plot_psd=False, validate_rf_freq=None, validate_if_freq=None, validate_bandwidth=None, create_iq_recording=False, profile=None):
    packet_type = data[0] >> 4
    # Bytes 12-15 of every DIFI packet are Word 4 = Information Class | Packet Class.
    # Peek the 16-bit packetClassCode without parsing so we can disambiguate
    # v1.2.1's pktType 0x4 (signal context vs version flow).
    packet_class_code = int.from_bytes(data[14:16], "big") if len(data) >= 16 else None

    # Version Flow Packet
    #   v1.1:   pktType 0x5
    #   v1.2.1: pktType 0x5 (legacy emitters) or pktType 0x4 with packet class 0x0004
    is_version_pkt = (
        defs["version_pkt"] is not None
        and packet_type in defs["version_pkt_types"]
        and (
            defs["version"] == "1.1"
            or packet_type == 0x5  # any 0x5 in v1.2.1 mode is a legacy version flow
            or packet_class_code == 0x0004
        )
    )
    if is_version_pkt:
        ver_def = defs["version_pkt"]
        if len(data) != ver_def.sizeof():
            raise Exception(f"Version packet size {len(data)} does not match expected size {ver_def.sizeof()}")
        parsed = ver_def.parse(data)
        errors = ver_def.validate(parsed)
        errors.extend(validate_profile_version(profile, parsed))
        if stats.version_sequence_count != -1 and parsed.header.seqNum != (stats.version_sequence_count + 1) % 16:
            errors.append(f"Version packet sequence count jumped from {stats.version_sequence_count} to {parsed.header.seqNum}")
        stats.version_sequence_count = parsed.header.seqNum
        if stats.stream_id == -1:
            stats.stream_id = parsed.streamId
        elif parsed.streamId != stats.stream_id:
            errors.append(f"Stream ID changed from {stats.stream_id} to {parsed.streamId}")
        timestamp = parsed.intSecsTimestamp + parsed.fracSecsTimestamp / 1e12
        if timestamp < stats.version_timestamp:
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

    # Context Packet
    if packet_type == 0x4:
        ctx_def = defs["context"]
        if len(data) != ctx_def.sizeof():
            raise Exception(f"Packet size {len(data)} does not match expected size {ctx_def.sizeof()}")
        parsed = ctx_def.parse(data)
        errors = ctx_def.validate(parsed)
        errors.extend(validate_profile_context(profile, parsed))
        if validate_rf_freq is not None and abs(parsed.rfFreq - validate_rf_freq) > 1e-6: # leave a tolerance
            errors.append(f"RF frequency {parsed.rfFreq} does not match expected {validate_rf_freq}")
        if validate_if_freq is not None and abs(parsed.ifFreq - validate_if_freq) > 1e-6:
            errors.append(f"IF frequency {parsed.ifFreq} does not match expected {validate_if_freq}")
        if validate_bandwidth is not None and abs(parsed.bandwidth - validate_bandwidth) > 1e-6:
            errors.append(f"Bandwidth {parsed.bandwidth} does not match expected {validate_bandwidth}")
        if stats.context_sequence_count != -1 and parsed.header.seqNum != (stats.context_sequence_count + 1) % 16:
            errors.append(f"Context packet sequence count jumped from {stats.context_sequence_count} to {parsed.header.seqNum}")
        stats.context_sequence_count = parsed.header.seqNum
        if stats.stream_id == -1:
            stats.stream_id = parsed.streamId
        elif parsed.streamId != stats.stream_id:
            errors.append(f"Stream ID changed from {stats.stream_id} to {parsed.streamId}")
        timestamp = parsed.intSecsTimestamp + parsed.fracSecsTimestamp / 1e12
        if timestamp < stats.context_timestamp:  # Eventually may want to switch to <=
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
        stats.rf_freq = parsed.rfFreq
        return None

    # Data Packet
    if packet_type == 0x1 and stats.bit_depth:
        parsed = defs["data"].parse(data)
        if stats.bit_depth == 4:
            # Each byte contains two 4-bit signed samples: I then Q, I don't think endianness matters here since it's just 1 byte
            payload = parsed.payload
            num_iq_samples = (parsed.header.pktSize - 7) * 4  # 1 byte holds 1 IQ pair (4b I + 4b Q)
            samples = []
            for b in payload:
                i_raw = (b >> 4) & 0x0F # high nibble
                q_raw = b & 0x0F # low nibble
                i = i_raw - 16 if i_raw & 0x8 else i_raw # convert from unsigned to signed 4-bit
                q = q_raw - 16 if q_raw & 0x8 else q_raw
                samples.extend([i, q])
            samples = np.array(samples, dtype=np.float32)
            samples = samples / 8.0  # normalize to -1.0 to 1.0
            samples = samples[::2] + 1j * samples[1::2]
            samples = samples.astype(np.complex64)
        elif stats.bit_depth == 8:
            num_iq_samples = (parsed.header.pktSize - 7) * 4 // 2
            samples = np.frombuffer(parsed.payload, dtype=np.int8)
            samples = samples / 128.0  # normalize to -1.0 to 1.0
            samples = samples.astype(np.float32)
            samples = samples[::2] + 1j * samples[1::2]
            samples = samples.astype(np.complex64)
        elif stats.bit_depth == 12:
            # Assume signed 12-bit, packed as big-endian, I then Q, 3 bytes = 2 samples.
            payload = parsed.payload
            num_iq_samples = ((parsed.header.pktSize - 7) * 4 * 8) // 24  # 24 bits per 2 IQ samples
            if len(payload) * 8 < num_iq_samples * 12:
                raise Exception(f"Payload too small for {num_iq_samples} 12-bit IQ samples")
            samples = []
            i = 0
            while i + 2 < len(payload):
                b0 = payload[i]
                b1 = payload[i+1]
                b2 = payload[i+2]
                # Big-endian: first sample is upper 12 bits, second sample is lower 12 bits
                s1 = (b0 << 4) | (b1 >> 4)  # Sample 1: upper 12 bits
                s2 = ((b1 & 0x0F) << 8) | b2  # Sample 2: lower 12 bits
                if s1 & 0x800:  # Convert to signed
                    s1 = s1 - 0x1000
                if s2 & 0x800:
                    s2 = s2 - 0x1000
                samples.extend([s1, s2])
                i += 3
            samples = np.array(samples, dtype=np.float32)
            samples = samples / 2048.0  # normalize to -1.0 to 1.0
            samples = samples[::2] + 1j * samples[1::2]
            samples = samples.astype(np.complex64)
        elif stats.bit_depth == 16:
            num_iq_samples = (parsed.header.pktSize - 7) * 4 // 4
            samples = np.frombuffer(parsed.payload, dtype='>i2')  # big-endian!
            samples = samples / 32768.0  # normalize to -1.0 to 1.0
            samples = samples.astype(np.float32)
            samples = samples[::2] + 1j * samples[1::2]
            samples = samples.astype(np.complex64)
        else:
            raise Exception(
                f"Bit depth of {stats.bit_depth} not supported for sample extraction")
        if num_iq_samples != len(samples):
            raise Exception(f"Payload size doesnt match packet size, expected {num_iq_samples} IQ samples but got {len(samples)}")
        if create_iq_recording:
            with open("iq_recording.sigmf-data", "ab") as f:
                f.write(samples.tobytes())
        stats.most_recent_samples = samples  # for plotting at the end
        if plot_psd:  # TODO: move this plotting code to a separate function
            plt.ion()
            PSD = 10 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples))) ** 2 / (len(samples) * stats.sample_rate))
            f = np.linspace(-stats.sample_rate / 2,
                            stats.sample_rate / 2, len(PSD))
            if not hasattr(process_packet, "fig") or process_packet.fig is None:
                process_packet.fig, process_packet.axs = plt.subplots(3, 1, figsize=(8, 10))
            fig, axs = process_packet.fig, process_packet.axs
            # PSD subplot
            axs[0].cla()
            axs[0].plot(f / 1e6, PSD)
            axs[0].set_xlabel("Frequency (MHz)")
            axs[0].set_ylabel("Power Spectral Density (dB/Hz)")
            axs[0].set_ylim(-90, -30)
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
        errors = defs["data"].validate(parsed)
        errors.extend(validate_profile_data(profile, parsed))
        if stats.data_sequence_count != -1 and parsed.header.seqNum != (stats.data_sequence_count + 1) % 16:
            errors.append(f"Data packet sequence count jumped from {stats.data_sequence_count} to {parsed.header.seqNum}")
        stats.data_sequence_count = parsed.header.seqNum
        if stats.stream_id == -1:
            stats.stream_id = parsed.streamId
        elif parsed.streamId != stats.stream_id:
            errors.append(f"Stream ID changed from {stats.stream_id} to {parsed.streamId}")
        timestamp = parsed.intSecsTimestamp + parsed.fracSecsTimestamp / 1e12
        if timestamp < stats.data_timestamp: # Eventually may want to switch to <=
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

    # Command Packet (v1.2.1+ only — Timing Flow Control, packet classes 0x0005 / 0x0006)
    if packet_type == 0x6 and defs["command_pkt"] is not None:
        cmd_def = defs["command_pkt"]
        if len(data) != cmd_def.sizeof():
            raise Exception(f"Command packet size {len(data)} does not match expected size {cmd_def.sizeof()}")
        parsed = cmd_def.parse(data)
        errors = cmd_def.validate(parsed)
        errors.extend(validate_profile_command(profile, parsed))
        if stats.command_sequence_count != -1 and parsed.header.seqNum != (stats.command_sequence_count + 1) % 16:
            errors.append(f"Command packet sequence count jumped from {stats.command_sequence_count} to {parsed.header.seqNum}")
        stats.command_sequence_count = parsed.header.seqNum
        if stats.stream_id == -1:
            stats.stream_id = parsed.streamId
        elif parsed.streamId != stats.stream_id:
            errors.append(f"Stream ID changed from {stats.stream_id} to {parsed.streamId}")
        # Fractional seconds in command packet are picoseconds (class 0x0006) or sample count (class 0x0005);
        # the monotonicity check still works against the same units packet-to-packet within the run.
        timestamp = parsed.intSecsTimestamp + parsed.fracSecsTimestamp / 1e12
        if timestamp < stats.command_timestamp:
            errors.append(f"Command packet timestamp went backwards from {stats.command_timestamp} to {timestamp}")
        stats.command_timestamp = timestamp
        if not errors:
            stats.compliant_command_count += 1
        else:
            print("Validation errors found:")
            stats.noncompliant_command_count += 1
            for error in errors:
                print(f" - {error}")
            with open(error_log, "a") as f:
                for error in errors:
                    for line in str(error).splitlines():
                        f.write(f"[Command][Packet {packet_index}] {line}\n")
        return None



if __name__ == "__main__":  
    # Allow cli args or a YAML file
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument("--config", type=str, help="YAML config file with arguments")
    config_args, remaining_argv = base_parser.parse_known_args()
    defaults = {}
    parser = argparse.ArgumentParser(description="Parse DIFI packets from pcap or live UDP port.", parents=[base_parser])
    parser.add_argument("--pcap", type=str, help="Path to pcap file to parse")
    parser.add_argument("--udp-port", type=int, help="UDP port to listen for live packets")
    parser.add_argument("--error-log", type=str, default="error_log.txt", help="Error log file")
    parser.add_argument("--plot-psd", action="store_true", help="Plot the Power Spectral Density (PSD)")
    parser.add_argument("--pn11", action="store_true", help="Run PN11 receiver and report BER")
    parser.add_argument("--sps", type=int, default=4, help="Samples per symbol for PN11 QPSK demod (default: 4)")
    parser.add_argument("--company", type=str, default="Fillmein", help="Company name")
    parser.add_argument("--product-name", type=str, default="Fillmein", help="Product name")
    parser.add_argument("--product-version", type=str, default="0.0", help="Product version")
    parser.add_argument("--validate-rf-freq", type=float, help="(Optional) Expected RF frequency in Hz for validation")
    parser.add_argument("--validate-if-freq", type=float, help="(Optional) Expected IF frequency in Hz for validation")
    parser.add_argument("--validate-bandwidth", type=float, help="(Optional) Expected bandwidth in Hz for validation")
    parser.add_argument("--create-iq-recording", action="store_true", help="Create IQ recording (SigMF format) file from samples in data packets")
    parser.add_argument("--difi-version", type=str, default="1.2.1", choices=list(SUPPORTED_DIFI_VERSIONS),
                        help="DIFI specification version to validate against (default: 1.2.1)")
    parser.add_argument(
        "--profile",
        type=str,
        default="",
        choices=available_profiles(),
        help="Specific profile to do extra validations on",
    )

    valid_args = set()
    for action in parser._actions:
        if action.dest != argparse.SUPPRESS:
            valid_args.add(action.dest.replace('_', '-'))
    if config_args.config:
        with open(config_args.config, "r") as f:
            yaml_args = yaml.safe_load(f)
            if yaml_args:
                # Accept both dash and underscore in YAML keys, but always set defaults with underscores
                normalized_yaml_args = {}
                for k, v in yaml_args.items():
                    k_norm = k.replace('-', '_')
                    normalized_yaml_args[k_norm] = v
                yaml_keys = set(k.replace('_', '-') for k in normalized_yaml_args.keys())
                invalid_keys = yaml_keys - valid_args
                if invalid_keys:
                    raise ValueError(f"Unknown argument(s) in YAML config: {', '.join(invalid_keys)}")
                defaults.update(normalized_yaml_args)
    parser.set_defaults(**defaults)
    args = parser.parse_args(remaining_argv)

    # Resolve the profile before doing any capture/file work so an invalid name
    # fails even when the input contains no packets of a profile-validated type.
    load_profile(args.profile)

    if not args.pcap and not args.udp_port:
        print("You must specify either --pcap or --udp-port")
        exit()
    if args.pcap and args.udp_port:
        print("Specify either --pcap or --udp-port, not both")
        exit()

    if args.create_iq_recording:
        if os.path.exists("iq_recording.sigmf-data"):
            os.remove("iq_recording.sigmf-data")

    # Add the pcap filename or UDP port to top of error log file, as well as start time
    with open(args.error_log, "w") as f:  # also clears the file
        if args.pcap:
            f.write(f"Parsing pcap file: {args.pcap}\n")
        if args.udp_port:
            f.write(f"Listening on UDP port: {args.udp_port}\n")
        f.write(f"Start time: {strftime('%Y-%m-%d %H:%M:%S')}\n")

    # If UDP Mode, first record a live stream to a temporary pcap file, using tcpdump for max performance
    if args.udp_port:
        pcap_filename = "temp.pcap"
        PCAP_GLOBAL_HEADER = (
            b'\xd4\xc3\xb2\xa1'  # magic number
            b'\x02\x00'          # version major
            b'\x04\x00'          # version minor
            b'\x00\x00\x00\x00'  # thiszone
            b'\x00\x00\x00\x00'  # sigfigs
            b'\xff\xff\x00\x00'  # snaplen
            b'\x93\x00\x00\x00'  # network (LINKTYPE_USER0 = 147; pcap holds raw UDP payloads with no L2/L3/L4 framing)
        )
        print(f"Recording UDP packets on port {args.udp_port}, hit control-c to finish...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # TCP packets get ignored
        sock.bind(("", args.udp_port))
        count = 0
        with open(pcap_filename, 'wb') as f:
            f.write(PCAP_GLOBAL_HEADER)
            try:
                while True:
                    data, addr = sock.recvfrom(65535)
                    if len(data) < 28: # ignore packets too small to be DIFI
                        continue
                    # Write to temp pcap file
                    ts = time.time()
                    ts_sec = int(ts)
                    ts_usec = int((ts - ts_sec) * 1_000_000)
                    pkt_len = len(data)
                    header = struct.pack('<IIII', ts_sec, ts_usec, pkt_len, pkt_len)
                    f.write(header)
                    f.write(data)
                    count += 1
                    if count % 100 == 0:
                        print(f"Recorded {count} packets...", end='\r')
            except KeyboardInterrupt:
                print("\nStopped listening.")
            finally:
                sock.close()

        print(f"Recorded {count} packets to {pcap_filename}")
        if count == 0:
            print("No packets recorded, exiting.")
            exit()

    # Process PCAP (either provided --pcap or the one we just recorded if --udp_port was used)
    stats = PacketStats()
    packet_index = 0
    if args.pcap:
        pcap_filename = args.pcap
    defs = get_definitions(args.difi_version)
    output_yaml_dict["difi_version"] = args.difi_version
    print(f"Processing packets from {pcap_filename} (DIFI v{args.difi_version})...")
    samples_buffer = np.array([], dtype=np.complex64)
    pn11_total_bit_errors = 0
    pn11_total_bits = 0
    for packet in PcapReader(pcap_filename):
        if args.udp_port: # pcaps made above did not include the headers, so no UDP layer
            data = bytes(packet)
        else: # if we pass in a pcap it is assumed to include headers, and be wireshark compliant, so we look for UDP layer and extract payload
            if UDP not in packet:
                continue
            data = bytes(packet[UDP].payload)
        if len(data) < 28: # ignore packets too small to be DIFI
            continue
        samples = process_packet(data, packet_index, stats, args.error_log, defs, plot_psd=args.plot_psd, validate_rf_freq=args.validate_rf_freq,
                                 validate_if_freq=args.validate_if_freq, validate_bandwidth=args.validate_bandwidth, create_iq_recording=args.create_iq_recording, profile=args.profile)
        if samples is not None and args.pn11:
            samples_buffer = np.concatenate((samples_buffer, samples))
            if len(samples_buffer) >= 2047 * args.sps * 2: # Process PN11 in chunks, 2 sequences worth (2047 symbols * sps), so we know there's 1 full sequence in the middle
                demod_bits = process_pn11_qpsk(samples_buffer, args.sps)
                if len(demod_bits) >= len(pn11_bits):
                    bit_errors = sum([demod_bits[i] != pn11_bits[i] for i in range(len(pn11_bits))])
                    pn11_total_bit_errors += bit_errors
                    pn11_total_bits += len(pn11_bits)
                    BER = bit_errors / len(pn11_bits)
                    print("BER:", BER)
                else:
                    print(f"Skipping BER (got {len(demod_bits)} demod bits, need {len(pn11_bits)})")
                samples_buffer = np.array([], dtype=np.complex64) # for now just clear buffer after each processing, in theory we could keep leftover samples though
        packet_index += 1
        if packet_index % 100 == 0:
            print(f"Processed {packet_index} packets...", end='\r')

    with open(args.error_log, "a") as f:
        f.write(f"Total packets processed: {packet_index}\n")

    print("compliant_context_count:", stats.compliant_context_count)
    print("noncompliant_context_count:", stats.noncompliant_context_count)
    print("compliant_data_count:", stats.compliant_data_count)
    print("noncompliant_data_count:", stats.noncompliant_data_count)
    print("compliant_version_count:", stats.compliant_version_count)
    print("noncompliant_version_count:", stats.noncompliant_version_count)
    if defs["command_pkt"] is not None:
        print("compliant_command_count:", stats.compliant_command_count)
        print("noncompliant_command_count:", stats.noncompliant_command_count)
    if (stats.noncompliant_context_count == 0
            and stats.noncompliant_data_count == 0
            and stats.noncompliant_version_count == 0
            and stats.noncompliant_command_count == 0):
        print("Overall Result: PASS")
        output_yaml_dict["overall_result"] = "PASS"
    else:
        print("Overall Result: FAIL")
        output_yaml_dict["overall_result"] = "FAIL"

    if args.create_iq_recording:
        # Create spectrogram
        x = np.fromfile("iq_recording.sigmf-data", dtype=np.complex64)
        fft_size = 1024
        num_rows = len(x) // fft_size # // is an integer division which rounds down
        spectrogram = np.zeros((num_rows, fft_size))
        for i in range(num_rows):
            spectrogram[i,:] = 10*np.log10(np.abs(np.fft.fftshift(np.fft.fft(x[i*fft_size:(i+1)*fft_size])))**2 / (fft_size * stats.sample_rate)) # dB/Hz
        PSD = np.mean(spectrogram, axis=0) # Calc PSD by averaging over the time axis
        plt.figure(1)
        plt.imshow(spectrogram, aspect='auto', extent = [stats.sample_rate/-2/1e6, stats.sample_rate/2/1e6, len(x)/stats.sample_rate, 0])
        plt.xlabel("Frequency [MHz]")
        plt.ylabel("Time [s]")
        plt.savefig("iq_recording_spectrogram.png", dpi=300, bbox_inches='tight')

        # Create SigMF metadata file
        sigmf_meta =   {
            "global": {
                "core:datatype": "cf32_le", # we convert to np.complex64 during sample parsing
                "core:sample_rate": stats.sample_rate,
                "core:hw": args.product_name,
                "core:author": args.company,
                "core:version": "1.0.0"
            },
            "captures": [
                {
                    "core:sample_start": 0,
                    "core:frequency": stats.rf_freq
                }
            ],
            "annotations": []
        }
        with open("iq_recording" + ".sigmf-meta", "w") as f:
            json.dump(sigmf_meta, f, indent=2)
    else:
        # PSD of only the last data packet
        if len(stats.most_recent_samples) == 0:
            print("No data packets found, cannot plot PSD.")
            samples = np.ones(1024) # just plot something so the code runs, but it will be flat since it's all ones
        else:
            samples = stats.most_recent_samples
        PSD = 10 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples))) ** 2 / (len(samples) * stats.sample_rate)) # dB/Hz
    
    f = np.linspace(-stats.sample_rate / 2, stats.sample_rate / 2, len(PSD))
    plt.figure(2)
    plt.plot(f / 1e6, PSD)
    plt.xlabel("Frequency [MHz]")
    plt.ylabel("Power Spectral Density [dB/Hz]")
    # Bit of analysis to find -3 dB bandwidth
    max_val_after_smoothing = 10.0 * np.log10(np.max(np.convolve(10**(PSD/10), np.ones(10)/10, mode='same')))
    plt.axhline(y=max_val_after_smoothing, color='r', linestyle=':')
    plt.text(f[0] / 1e6, max_val_after_smoothing, f"{max_val_after_smoothing:.2f} dB", verticalalignment='bottom', horizontalalignment='left', color='r')
    half_power_point = max_val_after_smoothing - 3
    indices = np.where(PSD >= half_power_point)[0]
    if len(indices) > 0:
        left_idx = indices[0]
        right_idx = indices[-1]
        plt.axvline(x=f[left_idx] / 1e6, color='r', linestyle=':')
        plt.axvline(x=f[right_idx] / 1e6, color='r', linestyle=':')
        bandwidth_mhz = float((f[right_idx] - f[left_idx]) / 1e6)
        ax = plt.gca()
        plt.text((f[left_idx] + f[right_idx]) / 2 / 1e6, ax.get_ylim()[1], f"{bandwidth_mhz:.2f} MHz", verticalalignment='bottom', horizontalalignment='center', color='r')
        output_yaml_dict["measured_bandwidth_mhz"] = bandwidth_mhz
    plt.grid()
    plt.savefig("power_spectral_density.png")

    output_yaml_dict["company"] = args.company
    output_yaml_dict["product_name"] = args.product_name
    output_yaml_dict["product_version"] = args.product_version
    output_yaml_dict["bit_depth"] = stats.bit_depth
    output_yaml_dict["sample_rate_hz"] = stats.sample_rate
    if args.pn11:
        if pn11_total_bits > 0:
            output_yaml_dict["ber"] = pn11_total_bit_errors / pn11_total_bits
        else:
            output_yaml_dict["ber"] = None  # not enough samples to compute BER
    timestamp_str = strftime("%Y%m%d_%H%M%S")
    output_yaml_filename = f"certify_source_summary_{timestamp_str}.yaml"
    with open(output_yaml_filename, "w") as f:
        yaml.dump(output_yaml_dict, f)
