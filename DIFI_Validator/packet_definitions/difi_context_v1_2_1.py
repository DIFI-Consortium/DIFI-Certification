from construct import Struct, BitStruct, Enum
from construct_custom_types import *

'''
New in v1.2.1 there are now 3 different classes of context packets and the version packet is now a subset of this context packet instead of its own thing
(see packetClassCode field) within the Context Packet Type (0x4):
  0x1, Standard Flow Signal Context
  0x3, Sample Count Signal Flow Context
  0x4, Version Flow Signal Context

0x1 and 0x3 have the same packet structure, there's just a couple fields that are interpreted differently
0x4 has an entirely different packet structure
So we'll have a separate Construct definition (and thus file) for version, and this one will be 0x1 and 0x3
'''

# Used for 0x1 and 0x3 packetClassCode, see difi_version_v1_2_1.py for the 0x4 (version) packet
difi_context_definition = Struct(
    "header" / BitStruct( # 1 word
        "pktType"  / Bits(4),
        "classId"  / Bits(1),
        "reserved" / Bits(2),
        "tsm"      / Bits(1), # for 0x1, 0->fine and 1->coarse. For 0x3 it's always 0
        "tsi"      / Enum(Bits(2), not_allowed=0, UTC=1, GPS=2, POSIX=3),
        "tsf"      / Bits(2), # for 0x1, it should be set to 2 representing picoseconds.  for 0x3 it should be set to 1 representing sample count
        "seqNum"   / Bits(4),
        "pktSize"  / Bits(16)), # bits 0-15 (order is reversed in BitStruct)
    "streamId" / UnsignedInt32(),
    "classId" / BitStruct( # 2 words
        "paddingBits"     / Bits(5),
        "reserved1"       / Bits(3),
        "oui"             / Bits(24), # called CID now? value 0x6A621E
        "infoClassCode"   / Bits(16),
        "packetClassCode" / Bits(16)), # where we find out whether it's a 0x1 or 0x3
    "intSecsTimestamp"  / UnsignedInt32(),
    "fracSecsTimestamp" / UnsignedInt64(), # for packetClassCode 0x3 it's sample count, for 0x1 it's picoseconds
    "cif0"              / Enum(UnsignedInt32(), context_changed=0xFBB98000, no_change=0x7BB98000),
    "refPoint"          / Enum(UnsignedInt32(), IF=100, RF=75, antenna=25, air=15),
    "bandwidth"         / UnsignedInt64Scaled(),
    "ifFreq"            / SignedInt64Scaled(), # for non-IF systems set to 0
    "rfFreq"            / SignedInt64Scaled(),
    "ifBandOffset"      / SignedInt64Scaled(), # for non-IF systems set to 0
    "refLevel"          / SignedInt16Scaled(), # TODO: make sure this and the next field arent in the wrong order
    "scalingLevel"      / SignedInt16Scaled(),
    "gain1"             / SignedInt16Scaled(), # set to 0x0, use refLevel instead
    "gain2"             / SignedInt16Scaled(), # set to 0x0, use refLevel instead
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
        "data_item_size"          / Bits(6),   # unsigned number that is one less than the actual Data Item size, so usually 7 or 15
        "repeat_count"            / Bits(16),  # 2nd word, bits 16-31
        "vector_size"             / Bits(16))) # 2nd word, bits 0-15


# Validations
def validate(packet):
    errors = []
    ''' Need an example pcap before filling these out
    if packet.header.pktType != 0x4: errors.append("Not a standard flow signal context packet")
    if packet.header.pktSize != 27: errors.append("Packet size is not 27 words")
    if packet.header.classId != 1: errors.append("Class ID must be 1 for standard flow signal context")
    if packet.header.reserved != 0: errors.append("Reserved bits must be 0")
    if packet.header.tsm != 1: errors.append("TSM must be 1")
    if packet.header.tsf != 2: errors.append("TSF must be 2")
    if packet.cif0 != 0xFBB98000: errors.append(f"Nonstandard CIF0, it was {packet.cif0:X}")
    if packet.dataPacketFormat.real_complex_type != "complex_cartesian": errors.append(f"Bad real_complex_type, value was {packet.dataPacketFormat.real_complex_type}")
    if packet.dataPacketFormat.data_item_format != "signed_fixed_point": errors.append(f"Bad data_item_format, value was {packet.dataPacketFormat.data_item_format}")
    if packet.dataPacketFormat.sample_repeat_indicator != "no_repeat": errors.append(f"Bad sample_repeat_indicator, value was {packet.dataPacketFormat.sample_repeat_indicator}")
    if packet.dataPacketFormat.event_tag_size != 0: errors.append(f"Bad event_tag_size, value was {packet.dataPacketFormat.event_tag_size}")
    if packet.dataPacketFormat.channel_tag_size != 0: errors.append(f"Bad channel_tag_size, value was {packet.dataPacketFormat.channel_tag_size}")
    '''
    return errors
difi_context_definition.validate = validate # so it can be called as difi_context.validate(packet)
