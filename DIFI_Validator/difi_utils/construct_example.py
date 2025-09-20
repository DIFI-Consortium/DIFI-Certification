from construct import Struct, BitStruct, BitsInteger, Int16ub, Int32ub, Int64ub, Int64sb, Int16sb, ExprAdapter, ExprSymmetricAdapter, obj_
from scapy.all import PcapReader, UDP

pcap_file = "../examples/Example1_1Msps_8bits.pcapng"

def Int64ubScaled():
    return ExprAdapter(Int64ub, lambda obj, ctx: obj / 2.0 ** 20, lambda obj, ctx: int(obj * 2.0 ** 20))

def Int64sbScaled():
    return ExprAdapter(Int64sb, lambda obj, ctx: obj / 2.0 ** 20, lambda obj, ctx: int(obj * 2.0 ** 20))

def Int16sbScaled():
    return ExprAdapter(Int16sb, lambda obj, ctx: obj / 2.0 ** 7, lambda obj, ctx: int(obj * 2.0 ** 7))


DIFIContext = Struct(
    "header" / BitStruct(
        "pktType" / BitsInteger(4),      # bits 28-31
        "classId" / BitsInteger(1),      # bit 27
        "reserved" / BitsInteger(2),     # bits 25-26
        "tsm" / BitsInteger(1),          # bit 24
        "tsi" / BitsInteger(2),          # bits 22-23
        "tsf" / BitsInteger(2),          # bits 20-21
        "seqNum" / BitsInteger(4),       # bits 16-19
        "pktSize" / BitsInteger(16),     # bits 0-15
    ),
    "streamId" / Int32ub,
    "classId" / BitStruct(
        "paddingBits" / BitsInteger(5),      # bits 27-31
        "reserved1" / BitsInteger(3),        # bits 24-26
        "oui" / BitsInteger(24),             # bits 0-23
        "infoClassCode" / BitsInteger(16),   # bits 16-31
        "packetClassCode" / BitsInteger(16), # bits 0-15
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
        "calibrated_time_indicator" / BitsInteger(1),
        "valid_data_indicator" / BitsInteger(1),
        "reference_lock_indicator" / BitsInteger(1),
        "agc_mgc_indicator" / BitsInteger(1),
        "detected_signal_indicator" / BitsInteger(1),
        "spectral_inversion_indicator" / BitsInteger(1),
        "over_range_indicator" / BitsInteger(1),
        "sample_loss_indicator" / BitsInteger(1),
    ),
    "dataPacketFormat" / BitStruct( # 2 words TODO make sure these are in the right order
        "packing_method" / BitsInteger(1),
        "real_complex_type" / BitsInteger(2),
        "data_item_format" / BitsInteger(5),
        "sample_component_repeat_indicator" / BitsInteger(1),
        "event_tag_size" / BitsInteger(3),
        "channel_tag_size" / BitsInteger(4),
        "data_item_fraction_size" / BitsInteger(4),
        "item_packing_field_size" / BitsInteger(6),
        "data_item_size" / BitsInteger(6),
        "repeat_count" / BitsInteger(16),
        "vector_size" / BitsInteger(16)
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

parsed = DIFIContext.parse(data)
for key, value in parsed.items():
    print(f"{key}: {value}")
