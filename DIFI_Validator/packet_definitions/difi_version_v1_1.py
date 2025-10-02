from construct import Struct, BitStruct, Enum
from construct_custom_types import *

difi_version_definition = Struct(
    "header" / BitStruct( # 1 word
        "pktType"  / Bits(4),
        "classId"  / Bits(1),
        "reserved" / Bits(2),
        "tsm"      / Bits(1),
        "tsi"      / Enum(Bits(2), not_allowed=0, UTC=1, GPS=2, POSIX=3),
        "tsf"      / Bits(2),
        "seqNum"   / Bits(4),
        "pktSize"  / Bits(16)), # bits 0-15 (order is reversed in BitStruct)
    "streamId" / UnsignedInt32(),
    "classId" / BitStruct( # 2 words
        "paddingBits"     / Bits(5),
        "reserved1"       / Bits(3),
        "oui"             / Bits(24),
        "infoClassCode"   / Bits(16),
        "packetClassCode" / Bits(16)),
    "intSecsTimestamp"  / UnsignedInt32(),
    "fracSecsTimestamp" / UnsignedInt64(),
    "cif0"              / Enum(UnsignedInt32(), context_changed=0x80000002, no_change=0x00000002),
    "cif1"              / UnsignedInt32(), # must be 0x0000000C
    "v49SpecVersion"  / UnsignedInt32(), # must be 0x00000004
    "versionInfo" / BitStruct( # 1 word
        "year"       / Bits7Year(),
        "day"        / Bits(9),
        "revision"   / Bits(6),
        "type"       / Bits(4),
        "icdVersion" / Bits(6)))

# Validations
def validate(packet):
    errors = []
    if packet.header.pktType != 0x5: errors.append("Not a standard flow signal data packet")
    if packet.header.classId != 1: errors.append("Class ID must be 1 for standard flow signal context")
    if packet.header.reserved != 0: errors.append("Reserved bits must be 0")
    if packet.header.tsf != 2: errors.append("TSF must be 2")
    if packet.cif0 not in ["context_changed", "no_change"]: errors.append("CIF0 must be 0x80000002 (context_changed) or 0x00000002 (no_change)")
    if packet.cif1 != 0x0000000C: errors.append("CIF1 must be 0x0000000C")
    if packet.v49SpecVersion != 0x00000004: errors.append("V49SpecVersion must be 0x00000004")
    return errors
difi_version_definition.validate = validate
