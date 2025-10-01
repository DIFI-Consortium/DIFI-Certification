from construct import Struct, BitStruct, Enum
from scapy.all import PcapReader, UDP
from construct_custom_types import *
from difi_constants import *

# Notes on endianness and order of fields within Construct-
#   - DIFI wireshark dissector uses big-endian
#   - currently I'm using big-endian with construct
#   - the order of fields within 1 word seem to be reverse of what the DIFI spec shows
#   - eg packet size is bits 0-15 in the spec
#   - so it seems like BitStruct is defined with most significant bits first

DIFIContext = Struct(
    "header" / BitStruct( # 1 word
        "pktType"  / Bits(4),
        "classId"  / Bits(1),
        "reserved" / Bits(2),
        "tsm"      / Bits(1),
        "tsi"      / Enum(Bits(2), NOTALLOWED=0, UTC=1, GPS=2, POSIX=3),
        "tsf"      / Bits(2),
        "seqNum"   / Bits(4),
        "pktSize"  / Bits(16)), # bits 0-15 (order is reversed in BitStruct)
    "streamId" / UnsignedInt32(),
    "classId" / BitStruct( # 1 word
        "paddingBits"     / Bits(5),
        "reserved1"       / Bits(3),
        "oui"             / Bits(24),
        "infoClassCode"   / Bits(16),
        "packetClassCode" / Bits(16)),
    "intSecsTimestamp"  / UnsignedInt32(),
    "fracSecsTimestamp" / UnsignedInt64(),
    "cif0"              / UnsignedInt32(),
    "refPoint"          / UnsignedInt32(),
    "bandwidth"         / UnsignedInt64Scaled(),
    "ifFreq"            / SignedInt64Scaled(),
    "rfFreq"            / SignedInt64Scaled(),
    "ifBandOffset"      / SignedInt64Scaled(),
    "refLevel1"         / SignedInt16Scaled(),
    "refLevel2"         / SignedInt16Scaled(),
    "stage1GainAtten"   / SignedInt16Scaled(),
    "stage2GainAtten"   / SignedInt16Scaled(),
    "sampleRate"        / UnsignedInt64Scaled(),
    "timeStampAdj"      / SignedInt64(),
    "timeStampCal"      / UnsignedInt32(),
    "stateEventInd" / BitStruct( # 1 word
        "misc_enables"                 / Bits(8),
        "reserved"                     / Bits(4),
        "calibrated_time_indicator"    / Bits(1),
        "valid_data_indicator"         / Bits(1),
        "reference_lock_indicator"     / Bits(1),
        "agc_mgc_indicator"            / Bits(1),
        "detected_signal_indicator"    / Bits(1),
        "spectral_inversion_indicator" / Bits(1),
        "over_range_indicator"         / Bits(1),
        "sample_loss_indicator"        / Bits(1),
        "reserved2"                    / Bits(4),
        "user_defined"                 / Bits(8)),
    "dataPacketFormat" / BitStruct( # 2 words
        "packing_method"          / Enum(Bits(1), processing_efficient=0, link_efficient=1),
        "real_complex_type"       / Enum(Bits(2), real=0, complex_cartesian=1, complex_polar=2, reserved=3),
        "data_item_format"        / Enum(Bits(5), signed_fixed_point=0),
        "sample_repeat_indicator" / Enum(Bits(1), no_repeat=0, yes_repeat=1),
        "event_tag_size"          / Bits(3), # 0 for no event tags
        "channel_tag_size"        / Bits(4), # 0 for no channel tags
        "data_item_fraction_size" / Bits(4),
        "item_packing_field_size" / Bits(6),
        "data_item_size"          / Bits(6),
        "repeat_count"            / Bits(16),  # 2nd word, bits 16-31
        "vector_size"             / Bits(16))) # 2nd word, bits 0-15
if DIFIContext.sizeof() != 108: raise Exception("Bug in Construct definition of DIFIContext, it should be 108 bytes")

# Example of parsing a packet
pcap_file = "../examples/Example1_1Msps_8bits.pcapng"
for packet in PcapReader(pcap_file):
    data = bytes(packet[UDP].payload)
    packet_type = data[0:4][0] >> 4
    if packet_type == 0x4:
        print("Found first context packet")
        break
# print(data)
if len(data) != DIFIContext.sizeof(): raise Exception(f"Packet size {len(data)} does not match expected size {DIFIContext.sizeof()}")
parsed = DIFIContext.parse(data)
for key, value in parsed.items():
    print(f"{key}: {value}")

# Validations
if parsed.header.pktType != 0x4: raise Exception("Not a standard flow signal context packet")
if parsed.header.pktSize != 27: raise Exception("Packet size is not 27 words")
if parsed.header.classId != 1: raise Exception("Class ID must be 1 for standard flow signal context")
if parsed.header.reserved != 0: raise Exception("Reserved bits must be 0")
if parsed.header.tsm != 1: raise Exception("TSM must be 1")
if parsed.header.tsf != 2: raise Exception("TSF must be 2")
if parsed.cif0 != 0xFBB98000: raise Exception(f"Nonstandard CIF0, it was {parsed.cif0:X}")
if parsed.dataPacketFormat.real_complex_type != "complex_cartesian": raise Exception(f"Bad real_complex_type, value was {parsed.dataPacketFormat.real_complex_type}")
if parsed.dataPacketFormat.data_item_format != "signed_fixed_point": raise Exception(f"Bad data_item_format, value was {parsed.dataPacketFormat.data_item_format}")
if parsed.dataPacketFormat.sample_repeat_indicator != "no_repeat": raise Exception(f"Bad sample_repeat_indicator, value was {parsed.dataPacketFormat.sample_repeat_indicator}")
if parsed.dataPacketFormat.event_tag_size != 0: raise Exception(f"Bad event_tag_size, value was {parsed.dataPacketFormat.event_tag_size}")
if parsed.dataPacketFormat.channel_tag_size != 0: raise Exception(f"Bad channel_tag_size, value was {parsed.dataPacketFormat.channel_tag_size}")
print("All validations passed")
