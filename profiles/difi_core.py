from packet_definitions.construct_custom_types import *

# Profile-specific Validations (keep DIFI version agnostic wherever possible)

# Put any header-specific checks in the context category
def validate_profile_context(profile, parsed):
    errors = []
    if parsed.sampleRate != 20e6: errors.append("Sample rate doesnt match profile")
    if parsed.dataPacketFormat.data_item_size != 7: errors.append("Was not 8-bit data_item_size")
    if parsed.header.pktSize != 360: errors.append("Expected pktSize=360")
    return errors

def validate_profile_data(profile, parsed):
    return []

def validate_profile_version(profile, parsed):
    return []

def validate_profile_command(profile, parsed):
    return []
