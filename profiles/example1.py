# This is not an official DIFI profile; it's used to test the software, as it is based on the Example1 pcap

# Profile-specific Validations (keep DIFI version agnostic wherever possible)

# Put any header-specific checks in the context category
def validate_profile_context(profile, parsed):
    errors = []
    if parsed.sampleRate != 1e6:
        errors.append("Sample rate doesn't match profile (expected 1e6)")
    return errors


def validate_profile_data(profile, parsed):
    return []


def validate_profile_version(profile, parsed):
    return []


def validate_profile_command(profile, parsed):
    return []
