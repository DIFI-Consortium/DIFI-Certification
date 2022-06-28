# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

import sys
import pytest
import dds

def test_invalid_dcs(ipaddress):
    try:
        dds.DESTINATION_IP = ipaddress
        #"10.247.32.107"
        dds.DESTINATION_PORT = 4991
        dds.STREAM_ID = 14
        dds.FIELDS["--tsf"] = "3"
        dds.FIELDS["--cif0"] = "22221111"
        dds.send_difi_compliant_data_packet()
    except Exception as e:
        assert 0
        print(e)


def test_valid_dcs(ipaddress):
    try:
        dds.DESTINATION_IP = ipaddress
        dds.DESTINATION_PORT = 4991
        dds.STREAM_ID = 15
        dds.FIELDS["--tsf"] = "2"
        dds.FIELDS["--icc"] = "1234"
        dds.send_difi_compliant_data_packet()
    except Exception as e:
        assert 0
        print(e)
