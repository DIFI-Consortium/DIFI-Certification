import socket
import threading
import time
import argparse
from difi_context_v1_1 import difi_context_definition
from difi_data_v1_1 import difi_data_definition
from difi_version_v1_1 import difi_version_definition
import numpy as np
from pn11 import gen_pn11_qpsk
import subprocess
import yaml
from time import strftime

CONTEXT_PACKETS_PER_SEC = 10
VERSION_PACKETS_PER_SEC = 2

context = {
    "header": {
        "pktType": 4,
        "classId": 1,
        "reserved": 0,
        "tsm": 1,
        "tsi": "POSIX",
        "tsf": 2,
        "seqNum": -1,  # FILL IN BEFORE SENDING
        "pktSize": 27,
    },
    "streamId": 0,
    "classId": {
        "paddingBits": 0,
        "reserved1": 0,
        "oui": 6971934,
        "infoClassCode": 0,
        "packetClassCode": 1,
    },
    "intSecsTimestamp": 1740688471,
    "fracSecsTimestamp": 200000000000,
    "cif0": 4223238144,
    "refPoint": 100,
    "bandwidth": 800000.0,
    "ifFreq": 0.0,
    "rfFreq": 1950000000.0,
    "ifBandOffset": 0.0,
    "refLevel1": 0.0,
    "refLevel2": 0.0,
    "stage1GainAtten": 0.0,
    "stage2GainAtten": -13.25,
    "sampleRate": 1000000.0,
    "timeStampAdj": 0,
    "timeStampCal": 0,
    "stateEventInd": {
        "misc_enables": 160,
        "reserved": 0,
        "calibrated_time_indicator": 0,
        "valid_data_indicator": 0,
        "reference_lock_indicator": 1,
        "agc_mgc_indicator": 0,
        "detected_signal_indicator": 0,
        "spectral_inversion_indicator": 0,
        "over_range_indicator": 0,
        "sample_loss_indicator": 0,
        "reserved2": 0,
        "user_defined": 0,
    },
    "dataPacketFormat": {
        "packing_method": "link_efficient",
        "real_complex_type": "complex_cartesian",
        "data_item_format": "signed_fixed_point",
        "sample_repeat_indicator": "no_repeat",
        "event_tag_size": 0,
        "channel_tag_size": 0,
        "data_item_fraction_size": 0,
        "item_packing_field_size": 0,  # FILL IN BEFORE SENDING
        "data_item_size": 0,  # FILL IN BEFORE SENDING
        "repeat_count": 0,
        "vector_size": 0,
    },
}

version = {
    "header": {
        "pktType": 5,
        "classId": 1,
        "reserved": 0,
        "tsm": 1,
        "tsi": "POSIX",
        "tsf": 2,
        "seqNum": -1,  # FILL IN BEFORE SENDING
        "pktSize": 11,
    },
    "streamId": 0,
    "classId": {
        "paddingBits": 0,
        "reserved1": 0,
        "oui": 6971934,
        "infoClassCode": 1,
        "packetClassCode": 4,
    },
    "intSecsTimestamp": 1740688471,
    "fracSecsTimestamp": 500000000000,
    "cif0": "no_change",
    "cif1": 12,
    "v49SpecVersion": 4,
    "versionInfo": {
        "year": 2025,
        "day": 49,
        "revision": 1,
        "type": 0,
        "icdVersion": 0,
    },
}

data = {
    "header": {
        "pktType": 1,
        "classId": 1,
        "reserved": 0,
        "tsm": 0,
        "tsi": "POSIX",
        "tsf": 2,
        "seqNum": -1,  # FILL IN BEFORE SENDING
        "pktSize": -1,  # FILL IN BEFORE SENDING
    },
    "streamId": 0,
    "classId": {
        "paddingBits": 0,
        "reserved1": 0,
        "oui": 6971934,
        "infoClassCode": 0,
        "packetClassCode": 0,
    },
    "intSecsTimestamp": 1740688471,
    "fracSecsTimestamp": 106369572000,
    "payload": "",
}

tx_samples = gen_pn11_qpsk()
tx_samples_tiled = np.concatenate((tx_samples, tx_samples, tx_samples, tx_samples))
tx_samples_i = 0

output_yaml_dict = {}

try:
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    output_yaml_dict["difi_cert_commit_hash"] = commit_hash
except Exception as e:
    output_yaml_dict["difi_cert_commit_hash"] = "unknown"

def send_packet(sock, addr, packet_bytes):
    sock.sendto(packet_bytes, addr)

def context_sender(sock, addr, bit_depth):
    interval = 1.0 / CONTEXT_PACKETS_PER_SEC
    seq_num = 0
    while True:
        context["header"]["seqNum"] = seq_num
        context["dataPacketFormat"]["item_packing_field_size"] = bit_depth - 1
        context["dataPacketFormat"]["data_item_size"] = bit_depth - 1
        pkt = difi_context_definition.build(context)
        send_packet(sock, addr, pkt)
        seq_num = (seq_num + 1) % 16
        time.sleep(interval)


def version_sender(sock, addr):
    interval = 1.0 / VERSION_PACKETS_PER_SEC
    seq_num = 0
    while True:
        version["header"]["seqNum"] = seq_num
        pkt = difi_version_definition.build(version)
        send_packet(sock, addr, pkt)
        seq_num = (seq_num + 1) % 16
        time.sleep(interval)


