from difi_context_v1_1 import difi_context_definition
from difi_data_v1_1 import difi_data_definition
from difi_version_v1_1 import difi_version_definition


# Prototype Context packet
context = {
    "header": {
        "pktType": 4,
        "classId": 1,
        "reserved": 0,
        "tsm": 1,
        "tsi": "POSIX",
        "tsf": 2,
        "seqNum": 14,
        "pktSize": 27,
    },
    "streamId": 0,
    "classId": {
        "paddingBits": 0,
        "reserved1": 0,
        "oui": 6971934,
        "infoClassCode": 0,
        "packetClassCode": 1,
    },
    "intSecsTimestamp": 1740688471,
    "fracSecsTimestamp": 200000000000,
    "cif0": 4223238144,
    "refPoint": 100,
    "bandwidth": 800000.0,
    "ifFreq": 0.0,
    "rfFreq": 1950000000.0,
    "ifBandOffset": 0.0,
    "refLevel1": 0.0,
    "refLevel2": 0.0,
    "stage1GainAtten": 0.0,
    "stage2GainAtten": -13.25,
    "sampleRate": 1000000.0,
    "timeStampAdj": 0,
    "timeStampCal": 0,
    "stateEventInd": {
        "misc_enables": 160,
        "reserved": 0,
        "calibrated_time_indicator": 0,
        "valid_data_indicator": 0,
        "reference_lock_indicator": 1,
        "agc_mgc_indicator": 0,
        "detected_signal_indicator": 0,
        "spectral_inversion_indicator": 0,
        "over_range_indicator": 0,
        "sample_loss_indicator": 0,
        "reserved2": 0,
        "user_defined": 0,
    },
    "dataPacketFormat": {
        "packing_method": "link_efficient",
        "real_complex_type": "complex_cartesian",
        "data_item_format": "signed_fixed_point",
        "sample_repeat_indicator": "no_repeat",
        "event_tag_size": 0,
        "channel_tag_size": 0,
        "data_item_fraction_size": 0,
        "item_packing_field_size": 7,
        "data_item_size": 7,
        "repeat_count": 0,
        "vector_size": 0,
    },
}
context_packet = difi_context_definition.build(context)

# Prototype Data packet
data = {
    "header": {
        "pktType": 1,
        "classId": 1,
        "reserved": 0,
        "tsm": 0,
        "tsi": "POSIX",
        "tsf": 2,
        "seqNum": 15,
        "pktSize": 367,
    },
    "streamId": 0,
    "classId": {
        "paddingBits": 0,
        "reserved1": 0,
        "oui": 6971934,
        "infoClassCode": 0,
        "packetClassCode": 0,
    },
    "intSecsTimestamp": 1740688471,
    "fracSecsTimestamp": 106369572000,
    "payload": b'\xf3\x1c\xf2\x19\xf8\x11\n\x10\x1c\x0c\x1d\x04\x0c\x0e\xfa\x1f',
}
data_packet = difi_data_definition.build(data)

# Prototype Version packet
version = {
    "header": {
        "pktType": 5,
        "classId": 1,
        "reserved": 0,
        "tsm": 1,
        "tsi": "POSIX",
        "tsf": 2,
        "seqNum": 13,
        "pktSize": 11,
    },
    "streamId": 0,
    "classId": {
        "paddingBits": 0,
        "reserved1": 0,
        "oui": 6971934,
        "infoClassCode": 1,
        "packetClassCode": 4,
    },
    "intSecsTimestamp": 1740688471,
    "fracSecsTimestamp": 500000000000,
    "cif0": "no_change",
    "cif1": 12,
    "v49SpecVersion": 4,
    "versionInfo": {
        "year": 2025,
        "day": 49,
        "revision": 1,
        "type": 0,
        "icdVersion": 0,
    },
}
version_packet = difi_version_definition.build(version)

