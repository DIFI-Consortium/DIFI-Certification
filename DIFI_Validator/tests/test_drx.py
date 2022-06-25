# Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

import io
import drx

def test_invalid_drx_version_context_packet():
    try:
        drx.DEBUG = False
        drx.VERBOSE = False

        b = bytearray(b'invalid bytes')
        stream = io.BytesIO(b)

        pkt = drx.DifiVersionContextPacket(stream)  #simply feed the byte stream into constructor, that's it.
        assert 1
        print(pkt)
        print(pkt.to_json())
        print(pkt.to_json(hex_values=True))

    except drx.NoncompliantDifiPacket as e:
        print("error: ", e.message)
        print("--> not DIFI compliant, packet not decoded:\r\n%s" % e.difi_info.to_json())
        assert 1
    except Exception as e:
        print("error: ", e)
        assert 0

def test_drx_header_compliant():
    try:
        pkt = drx.DifiVersionContextPacket

        if pkt.is_difi10_version_context_packet_header(pkt,
            packet_type=drx.DIFI_VERSION_FLOW_SIGNAL_CONTEXT,
            class_id=drx.DIFI_CLASSID,
            rsvd=drx.DIFI_RESERVED,
            tsm=drx.DIFI_TSM_GENERAL_TIMING,
            tsf=drx.DIFI_TSF_REALTIME_PICOSECONDS,
            packet_size=drx.DIFI_VERSION_FLOW_SIGNAL_CONTEXT_SIZE) is True:

            print("valid...")
        else:
            print("not valid...")
            assert 0
    except Exception as e:
        print("error: ", e)

def test_drx_packet_compliant():
    try:
        pkt = drx.DifiVersionContextPacket

        if pkt.is_difi10_version_context_packet(pkt,
            icc=drx.DIFI_INFORMATION_CLASS_CODE_VERSION_FLOW_CONTEXT,
            pcc=drx.DIFI_PACKET_CLASS_CODE_VERSION_FLOW_CONTEXT,
            cif0=drx.DIFI_CONTEXT_INDICATOR_FIELD_0_VERSION_FLOW_CONTEXT,
            cif1=drx.DIFI_CONTEXT_INDICATOR_FIELD_1_VERSION_FLOW_CONTEXT,
            v49_spec=drx.DIFI_V49_SPEC_VERSION_VERSION_FLOW_CONTEXT) is True:

            print("valid...")
        else:
            print("not valid...")
            assert 0

    except Exception as e:
        print("error: ", e)
        assert 0
