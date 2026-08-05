# Profile-specific Validations (keep DIFI version agnostic wherever possible)

# Put any header-specific checks in the context category
def validate_profile_context(profile, parsed):
    errors = []
    if parsed.sampleRate != 20e6:
        errors.append("Sample rate doesn't match profile (expected 20e6)")
    if parsed.dataPacketFormat.data_item_size != 7:
        errors.append("Expected data_item_size=7 (8-bit)")
    return errors


def validate_profile_data(profile, parsed):
    errors = []
    if parsed.header.pktSize != 360:
        errors.append("Expected data pktSize=360")
    return errors


def validate_profile_version(profile, parsed):
    return []


def validate_profile_command(profile, parsed):
    return []
