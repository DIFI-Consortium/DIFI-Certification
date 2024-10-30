from datetime import timezone, datetime
import struct
from io import BytesIO
import json

from difi_utils.difi_constants import *
from difi_utils.custom_error_types import *

##############################
# standard context packet class - object that is filled from the decoded standard context packet stream
##############################

DEBUG = False

class DifiStandardContextPacket():
    """
    DIFI Context Packet.
      -Standard Flow Signal Context Packet

    :param stream: raw data stream of bytes to decode
    """

    def __init__(self, stream: BytesIO):

        ##############################
        # decode 32bit header (4 bytes)
        ##############################
        hdrbuf = stream.read1(4)
        if not hdrbuf:
            return
        (hdr,) = struct.unpack(">I", hdrbuf)

        self.pkt_type = (hdr >> 28) & 0x0f     #(bit 28-31)
        self.class_id = (hdr >> 27) & 0x01     #(bit 27)
        self.reserved = (hdr >> 25) & 0x03     #(bit 25-26)
        self.tsm = (hdr >> 24) & 0x01          #(bit 24)
        self.tsi = (hdr >> 22) & 0x03          #(bit 22-23)
        self.tsf = (hdr >> 20) & 0x03          #(bit 20-21)
        self.seq_num = (hdr >> 16) & 0x0f      #(bit 16-19) #mod16 of pkt count (seqnum in difi spec)
        self.pkt_size = (hdr >> 0) & 0xffff    #(bit 0-15) #num 32bit words in pkt

        ##############################
        # decode stream id (4 bytes)
        ##############################
        idbuf = stream.read1(4)
        (value,) = struct.unpack(">I", idbuf)
        self.stream_id = value
        stream.seek(4) #backup to 4 to re-include stream id in data for decoding below

        if DEBUG: print("")
        if DEBUG: print("---")
        if DEBUG: print("DifiStandardContextPacket header data in constructor:")
        if DEBUG: print("Header: %s" % (hdrbuf.hex()))
        if DEBUG: print("Header: %d" % (int.from_bytes(hdrbuf, byteorder='big', signed=False)))
        if DEBUG: print(f"Header: {(int.from_bytes(hdrbuf, byteorder='big', signed=False)):032b}")
        if DEBUG: print("stream id: 0x%08x" % (self.stream_id))
        if DEBUG: print("pkt type: 0x%01x" % (self.pkt_type))
        if DEBUG: print("classid: 0x%01x" % (self.class_id))
        if DEBUG: print("reserved: 0x%01x" % (self.reserved))
        if DEBUG: print("tsm: 0x%01x" % (self.tsm))
        if DEBUG: print("tsi: 0x%01x" % (self.tsi))
        if DEBUG: print("tsf: 0x%01x" % (self.tsf))
        if DEBUG: print("pkt count (mod16): %d" % (self.seq_num))  #packet_count
        if DEBUG: print("pkt size: %d" % (self.pkt_size)) #packet_size
        if DEBUG: print("---")

        #only allow if standard context packet type
        if self.pkt_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT:

            #only decode if header is valid
            if self.is_difi10_standard_context_packet_header(self.pkt_type, self.pkt_size, self.class_id, self.reserved, self.tsm, self.tsf):
                packet_size_in_bytes = (self.pkt_size - 1) * 4  #less header (-1)
                context_data = stream.read1(packet_size_in_bytes)
                self._decode_standard_flow_signal_context(context_data)
            else:
                raise NoncompliantDifiPacket("non-compliant DIFI standard context packet header [packet type: 0x%1x]" % self.pkt_type, DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))
        else:
            raise NoncompliantDifiPacket("non-compliant packet type [0x%1x] for DIFI standard context packet  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (self.pkt_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))


    #function to decode standard context packet
    def _decode_standard_flow_signal_context(self, data):

        if DEBUG: print("Decoding.....")
        #print(data.hex())

        try:
            #only fully decode if DIFI compliant
            #  -check Context Indicator Field
            #  -check Data Payload Format Fields
            (cif,) = struct.unpack(">I", data[24:28])
            cif = (cif & 0x0FFFFFFF)
            (value1,value2) = struct.unpack(">II", data[96:104])
            data_payload_fmt_pk_mh = (value1 >> 31) & 0x01  #bit31
            data_payload_fmt_real_cmp_type = (value1 >> 29) & 0x03  #bit29-30
            data_payload_fmt_data_item_fmt = (value1 >> 24) & 0x1F  #bit24-28
            data_payload_fmt_rpt_ind = (value1 >> 23) & 0x01  #bit23
            data_payload_fmt_event_tag_size = (value1 >> 20) & 0x07  #bit20-22
            data_payload_fmt_channel_tag_size = (value1 >> 16) & 0x0F  #bit16-19
            if not self.is_difi10_standard_context_packet(cif, data_payload_fmt_pk_mh, data_payload_fmt_real_cmp_type, data_payload_fmt_data_item_fmt, data_payload_fmt_rpt_ind, data_payload_fmt_event_tag_size, data_payload_fmt_channel_tag_size):
                raise NoncompliantDifiPacket("non-compliant DIFI standard context packet.", DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf, cif0=cif, data_payload_fmt_pk_mh=data_payload_fmt_pk_mh, data_payload_fmt_real_cmp_type=data_payload_fmt_real_cmp_type, data_payload_fmt_data_item_fmt=data_payload_fmt_data_item_fmt, data_payload_fmt_rpt_ind=data_payload_fmt_rpt_ind, data_payload_fmt_event_tag_size=data_payload_fmt_event_tag_size, data_payload_fmt_channel_tag_size=data_payload_fmt_channel_tag_size))


            #######################
            # Stream ID (5.1.2)
            #######################
            if DEBUG: print(data[0:4].hex())
            #already unpacked in constructor __init__
            #(value,) = struct.unpack(">I", data[0:4])
            #if DEBUG: print(" Stream ID = 0x%08x (ID)" % (value))
            #self.stream_id = value
            if DEBUG: print(" Stream ID = 0x%08x (ID)" % (self.stream_id))

            ##########################
            # OUI (5.1.3)
            ##########################
            if DEBUG: print(data[4:8].hex())
            #h = b'\x00\x7C\x38\x6C'
            #h = b'\x00\x00\x12\xa2'
            (value,) = struct.unpack(">I", data[4:8])
            value = value & 0x00FFFFFF
            if DEBUG: print(" OUI = 0x%06x" % (value))
            self.oui = value

            #########################
            # Information Class Code / Packet Class Code (5.1.3)
            ########################
            if DEBUG: print(data[8:12].hex())
            #h = b'\x00\x00\x00\x80'
            #h = b'\x00\x00\xff\x80'
            #h = b'\x00\x00\x00\x01'
            #h = b'\x00\x00\xff\xff'
            (icc,pcc) = struct.unpack(">HH", data[8:12])
            if DEBUG: print(" Information Class Code = 0x%04x - Packet Class Code = 0x%04x" % (icc, pcc))
            self.information_class_code = icc
            self.packet_class_code = pcc

            #######################
            # Integer-seconds Timestamp (5.1.4 and 5.1.5)
            #######################
            if DEBUG: print(data[12:16].hex())
            (value,) = struct.unpack(">I", data[12:16])
            if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).isoformat()))
            #if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).isoformat()))
            self.integer_seconds_timestamp = value
            self.integer_seconds_timestamp_display = datetime.fromtimestamp(value, tz=timezone.utc).isoformat()

            #######################
            # Fractional-seconds Timestamp (5.1.4 and 5.1.5)
            #######################
            if DEBUG: print(data[16:24].hex())
            (value,) = struct.unpack(">Q", data[16:24])
            if DEBUG: print(" Fractional-seconds Timestamp (picoseconds past integer seconds) = %d" % (value))
            self.fractional_seconds_timestamp = value

            #######################
            # Context Indicator Field(CIF 0) (9)
            #######################
            if DEBUG: print(data[24:28].hex())
            (value,) = struct.unpack(">I", data[24:28])
            if DEBUG: print(" Context Indicator Field (CIF 0) = 0x%08x" % (value))
            self.context_indicator_field_cif0 = value

            #######################
            # Reference Point (9.2)
            #######################
            if DEBUG: print(data[28:32].hex())
            (value,) = struct.unpack(">I", data[28:32])
            if DEBUG: print(" Reference Point = 0x%08x (ID)" % (value))
            self.ref_point = value

            ###################
            # Bandwidth (9.5.1)
            ###################
            if DEBUG: print(data[32:40].hex())
            #h = b'\x00\x00\x00\x00\x00\x10\x00\x00'
            #h = b'\x00\x00\x00\x00\x00\x00\x00\x01'
            (value,) = struct.unpack(">Q", data[32:40])
            value /= 2.0 ** 20
            if DEBUG: print(" Bandwidth = %.8f (Hertz)" % value)
            self.bandwidth = value

            ################################
            # IF Reference Frequency (9.5.5)
            ################################
            if DEBUG: print(data[40:48].hex())
            #h = b'\x00\x00\x00\x00\x00\x10\x00\x00'
            #h = b'\xff\xff\xff\xff\xff\xf0\x00\x00'
            #h = b'\x00\x00\x00\x00\x00\x00\x00\x01'
            #h = b'\xff\xff\xff\xff\xff\xff\xff\xff'
            (value,) = struct.unpack(">q", data[40:48])
            value /= 2.0 ** 20
            if DEBUG: print(" IF Reference Frequency = %.8f (Hertz)" % (value))
            self.if_ref_freq = value

            #################################
            # RF Reference Frequency (9.5.10)
            #################################
            if DEBUG: print(data[48:56].hex())
            #h = b'\x00\x00\x00\x00\x00\x10\x00\x00'
            #h = b'\xff\xff\xff\xff\xff\xf0\x00\x00'
            #h = b'\x00\x00\x00\x00\x00\x00\x00\x01'
            #h = b'\xff\xff\xff\xff\xff\xff\xff\xff'
            (value,) = struct.unpack(">q", data[48:56])
            value /= 2.0 ** 20
            if DEBUG: print(" RF Reference Frequency = %.8f (Hertz)" % (value))
            self.rf_ref_freq = value

            ########################
            # IF Band Offset (9.5.4)
            #######################
            if DEBUG: print(data[56:64].hex())
            #h = b'\x00\x00\x00\x00\x00\x10\x00\x00'
            #h = b'\xff\xff\xff\xff\xff\xf0\x00\x00'
            #h = b'\x00\x00\x00\x00\x00\x00\x00\x01'
            #h = b'\xff\xff\xff\xff\xff\xff\xff\xff'
            (value,) = struct.unpack(">q", data[56:64])
            value /= 2.0 ** 20
            if DEBUG: print(" IF Band Offset = %.8f (Hertz)" % (value))
            self.if_band_offset = value

            #########################
            # Reference Level (9.5.9)
            ########################
            if DEBUG: print(data[64:68].hex())
            #h = b'\x00\x00\x00\x80'
            #h = b'\x00\x00\xff\x80'
            #h = b'\x00\x00\x00\x01'
            #h = b'\x00\x00\xff\xff'
            (r1,value) = struct.unpack(">hh", data[64:68])  # pylint: disable=unused-variable
            value /= 2.0 ** 7
            if DEBUG: print(" Reference Level = %.8f (dBm)" % (value))
            self.ref_level = value

            ##########################
            # Gain/Attenuation (9.5.3)
            ##########################
            if DEBUG: print(data[68:72].hex())
            #h = b'\x00\x80\x00\x80'
            #h = b'\xff\x80\xff\x80'
            #h = b'\x00\x01\x00\x01'
            #h = b'\xff\xff\xff\xff'
            (g2,g1) = struct.unpack(">hh", data[68:72])
            g2 /= 2.0 ** 7
            g1 /= 2.0 ** 7
            if DEBUG: print(" Stage1 Gain/Attenuation = %.8f (dB)" % (g1))
            if DEBUG: print(" Stage2 Gain/Attenuation = %.8f (dB)" % (g2))
            self.gain_attenuation = (g2, g1)

            ######################
            # Sample Rate (9.5.12)
            ######################
            if DEBUG: print(data[72:80].hex())
            #h = b'\x00\x00\x00\x00\x00\x10\x00\x00'
            #h = b'\x00\x00\x00\x00\x00\x00\x00\x01'
            (value,) = struct.unpack(">Q", data[72:80])
            value /= 2.0 ** 20
            if DEBUG: print(" Sample Rate = %.8f (Hertz)" % (value))
            self.sample_rate = value

            ############################################
            # Timestamp Adjustment (9.7.3.1)(rule 9.7-1)(9.7-2)
            ############################################
            if DEBUG: print(data[80:88].hex())
            (value,) = struct.unpack(">q", data[80:88])
            if DEBUG: print(" Timestamp Adjustment = %d (femtoseconds)" % (value))
            self.timestamp_adjustment = value

            ######################################
            # Timestamp Calibration Time (9.7.3.3)
            ######################################
            if DEBUG: print(data[88:92].hex())
            #h = b'\xff\xff\xff\xff'
            (value,) = struct.unpack(">I", data[88:92])
            if DEBUG: print(" Timestamp Calibration Time = %d (seconds)" % (value))
            self.timestamp_calibration_time = value

            #####################################
            # State and Event Indicators (9.10.8)
            #####################################
            #bit17 - Reference Lock Indicator
            #bit19 - Calibrated Time Indicator
            if DEBUG: print(data[92:96].hex())
            #h = b'\x00\x0A\x00\x00'
            (value,) = struct.unpack(">I", data[92:96])
            if DEBUG: print(" State and Event Indicators = %d" % (value))
            self.state_and_event_indicators = {
                    "raw_value" : value
                    ,"calibrated_time_indicator" : (value >> 19) & 0x01  #bit19
                    ,"valid_data_indicator" : (value >> 18) & 0x01  #bit18
                    ,"reference_lock_indicator" : (value >> 17) & 0x01  #bit17
                    ,"agc_mgc_indicator" : (value >> 16) & 0x01  #bit16
                    ,"detected_signal_indicator" : (value >> 15) & 0x01  #bit15
                    ,"spectral_inversion_indicator" : (value >> 14) & 0x01  #bit14
                    ,"over_range_indicator" : (value >> 13) & 0x01  #bit13
                    ,"sample_loss_indicator" : (value >> 12) & 0x01  #bit12
                    }
            if DEBUG: print("   Calibrated Time Indicator (bit 19) = %d" % (self.state_and_event_indicators["calibrated_time_indicator"]))
            if DEBUG: print("   Valid Data Indicator (bit 18) = %d" % (self.state_and_event_indicators["valid_data_indicator"]))
            if DEBUG: print("   Reference Lock Indicator (bit 17) = %d" % (self.state_and_event_indicators["reference_lock_indicator"]))
            if DEBUG: print("   AGC/MGC Indicator (bit 16) = %d" % (self.state_and_event_indicators["agc_mgc_indicator"]))
            if DEBUG: print("   Detected Signal Indicator (bit 15) = %d" % (self.state_and_event_indicators["detected_signal_indicator"]))
            if DEBUG: print("   Spectral Inversion Indicator (bit 14) = %d" % (self.state_and_event_indicators["spectral_inversion_indicator"]))
            if DEBUG: print("   Over-range Indicator (bit 13) = %d" % (self.state_and_event_indicators["over_range_indicator"]))
            if DEBUG: print("   Sample Loss Indicator (bit 12) = %d" % (self.state_and_event_indicators["sample_loss_indicator"]))

            #####################################
            # Data Packet Payload Format (9.13.3)(Figure B-37)
            #####################################
            if DEBUG: print(data[96:104].hex())
            #h = b'\x00\x00\x07\xDF\x00\x00\x00\x00'
            #h = b'\x00\x20\x02\x47\x00\x00\x00\x00'
            (value1,value2) = struct.unpack(">II", data[96:104])
            if DEBUG: print(" Data Packet Payload Format = %d (word1), %d (word2)" % (value1, value2))
            self.data_packet_payload_format = {
                    "raw_value_word1" : value1
                    ,"raw_value_word2" : value2
                    #--------
                    ,"packing_method" : (value1 >> 31) & 0x01  #bit31
                    ,"real_complex_type" : (value1 >> 29) & 0x03  #bit29-30
                    ,"data_item_format" : (value1 >> 24) & 0x1F  #bit24-28
                    ,"sample_component_repeat_indicator" : (value1 >> 23) & 0x01  #bit23
                    ,"event_tag_size" : (value1 >> 20) & 0x07  #bit20-22
                    ,"channel_tag_size" : (value1 >> 16) & 0x0F  #bit16-19
                    ,"data_item_fraction_size" : (value1 >> 12) & 0x0F  #bit12-15
                    ,"item_packing_field_size" : (value1 >> 6) & 0x3F  #bit6-11
                    ,"data_item_size" : (value1 >> 0) & 0x3F  #bit0-5
                    #--------
                    ,"repeat_count" : (value2 >> 16) & 0xFFFF  #bit16-31
                    ,"vector_size" : (value2 >> 0) & 0xFFFF  #bit0-15
                    }
            if DEBUG: print("   Packing Method (bit 31) = %d" % (self.data_packet_payload_format["packing_method"]))
            if DEBUG: print("   Real/Complex Type (bit 29-30) = %d" % (self.data_packet_payload_format["real_complex_type"]))
            if DEBUG: print("   Data Item Format (bit 24-28) = %d" % (self.data_packet_payload_format["data_item_format"]))
            if DEBUG: print("   Sample-Component Repeat Indicator (bit 23) = %d" % (self.data_packet_payload_format["sample_component_repeat_indicator"]))
            if DEBUG: print("   Event-Tag Size (bit 20-22) = %d" % (self.data_packet_payload_format["event_tag_size"]))
            if DEBUG: print("   Channel-Tag Size (bit 16-19) = %d" % (self.data_packet_payload_format["channel_tag_size"]))
            if DEBUG: print("   Data Item Fraction Size (bit 12-15) = %d" % (self.data_packet_payload_format["data_item_fraction_size"]))
            if DEBUG: print("   Item Packing Field Size (bit 6-11) = %d" % (self.data_packet_payload_format["item_packing_field_size"]))
            if DEBUG: print("   Data Item Size (bit 0-5) = %d" % (self.data_packet_payload_format["data_item_size"]))
            #--------
            if DEBUG: print("   Repeat Count (bit 16-31) = %d" % (self.data_packet_payload_format["repeat_count"]))
            if DEBUG: print("   Vector Size (bit 0-15) = %d" % (self.data_packet_payload_format["vector_size"]))

            #bit layout (value1 and value2)
            #[31]     Packing Method (1)
            #[30..29] Real/Complex Type (2)
            #[28..24] Data Item Format (5)
            #[23]     Sample-Component Repeat Indicator (1)
            #[22..20] Event-Tag Size (3)
            #[19..16] Channel-Tag Size (4)
            #[15..12] Data Item Fraction Size (4)
            #[11..6]  Item Packing Field Size (6)
            #[5..0]   Data Item Size (6)
            #--------
            #[31..16] Repeat Count (16)
            #[15..0]  Vector Size (16)
            #
            #
            #difi spec says only supports:
            #  complex Cartesian samples (I and Q)
            #  link-efficient packing
            #  signed fixed-point
            #  no event or channel tags
            #  sample sizes from 4 through 16 bits without sample component repeats and no unused bits
            #
            #"Packing Method" = 1 (for link-efficient packing)
            #  0 processing-efficient packing
            #  1 link-efficient packing
            #"Real/Complex Type" = 01 (for complex cartesian)
            #  00 Real
            #  01 Complex, Cartesian
            #  10 Complex, Polar
            #  11 Reserved
            #"Data Item Format" = 00000 (for signed fixed-point)
            #  00000 Signed Fixed-Point
            #  10000 Unsigned Fixed-Point
            #"Sample-Component Repeat Indicator" = 0 (for without sample component repeats)
            #  0 no Sample Component Repeating
            #  1 Sample Component Repeating
            #"Event-Tag Size" = 0 (for no event tag)
            #"Channel-Tag Size" = 0 (for no channel tag)

        except NoncompliantDifiPacket as e:
            raise e
        except Exception as e:
            raise e

        if DEBUG: print("Finished decoding.\r\n---\r\n")

        #debug
        #print("JSON dump object 'DifiStandardContextPacket'-standard flow:\r\n\r\n", self.to_json())
        #print("String dump object 'DifiStandardContextPacket'-standard flow:\r\n", str(self))


    #json encoder to change applicable int's to hex string
    class StandardContextPacketHexJSONEncoder(json.JSONEncoder):

        def encode(self, o):
            d = o.copy()
            if type(d["pkt_type"]) is int:
                d.update(pkt_type = "0x%1x" % d["pkt_type"])
            if type(d["class_id"]) is int:
                d.update(class_id = "0x%1x" % d["class_id"])
            if type(d["reserved"]) is int:
                d.update(reserved = "0x%1x" % d["reserved"])
            if type(d["tsm"]) is int:
                d.update(tsm = "0x%1x" % d["tsm"])
            if type(d["tsi"]) is int:
                d.update(tsi = "0x%1x" % d["tsi"])
            if type(d["tsf"]) is int:
                d.update(tsf = "0x%1x" % d["tsf"])
            if type(d["stream_id"]) is int:
                d.update(stream_id = "0x%08x" % d["stream_id"])
            if type(d["oui"]) is int:
                d.update(oui = "0x%06x" % d["oui"])
            if type(d["information_class_code"]) is int:
                d.update(information_class_code = "0x%04x" % d["information_class_code"])
            if type(d["packet_class_code"]) is int:
                d.update(packet_class_code = "0x%04x" % d["packet_class_code"])
            if type(d["context_indicator_field_cif0"]) is int:
                d.update(context_indicator_field_cif0 = "0x%08x" % d["context_indicator_field_cif0"])
            if type(d["ref_point"]) is int:
                d.update(ref_point = "0x%08x" % d["ref_point"])

            return json.JSONEncoder.encode(self, d)


    def to_json(self, hex_values=False):
        #s = json.dumps(self, default=vars, indent=4)
        #s = json.loads(zlib.decompress(data))
        if hex_values is True:
            return json.dumps(self.__dict__, indent=4, cls=self.StandardContextPacketHexJSONEncoder)
        else:
            return json.dumps(self, default=lambda o: o.__dict__, indent=4)


    def __str__(self):

        return ("Stream ID: 0x%08x (ID)\r\n\
OUI: 0x%06x\r\n\
Information Class Code: 0x%04x\r\n\
Packet Class Code: 0x%04x\r\n\
Integer-seconds Timestamp (seconds since epoch): %d (%s)\r\n\
Fractional-seconds Timestamp (picoseconds past integer-seconds): %d\r\n\
Context Indicator Field (CIF 0): 0x%08x\r\n\
Reference Point: 0x%08x (ID)\r\n\
Bandwidth: %.8f (Hertz)\r\n\
IF Reference Frequency: %.8f (Hertz)\r\n\
RF Reference Frequency: %.8f (Hertz)\r\n\
IF Band Offset: %.8f (Hertz)\r\n\
Reference Level: %.8f (dBm)\r\n\
Stage1 Gain/Attenuation: %.8f (dB)\r\n\
Stage2 Gain/Attenuation: %.8f (dB)\r\n\
Sample Rate: %.8f (Hertz)\r\n\
Timestamp Adjustment: %d (femtoseconds)\r\n\
Timestamp Calibration Time: %d (seconds)\r\n\
State and Event Indicators: %d\r\n\
  Calibrated Time Indicator (bit 19): %d\r\n\
  Valid Data Indicator (bit 18): %d\r\n\
  Reference Lock Indicator (bit 17): %d\r\n\
  AGC/MGC Indicator (bit 16): %d\r\n\
  Detected Signal Indicator (bit 15): %d\r\n\
  Spectral Inversion Indicator (bit 14): %d\r\n\
  Over-range Indicator (bit 13): %d\r\n\
  Sample Loss Indicator (bit 12): %d\r\n\
Data Packet Payload Format: %d (word1), %d (word2)\r\n\
  Packing Method (bit 31): %d\r\n\
  Real/Complex Type (bit 29-30): %d\r\n\
  Data Item Format (bit 24-28): %d\r\n\
  Sample-Component Repeat Indicator (bit 23): %d\r\n\
  Event-Tag Size (bit 20-22): %d\r\n\
  Channel-Tag Size (bit 16-19): %d\r\n\
  Data Item Fraction Size (bit 12-15): %d\r\n\
  Item Packing Field Size (bit 6-11): %d\r\n\
  Data Item Size (bit 0-5): %d\r\n\
  --------\r\n\
  Repeat Count (bit 16-31): %d\r\n\
  Vector Size (bit 0-15): %d\r\n\
" % (self.stream_id,
    self.oui,
    self.information_class_code,
    self.packet_class_code,
    self.integer_seconds_timestamp,
    datetime.fromtimestamp(self.integer_seconds_timestamp, tz=timezone.utc).isoformat(),
    self.fractional_seconds_timestamp,
    self.context_indicator_field_cif0,
    self.ref_point,
    self.bandwidth,
    self.if_ref_freq,
    self.rf_ref_freq,
    self.if_band_offset,
    self.ref_level,
    self.gain_attenuation[1],
    self.gain_attenuation[0],
    self.sample_rate,
    self.timestamp_adjustment,
    self.timestamp_calibration_time,
    self.state_and_event_indicators["raw_value"],
    self.state_and_event_indicators["calibrated_time_indicator"],
    self.state_and_event_indicators["valid_data_indicator"],
    self.state_and_event_indicators["reference_lock_indicator"],
    self.state_and_event_indicators["agc_mgc_indicator"],
    self.state_and_event_indicators["detected_signal_indicator"],
    self.state_and_event_indicators["spectral_inversion_indicator"],
    self.state_and_event_indicators["over_range_indicator"],
    self.state_and_event_indicators["sample_loss_indicator"],
    self.data_packet_payload_format["raw_value_word1"],
    self.data_packet_payload_format["raw_value_word2"],
    self.data_packet_payload_format["packing_method"],
    self.data_packet_payload_format["real_complex_type"],
    self.data_packet_payload_format["data_item_format"],
    self.data_packet_payload_format["sample_component_repeat_indicator"],
    self.data_packet_payload_format["event_tag_size"],
    self.data_packet_payload_format["channel_tag_size"],
    self.data_packet_payload_format["data_item_fraction_size"],
    self.data_packet_payload_format["item_packing_field_size"],
    self.data_packet_payload_format["data_item_size"],
    self.data_packet_payload_format["repeat_count"],
    self.data_packet_payload_format["vector_size"]))


    ##############################
    # DIFI packet validation checks
    ##############################

    #standard context packet header
    def is_difi10_standard_context_packet_header(self, packet_type, packet_size, class_id, rsvd, tsm, tsf):
        return (packet_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT
            and packet_size == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT_SIZE
            and class_id == DIFI_CLASSID
            and rsvd == DIFI_RESERVED
            and tsm == DIFI_TSM_GENERAL_TIMING
            and tsf == DIFI_TSF_REALTIME_PICOSECONDS)

    #standard context packet
    def is_difi10_standard_context_packet(self, cif, data_payload_fmt_pk_mh, data_payload_fmt_real_cmp_type, data_payload_fmt_data_item_fmt, data_payload_fmt_rpt_ind, data_payload_fmt_event_tag_size, data_payload_fmt_channel_tag_size):
        return (data_payload_fmt_pk_mh == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_PACKING_METHOD
            #and cif == DIFI_CONTEXT_INDICATOR_FIELD_STANDARD_FLOW_CONTEXT
            and data_payload_fmt_real_cmp_type == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_REAL_COMPLEX_TYPE
            and data_payload_fmt_data_item_fmt == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_DATA_ITEM_FORMAT
            and data_payload_fmt_rpt_ind == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_SAMPLE_COMPONENT_REPEAT_IND
            and data_payload_fmt_event_tag_size == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_EVENT_TAG_SIZE
            and data_payload_fmt_channel_tag_size == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_CHANNEL_TAG_SIZE)


