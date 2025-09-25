from construct import Struct, BitStruct, Int32ub, Int64ub, Int64sb, Enum
from scapy.all import PcapReader, UDP
from construct_custom_types import *
from difi_constants import *

DIFIContext = Struct(
    "header" / BitStruct( # 1 word
        "pktType"  / Bits(4),      # bits 28-31
        "classId"  / Bits(1),      # bit 27
        "reserved" / Bits(2),      # bits 25-26
        "tsm"      / Bits(1),      # bit 24 
        "tsi"      / Enum(Bits(2), NOTALLOWED=0, UTC=1, GPS=2, POSIX=3), # bits 22-23
        "tsf"      / Bits(2),      # bits 20-21
        "seqNum"   / Bits(4),      # bits 16-19
        "pktSize"  / Bits(16)),    # bits 0-15
    "streamId" / Int32ub,
    "classId" / BitStruct( # 1 word
        "paddingBits"     / Bits(5),   # bits 27-31
        "reserved1"       / Bits(3),   # bits 24-26
        "oui"             / Bits(24),  # bits 0-23
        "infoClassCode"   / Bits(16),  # bits 16-31
        "packetClassCode" / Bits(16)), # bits 0-15
    "intSecsTimestamp"  / Int32ub,
    "fracSecsTimestamp" / Int64ub,
    "cif0"              / Int32ub,
    "refPoint"          / Int32ub,
    "bandwidth"         / Int64ubScaled(),
    "ifFreq"            / Int64sbScaled(),
    "rfFreq"            / Int64sbScaled(),
    "ifBandOffset"      / Int64sbScaled(),
    "refLevel1"         / Int16sbScaled(),
    "refLevel2"         / Int16sbScaled(),
    "stage1GainAtten"   / Int16sbScaled(),
    "stage2GainAtten"   / Int16sbScaled(),
    "sampleRate"        / Int64ubScaled(),
    "timeStampAdj"      / Int64sb,
    "timeStampCal"      / Int32ub,
    "stateEventInd" / BitStruct( # 1 word
        "calibrated_time_indicator"    / Bits(1),
        "valid_data_indicator"         / Bits(1),
        "reference_lock_indicator"     / Bits(1),
        "agc_mgc_indicator"            / Bits(1),
        "detected_signal_indicator"    / Bits(1),
        "spectral_inversion_indicator" / Bits(1),
        "over_range_indicator"         / Bits(1),
        "sample_loss_indicator"        / Bits(1)),
    "dataPacketFormat" / BitStruct( # 2 words
        "packing_method"          / Enum(Bits(1), processing_efficient=0, link_efficient=1),
        "real_complex_type"       / Enum(Bits(2), real=0, complex_cartesian=1, complex_polar=2, reserved=3),
        "data_item_format"        / Enum(Bits(5), signed_fixed_point=0, unsigned_fixed_point=2),
        "sample_repeat_indicator" / Enum(Bits(1), no_repeat=0, yes_repeat=1),
        "event_tag_size"          / Bits(3), # 0 for no event tags
        "channel_tag_size"        / Bits(4), # 0 for no channel tags
        "data_item_fraction_size" / Bits(4),
        "item_packing_field_size" / Bits(6),
        "data_item_size"          / Bits(6),
        "repeat_count"            / Bits(16),
        "vector_size"             / Bits(16)))

# Example of parsing a packet
pcap_file = "../examples/Example1_1Msps_8bits.pcapng"
for packet in PcapReader(pcap_file):
    data = bytes(packet[UDP].payload)
    packet_type = data[0:4][0] >> 4
    if packet_type == 0x4:
        print("Found first context packet")
        break
print(data)
parsed = DIFIContext.parse(data)
for key, value in parsed.items():
    print(f"{key}: {value}")

# Example of validations
if parsed.header.pktType != 0x4: raise Exception("Not a standard flow signal context packet")
if parsed.header.pktSize != 27: raise Exception("Packet size is not 27 words")
if parsed.header.classId != 1: raise Exception("Class ID must be 1 for standard flow signal context")
if parsed.header.reserved != 0: raise Exception("Reserved bits must be 0")
if parsed.header.tsm != 1: raise Exception("TSM must be 1")
if parsed.header.tsf != 2: raise Exception("TSF must be 2")
if parsed.cif0 != 0xFBB98000: raise Exception(f"Nonstandard CIF0, it was {parsed.cif0:X}")
if parsed.dataPacketFormat.real_complex_type != "real": raise Exception(f"Not a standard flow signal context packet, value was {parsed.dataPacketFormat.real_complex_type}")
if parsed.dataPacketFormat.data_item_format != "unsigned_fixed_point": raise Exception(f"Not a standard flow signal context packet, value was {parsed.dataPacketFormat.data_item_format}")
if parsed.dataPacketFormat.sample_repeat_indicator != "no_repeat": raise Exception(f"Not a standard flow signal context packet, value was {parsed.dataPacketFormat.sample_repeat_indicator}")
if parsed.dataPacketFormat.event_tag_size != 0: raise Exception(f"Not a standard flow signal context packet, value was {parsed.dataPacketFormat.event_tag_size}")
if parsed.dataPacketFormat.channel_tag_size != 0: raise Exception(f"Not a standard flow signal context packet, value was {parsed.dataPacketFormat.channel_tag_size}")


'''
# example of how to build a packet (of type bytes)
data = DIFIContext.build(
    dict(
        header=dict(
            pktType=0x4,
            classId=0x1,
            reserved=0x0,
            tsm=0x1,
            tsi=0x1,
            tsf=0x2,
            seqNum=0,
            pktSize=4,
        ),
        streamId=12345,
        classId=dict(
            paddingBits=0,
            reserved1=0,
            oui=0x000000,
            infoClassCode=0,
            packetClassCode=0,
        ),
        intSecsTimestamp=0,
        fracSecsTimestamp=0,
        cif0=0,
        refPoint=0,
        bandwidth=int(10),
        ifFreq=0,
        rfFreq=0,
        ifBandOffset=0,
        refLevel1=0,
        refLevel2=0,
        stage1GainAtten=0,
        stage2GainAtten=0,
        sampleRate=int(10),
        timeStampAdj=0,
        timeStampCal=0,
        stateEventInd=int(0),
        dataPacketFormat=0,
    )
)
'''