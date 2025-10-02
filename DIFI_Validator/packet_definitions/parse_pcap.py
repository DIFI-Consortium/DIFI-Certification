from scapy.all import PcapReader, UDP
from difi_context_v1_1 import difi_context_definition
from difi_data_v1_1 import difi_data_definition
from difi_version_v1_1 import difi_version_definition
import numpy as np

# Example of parsing a packet
pcap_file = "../examples/Example1_1Msps_8bits.pcapng"
#bit_depth = None
bit_depth = 8 # for some reason this example pcap only has conext packet after all the data packets
sample_rate = 1
compliant_context_count = 0
noncompliant_context_count = 0
compliant_data_count = 0
noncompliant_data_count = 0
compliant_version_count = 0
noncompliant_version_count = 0
for packet in PcapReader(pcap_file):
    data = bytes(packet[UDP].payload)
    packet_type = data[0:4][0] >> 4

    if packet_type == 0x4:
        print("Found context packet")
        # print(data)
        if len(data) != difi_context_definition.sizeof(): raise Exception(f"Packet size {len(data)} does not match expected size {difi_context_definition.sizeof()}")
        parsed = difi_context_definition.parse(data)
        for key, value in parsed.items():
            print(f"{key}: {value}")

        print("Validating packet...")
        errors = difi_context_definition.validate(parsed)
        if not errors:
            print("All validations passed")
            compliant_context_count += 1
        else:
            print("Validation errors found:")
            noncompliant_context_count += 1
            for error in errors:
                print(f" - {error}")

        bit_depth = parsed.dataPacketFormat.data_item_size + 1 # actual size is one more than the field value
        sample_rate = parsed.sampleRate
        continue

    if packet_type == 0x1 and bit_depth:
        print("Found data packet")
        parsed = difi_data_definition.parse(data)
        for key, value in parsed.items():
            if key != "payload":
                print(f"{key}: {value}")
        
        # Extract samples to numpy array
        if bit_depth == 8:
            num_iq_samples = (parsed.header.pktSize - 7) * 4 // 2 # header is 28 bytes or 7 words, rest is payload. 2 bytes per IQ sample
            samples = np.frombuffer(parsed.payload, dtype=np.int8)
        elif bit_depth == 16:
            num_iq_samples = (parsed.header.pktSize - 7) * 4 // 4
            samples = np.frombuffer(parsed.payload, dtype=np.int16)
        else:
            raise Exception(f"Bit depth of {bit_depth} not supported for sample extraction")
        samples = samples.astype(np.float32)
        samples = samples[::2] + 1j * samples[1::2] # convert to complex64

        if False:
            import matplotlib.pyplot as plt
            plt.figure(0)
            plt.plot(samples.real, label="I")
            plt.plot(samples.imag, label="Q")
            plt.legend()

            plt.figure(1)
            psd = 10 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples)))**2)
            f = np.linspace(-sample_rate/2, sample_rate/2, len(psd))
            plt.plot(f, psd)
            plt.show()
            
        if num_iq_samples != len(samples):
            raise Exception(f"Payload size doesnt match packet size, expected {num_iq_samples} IQ samples but got {len(samples)}")

        print("Validating packet...")
        errors = difi_data_definition.validate(parsed)
        if not errors:
            print("All validations passed")
            compliant_data_count += 1
        else:
            print("Validation errors found:")
            noncompliant_data_count += 1
            for error in errors:
                print(f" - {error}")
        continue
        
    if packet_type == 0x5:
        print("Found version packet (v1.1 only)")
        if len(data) != difi_version_definition.sizeof(): raise Exception(f"Packet size {len(data)} does not match expected size {difi_version_definition.sizeof()}")
        parsed = difi_version_definition.parse(data)
        for key, value in parsed.items():
            print(f"{key}: {value}")

        print("Validating packet...")
        errors = difi_version_definition.validate(parsed)
        if not errors:
            print("All validations passed")
            compliant_version_count += 1
        else:
            print("Validation errors found:")
            noncompliant_version_count += 1
            for error in errors:
                print(f" - {error}")
        continue

print("compliant_context_count:", compliant_context_count)
print("noncompliant_context_count:", noncompliant_context_count)
print("compliant_data_count:", compliant_data_count)
print("noncompliant_data_count:", noncompliant_data_count)
print("compliant_version_count:", compliant_version_count)
print("noncompliant_version_count:", noncompliant_version_count)
