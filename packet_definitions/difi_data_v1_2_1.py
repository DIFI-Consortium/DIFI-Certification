from construct import Struct, BitStruct, Enum, GreedyBytes
from .construct_custom_types import *

'''
DIFI v1.2.1 Data Packets cover two Packet Classes:
  0x0000 - Standard Flow Signal Data (TSF = 0x2, Real Time picoseconds)
  0x0002 - Sample Count Signal Flow Data (TSF = 0x1, Sample Count)

Packet structure is identical between the two; only the TSF code (and the
interpretation of the fractional-seconds timestamp) differs. Bit-padding
rules also differ depending on Information Class (see spec Table 4-12).
'''

difi_data_definition = Struct(
    "header" / BitStruct( # 1 word
        "pktType"  / Bits(4),
        "classId"  / Bits(1),
        "reserved" / Bits(2), # Trailer Indicator + VITA 49.0 Indicator, both 0
        "tsm"      / Bits(1), # Spectrum/Time, must be 0 for time data
        "tsi"      / Enum(Bits(2), not_allowed=0, UTC=1, GPS=2, POSIX=3),
        "tsf"      / Bits(2), # 0x2 for class 0x0000, 0x1 for class 0x0002
        "seqNum"   / Bits(4),
        "pktSize"  / Bits(16)),
    "streamId" / UnsignedInt32(),
    "classId" / BitStruct( # 2 words
        "paddingBits"     / Bits(5),
        "reserved1"       / Bits(3),
        "oui"             / Bits(24),
        "infoClassCode"   / Bits(16),
        "packetClassCode" / Bits(16)),
    "intSecsTimestamp"  / UnsignedInt32(),
    "fracSecsTimestamp" / UnsignedInt64(),
    "payload" / GreedyBytes)


def validate(packet):
    errors = []
    if packet.header.pktType != 0x1: errors.append("Not a signal data packet (pktType must be 0x1)")
    if packet.header.classId != 1: errors.append("Class ID must be 1")
    if packet.header.reserved != 0: errors.append("Reserved bits (Trailer + V49.0) must be 0")
    if packet.header.tsm != 0: errors.append("Spectrum/Time bit (TSM) must be 0 for time data")
    if packet.header.tsi == "not_allowed": errors.append("TSI must not be 0")
    if packet.classId.oui != 0x6A621E: errors.append("OUI is invalid, expecting 0x6A621E")
    pkt_class = packet.classId.packetClassCode
    if pkt_class not in (0x0000, 0x0002):
        errors.append(f"Packet Class Code 0x{pkt_class:04X} not a valid v1.2.1 data class (expected 0x0000 or 0x0002)")
    if pkt_class == 0x0000 and packet.header.tsf != 2:
        errors.append("Packet Class 0x0000 requires TSF=0x2 (Real Time picoseconds)")
    if pkt_class == 0x0002 and packet.header.tsf != 1:
        errors.append("Packet Class 0x0002 requires TSF=0x1 (Sample Count)")
    info_class = packet.classId.infoClassCode
    if info_class not in (0x0000, 0x0002, 0x0003, 0x0004):
        errors.append(f"Information Class 0x{info_class:04X} not a valid v1.2.1 class for data packets")
    if info_class == 0x0000 and pkt_class != 0x0000:
        errors.append("Information Class 0x0000 must use Packet Class 0x0000")
    if info_class == 0x0002 and pkt_class != 0x0002:
        errors.append("Information Class 0x0002 must use Packet Class 0x0002")
    if info_class == 0x0003 and pkt_class != 0x0000:
        errors.append("Information Class 0x0003 must use Packet Class 0x0000")
    if info_class == 0x0004 and pkt_class != 0x0002:
        errors.append("Information Class 0x0004 must use Packet Class 0x0002")
    if info_class == 0x0000 and pkt_class == 0x0000 and packet.classId.paddingBits != 0:
        errors.append("Bit padding not permitted for Class 0x0000 in Information Class 0x0000")
    return errors

difi_data_definition.validate = validate
