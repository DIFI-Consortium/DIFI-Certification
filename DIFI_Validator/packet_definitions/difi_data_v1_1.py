from construct import Struct, BitStruct, Enum, GreedyBytes
from construct_custom_types import *

difi_data_definition = Struct(
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
    "payload" / GreedyBytes)  # Consume all remaining bytes as payload containing samples

# DIFI v1.1 only supports complex signed integers, of 4-16 bit depth, and no unused bits
# For now we'll only support 8 and 16 bit depth when it comes to extracting samples to numpy array

# Validations (note the packet size compared to payload size is validated separately)
def validate(packet):
    errors = []
    if packet.header.pktType != 0x1: errors.append("Not a standard flow signal data packet")
    if packet.header.classId != 1: errors.append("Class ID must be 1 for standard flow signal context")
    if packet.header.reserved != 0: errors.append("Reserved bits must be 0")
    if packet.header.tsf != 2: errors.append("TSF must be 2")
    return errors
difi_data_definition.validate = validate
