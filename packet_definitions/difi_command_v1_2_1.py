from construct import Struct, BitStruct, Enum
from .construct_custom_types import *

'''
DIFI v1.2.1 Command Packet — Timing Flow Control. Two Packet Classes:
  0x0005 - Sample Count Timing Flow Control (TSF = 0x1, Sample Count)
  0x0006 - Real Time TSF Timing Flow Control (TSF = 0x2, Real Time picoseconds)

Both classes share the same 21-word structure; only the TSF code differs.
'''

difi_command_definition = Struct(
    "header" / BitStruct( # 1 word
        "pktType"  / Bits(4),
        "classId"  / Bits(1),
        "ctrlAck"  / Bits(3), # bits 26-24, 0x0 for Control (not cancellation)
        "tsi"      / Enum(Bits(2), not_allowed=0, UTC=1, GPS=2, POSIX=3),
        "tsf"      / Bits(2),
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
    "cam" / BitStruct( # 1 word - Control/Acknowledge Mode
        "controlleeIdInd"   / Bits(1), # bit 31 - 1 = include Controllee ID
        "controlleeIdFmt"   / Bits(1), # bit 30 - 0 = 32-bit
        "controllerIdInd"   / Bits(1), # bit 29 - 1 = include Controller ID
        "controllerIdFmt"   / Bits(1), # bit 28 - 0 = 32-bit
        "partialPacketImpl" / Bits(1), # bit 27 - 0 (unused)
        "warnings"          / Bits(1), # bit 26 - 0 (unused)
        "errors"            / Bits(1), # bit 25 - 0 (unused)
        "actionMode"        / Bits(2), # bits 24-23, 10 = execute
        "nack"              / Bits(1), # bit 22
        "validityAck"       / Bits(1), # bit 21
        "reserved22_15"     / Bits(6), # bits 20-15 reserved
        "tsCtrlMode"        / Bits(3), # bits 14-12 - timestamp control mode
        "ackBits"           / Bits(4), # bits 11-8 - 0 for control packet only
        "reserved7_0"       / Bits(8)),# bits 7-0 reserved
    "messageId"     / UnsignedInt32(), # word 9
    "controlleeId"  / UnsignedInt32(), # word 10
    "controllerId"  / UnsignedInt32(), # word 11
    "cif0"          / UnsignedInt32(), # word 12
    "cif1"          / UnsignedInt32(), # word 13
    "refPoint"      / Enum(UnsignedInt32(), IF=100, RF=75, antenna=25, air=15), # word 14
    "sampleRate"    / UnsignedInt64Scaled(),                                     # words 15-16
    "timeStampAdj"  / SignedInt64(),                                             # words 17-18 (femtoseconds)
    "bufferSize"    / UnsignedInt64(),                                           # words 19-20 (bytes)
    "bufferStatus" / BitStruct( # word 21
        "reserved"       / Bits(16), # bits 31-16
        "bufferLevel"    / Bits(8),  # bits 15-8 (top 8 bits of 12-bit fill)
        "bufferLevelLow" / Bits(4),  # bits 7-4 (low 4 bits extending fill to 12 bits)
        "overflow"       / Bits(1),  # bit 3
        "nearlyFull"     / Bits(1),  # bit 2
        "nearlyEmpty"    / Bits(1),  # bit 1
        "underflow"      / Bits(1))) # bit 0


def validate(packet):
    errors = []
    if packet.header.pktType != 0x6: errors.append("Not a command packet (pktType must be 0x6)")
    if packet.header.classId != 1: errors.append("Class ID must be 1")
    if packet.header.ctrlAck != 0: errors.append("Control/Ack bits must be 0x0 for Control (no cancellation)")
    if packet.header.tsi == "not_allowed": errors.append("TSI must not be 0")
    if packet.header.pktSize != 21: errors.append("Packet size must be 21 words")
    if packet.classId.paddingBits != 0: errors.append("Padding bits must be 0")
    if packet.classId.oui != 0x6A621E: errors.append("OUI is invalid, expecting 0x6A621E")
    pkt_class = packet.classId.packetClassCode
    if pkt_class not in (0x0005, 0x0006):
        errors.append(f"Packet Class Code 0x{pkt_class:04X} not a valid v1.2.1 command class (expected 0x0005 or 0x0006)")
    if pkt_class == 0x0005 and packet.header.tsf != 1:
        errors.append("Packet Class 0x0005 requires TSF=0x1 (Sample Count)")
    if pkt_class == 0x0006 and packet.header.tsf != 2:
        errors.append("Packet Class 0x0006 requires TSF=0x2 (Real Time picoseconds)")
    info_class = packet.classId.infoClassCode
    if info_class not in (0x0002, 0x0003):
        errors.append(f"Information Class 0x{info_class:04X} not valid for command packets (expected 0x0002 or 0x0003)")
    if info_class == 0x0002 and pkt_class != 0x0005:
        errors.append("Information Class 0x0002 must use Packet Class 0x0005")
    if info_class == 0x0003 and pkt_class != 0x0006:
        errors.append("Information Class 0x0003 must use Packet Class 0x0006")
    # CAM field expectations for Timing Flow Control Control Packets
    if packet.cam.controlleeIdInd != 1: errors.append("CAM: Controllee ID Indicator must be 1")
    if packet.cam.controlleeIdFmt != 0: errors.append("CAM: Controllee ID Format must be 0 (32-bit)")
    if packet.cam.controllerIdInd != 1: errors.append("CAM: Controller ID Indicator must be 1")
    if packet.cam.controllerIdFmt != 0: errors.append("CAM: Controller ID Format must be 0 (32-bit)")
    if packet.cam.actionMode != 0b10: errors.append(f"CAM: Action Mode must be 0b10 (execute), was 0b{packet.cam.actionMode:02b}")
    if packet.cam.ackBits != 0: errors.append("CAM: Acknowledge bits must be 0 for Control packets")
    # CIF 0 must indicate: bit 30 (RefPoint), bit 21 (Sample Rate), bit 20 (Timestamp Adj), bit 1 (CIF1 present)
    expected_cif0_bits = (1 << 30) | (1 << 21) | (1 << 20) | (1 << 1)
    if (packet.cif0 & expected_cif0_bits) != expected_cif0_bits:
        errors.append(f"CIF0 0x{packet.cif0:08X} missing required bits (RefPoint/SampleRate/TS-Adj/CIF1)")
    # CIF 1 should indicate Buffer Size present (bit 1)
    if (packet.cif1 & 0x2) == 0:
        errors.append(f"CIF1 0x{packet.cif1:08X} must have Buffer Size present bit set")
    if packet.refPoint not in ("IF", "RF", "antenna", "air"):
        errors.append(f"Reference Point must be 100 (IF), 75 (RF), 25 (antenna), or 15 (air); was {packet.refPoint}")
    return errors

difi_command_definition.validate = validate