def data_sender(sock, addr, sample_rate, samples_per_packet, bit_depth):
    global tx_samples_i
    interval = samples_per_packet / sample_rate  # seconds between packets
    seq_num = 0
    while True:
        samples = tx_samples_tiled[tx_samples_i:tx_samples_i + samples_per_packet]
        tx_samples_i = (tx_samples_i + samples_per_packet) % len(tx_samples)
        if bit_depth == 8:
            samples_interleaved = np.empty((samples_per_packet * 2,), dtype=np.int8)
            samples_interleaved[0::2] = np.clip(np.real(samples * 128), -128, 127).astype(np.int8)
            samples_interleaved[1::2] = np.clip(np.imag(samples * 128), -128, 127).astype(np.int8)
            payload = samples_interleaved.tobytes()
        elif bit_depth == 12:
            # 12-bit signed samples, pack two 12-bit samples into 3 bytes
            i_samples = np.clip(np.real(samples * 2048), -2048, 2047).astype(np.int16)
            q_samples = np.clip(np.imag(samples * 2048), -2048, 2047).astype(np.int16)
            samples_interleaved = np.empty((samples_per_packet * 2,), dtype=np.int16)
            samples_interleaved[0::2] = i_samples
            samples_interleaved[1::2] = q_samples
            packed = bytearray()
            for i in range(0, len(samples_interleaved), 2):
                s1 = samples_interleaved[i] & 0xFFF  # 12 bits
                s2 = samples_interleaved[i + 1] & 0xFFF
                packed.append((s1 >> 4) & 0xFF)
                packed.append(((s1 & 0xF) << 4) | ((s2 >> 8) & 0xF))
                packed.append(s2 & 0xFF)
            payload = bytes(packed)
        elif bit_depth == 16:
            samples_interleaved = np.empty((samples_per_packet * 2,), dtype=np.int16)
            samples_interleaved[0::2] = np.clip(np.real(samples * 32768), -32768, 32767).astype(np.int16)
            samples_interleaved[1::2] = np.clip(np.imag(samples * 32768), -32768, 32767).astype(np.int16)
            payload = samples_interleaved.tobytes()
        else:
            raise ValueError(f"Unsupported bit_depth: {bit_depth}")
        data["header"]["seqNum"] = seq_num
        data["header"]["pktSize"] = 7 + (len(payload) + 3) // 4  # Update pktSize based on payload length
        print(data["header"]["pktSize"]) # TEMPORARY
        data["payload"] = payload
        pkt = difi_data_definition.build(data)
        send_packet(sock, addr, pkt)
        seq_num = (seq_num + 1) % 16  # wrap seq_num for demo
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send DIFI packets over UDP")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="Destination IP address")
    parser.add_argument("--port", type=int, default=50003, help="Destination UDP port")
    parser.add_argument("--sample-rate", type=float, default=100e3, help="Sample rate (Hz)")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration to send packets (seconds)")
    parser.add_argument("--packet-size", type=str, default="small", choices=["small", "large"], help="Packet size (small or large)")
    parser.add_argument("--bit-depth", type=int, default=8, choices=[8, 12, 16], help="Bit depth for IQ samples (8, 12, or 16)")
    parser.add_argument("--company", type=str, default="Fillmein", help="Company name")
    parser.add_argument("--product-name", type=str, default="Fillmein", help="Product name")
    parser.add_argument("--product-version", type=str, default="0.0", help="Product version")
    args = parser.parse_args()

    if args.packet_size == "small":
        packet_size_words = 360
    elif args.packet_size == "large":
        packet_size_words = 2232
    else:
        raise ValueError("Invalid packet size")
    samples_per_packet = int(((packet_size_words - 7) * 4) / (args.bit_depth / 8.0 * 2))
    print(f"samples_per_packet: {samples_per_packet}")

    if samples_per_packet > len(tx_samples) * 2:
        raise ValueError(f"samples_per_packet {samples_per_packet} exceeds available samples {len(tx_samples)}")

    addr = (args.ip, args.port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    threads = [
        threading.Thread(target=context_sender, args=(sock, addr, args.bit_depth), daemon=True),
        threading.Thread(target=version_sender, args=(sock, addr), daemon=True),
        threading.Thread(target=data_sender, args=(sock, addr, args.sample_rate, samples_per_packet, args.bit_depth), daemon=True),
    ]
    for t in threads:
        t.start()
    print(f"Sending packets to {addr}. Press Ctrl+C to stop.")
    try:
        start_time = time.time()
        while True:
            time.sleep(0.1)
            if time.time() - start_time > args.duration:
                break
    except KeyboardInterrupt:
        print("\nStopped.")

    output_yaml_dict["company"] = args.company
    output_yaml_dict["product_name"] = args.product_name
    output_yaml_dict["product_version"] = args.product_version
    output_yaml_dict["bit_depth"] = args.bit_depth
    output_yaml_dict["sample_rate_hz"] = args.sample_rate
    output_yaml_dict["samples_per_packet"] = samples_per_packet
    timestamp_str = strftime("%Y%m%d_%H%M%S")
    output_yaml_filename = f"certify_sink_summary_{timestamp_str}.yaml"
    with open(output_yaml_filename, "w") as f:
        yaml.dump(output_yaml_dict, f)
