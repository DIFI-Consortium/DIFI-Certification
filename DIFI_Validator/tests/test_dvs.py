
# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Copyright © `2023` `Microsoft Corporation`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

import sys
import pytest
import dvs

def test_invalid_dvs(ipaddress):
    try:
        dvs.DESTINATION_IP = ipaddress
        dvs.DESTINATION_PORT = 4991
        dvs.STREAM_ID = 12
        dvs.FIELDS["--year"] = "30"
        dvs.FIELDS["--cif1"] = "00000000"
        dvs.send_difi_compliant_version_context_packet()
    except Exception as e:
        assert 0
        print(e)


def test_valid_small_dvs(ipaddress):
    try:
        dvs.DESTINATION_IP = ipaddress
        dvs.DESTINATION_PORT = 4991
        dvs.STREAM_ID = 11
        dvs.FIELDS["--year"] = "32"
        dvs.FIELDS["--tsf"] = "2"
        dvs.send_difi_compliant_version_context_packet()
    except Exception as e:
        assert 0
        print(e)

def test_dvs_all_fields_in_packet(ipaddress):
    try:
        dvs.DESTINATION_IP = ipaddress
        dvs.DESTINATION_PORT = 4991
        dvs.STREAM_ID = 1
        dvs.FIELDS["--pkt-type"] = "5"
        dvs.FIELDS["--clsid"] = "1"
        dvs.FIELDS["--rsvd"] = "0"
        dvs.FIELDS["--tsm"] = "1"
        dvs.FIELDS["--tsi"] = "1"
        dvs.FIELDS["--tsf"] = "2"
        dvs.FIELDS["--seqnum"] = "0"
        dvs.FIELDS["--pkt-size"] = "000b"
        dvs.FIELDS["--oui"] = "0012A2"
        dvs.FIELDS["--icc"] = "0001"
        dvs.FIELDS["--pcc"] = "0004"
        dvs.FIELDS["--integer-seconds-ts"] = "1"
        dvs.FIELDS["--fractional-seconds-ts"] = "1"
        dvs.FIELDS["--cif0"] = "80000002"
        dvs.FIELDS["--cif1"] = "0000000C"
        dvs.FIELDS["--v49-spec-version"] = "00000004"
        dvs.FIELDS["--year"] = "22"
        dvs.FIELDS["--day"] = "1"
        dvs.FIELDS["--revision"] = "0"
        dvs.FIELDS["--type"] = "1"
        dvs.FIELDS["--icd-version"] = "0"
        dvs.send_difi_compliant_version_context_packet()
    except Exception as e:
        print(e)
        assert 0
