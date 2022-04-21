# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

import dcs
import sys
import pytest


def test_invalid_dcs(ipaddress):
    try:
        dcs.DESTINATION_IP = ipaddress
        dcs.DESTINATION_PORT = 4991
        dcs.STREAM_ID = 4
        dcs.FIELDS["--bandwidth"] = "2.0"
        dcs.FIELDS["--cif0"] = "22221111"
        dcs.send_difi_compliant_standard_context_packet()
    except Exception as e:
        assert 0
        print(e)


def test_valid_dcs(ipaddress):
    try:
        dcs.DESTINATION_IP = ipaddress
        dcs.DESTINATION_PORT = 4991
        dcs.STREAM_ID = 5
        dcs.FIELDS["--bandwidth"] = "2.0"
        dcs.FIELDS["--cif0"] = "0BB98000"
        dcs.send_difi_compliant_standard_context_packet()
    except Exception as e:
        assert 0
        print(e)
