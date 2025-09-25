from construct import Struct, BitStruct, BitsInteger, Int16ub, Int32ub, Int64ub, Int64sb, Int16sb, ExprAdapter, ExprSymmetricAdapter, obj_, Enum
from scapy.all import PcapReader, UDP

pcap_file = "../examples/Example1_1Msps_8bits.pcapng"

def Int64ubScaled():
    return ExprAdapter(Int64ub, lambda obj, ctx: obj / 2.0 ** 20, lambda obj, ctx: int(obj * 2.0 ** 20))

def Int64sbScaled():
    return ExprAdapter(Int64sb, lambda obj, ctx: obj / 2.0 ** 20, lambda obj, ctx: int(obj * 2.0 ** 20))

def Int16sbScaled():
    return ExprAdapter(Int16sb, lambda obj, ctx: obj / 2.0 ** 7, lambda obj, ctx: int(obj * 2.0 ** 7))

# This is aliased so that it 1) shows up yellow instead of green, and 2) shorter and more concise code
def Bits(N):
    return BitsInteger(N)

DIFIContext = Struct(
    "header" / BitStruct(
        "pktType" / Bits(4),      # bits 28-31
        "classId" / Bits(1),      # bit 27
        "reserved" / Bits(2),     # bits 25-26
        "tsm" / Bits(1),          # bit 24 
        "tsi" / Enum(Bits(2), NOTALLOWED=0, UTC=1, GPS=2, POSIX=3), # bits 22-23
        "tsf" / Bits(2),          # bits 20-21
        "seqNum" / Bits(4),       # bits 16-19
        "pktSize" / Bits(16),     # bits 0-15
    ),
    "streamId" / Int32ub,
    "classId" / BitStruct(
        "paddingBits" / Bits(5),      # bits 27-31
        "reserved1" / Bits(3),        # bits 24-26
        "oui" / Bits(24),             # bits 0-23
        "infoClassCode" / Bits(16),   # bits 16-31
        "packetClassCode" / Bits(16), # bits 0-15
    ),
    "intSecsTimestamp" / Int32ub,
    "fracSecsTimestamp" / Int64ub,
    "cif0" / Int32ub,
    "refPoint" / Int32ub,
    "bandwidth" / Int64ubScaled(),
    "ifFreq" / Int64sbScaled(),
    "rfFreq" / Int64sbScaled(),
    "ifBandOffset" / Int64sbScaled(),
    "refLevel1" / Int16sbScaled(),
    "refLevel2" / Int16sbScaled(),
    "stage1GainAtten" / Int16sbScaled(),
    "stage2GainAtten" / Int16sbScaled(),
    "sampleRate" / Int64ubScaled(),
    "timeStampAdj" / Int64sb,
    "timeStampCal" / Int32ub,
    "stateEventInd" / BitStruct( # 1 word TODO make sure these are in the right order
        "calibrated_time_indicator" / Bits(1),
        "valid_data_indicator" / Bits(1),
        "reference_lock_indicator" / Bits(1),
        "agc_mgc_indicator" / Bits(1),
        "detected_signal_indicator" / Bits(1),
        "spectral_inversion_indicator" / Bits(1),
        "over_range_indicator" / Bits(1),
        "sample_loss_indicator" / Bits(1),
    ),
    "dataPacketFormat" / BitStruct( # 2 words TODO make sure these are in the right order
        "packing_method" / Bits(1),
        "real_complex_type" / Bits(2),
        "data_item_format" / Bits(5),
        "sample_component_repeat_indicator" / Bits(1),
        "event_tag_size" / Bits(3),
        "channel_tag_size" / Bits(4),
        "data_item_fraction_size" / Bits(4),
        "item_packing_field_size" / Bits(6),
        "data_item_size" / Bits(6),
        "repeat_count" / Bits(16),
        "vector_size" / Bits(16)
    )
)

# example of how to build a packet, type bytes
if False:
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

else:
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
