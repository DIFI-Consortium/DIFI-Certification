import struct
from io import BytesIO
import json

from difi_utils.difi_constants import *
from difi_utils.custom_error_types import *

##############################
# context packet class used for legacy DIFI devices such as the kratos narrowband digitizer, its only 72 bytes instead of 108
##############################

class DifiStandardContextPacket():
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
        self.pkt_size = (hdr >> 0) & 0xffff    #(bit 0-15) #num 32bit words in pkt - should be 0x12 (18 in dec)

        ##############################
        # decode stream id (4 bytes)
        ##############################
        idbuf = stream.read1(4)
        (value,) = struct.unpack(">I", idbuf)
        self.stream_id = value
        stream.seek(4) #backup to 4 to re-include stream id in data for decoding below

        #only allow if standard context packet type
        if self.pkt_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT:

            #only decode if header is valid
            if self.is_difi10_standard_context_packet_header(self.pkt_type, self.pkt_size, self.class_id, self.reserved, self.tsm, self.tsf):
                packet_size_in_bytes = (self.pkt_size - 1) * 4  # pkt_size is in "words" (4-byte groups). subtract header
                context_data = stream.read1(packet_size_in_bytes)
                self._decode_standard_flow_signal_context(context_data)
            else:
                raise NoncompliantDifiPacket("non-compliant DIFI standard context packet header [packet type: 0x%1x]" % self.pkt_type, DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))
        else:
            raise NoncompliantDifiPacket("non-compliant packet type [0x%1x] for DIFI standard context packet  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (self.pkt_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))


    #function to decode standard context packet
    def _decode_standard_flow_signal_context(self, data):
        try:
            # at this point, the first 4 bytes of data are the streamid

            (cif,) = struct.unpack(">I", data[12:16])
            cif = (cif & 0x0FFFFFFF)
            (value1, value2) = struct.unpack(">II", data[60:68]) # Data packet payload format (8 bytes)
            data_payload_fmt_pk_mh = (value1 >> 31) & 0x01  #bit31
            data_payload_fmt_real_cmp_type = (value1 >> 29) & 0x03  #bit29-30
            data_payload_fmt_data_item_fmt = (value1 >> 24) & 0x1F  #bit24-28
            data_payload_fmt_rpt_ind = (value1 >> 23) & 0x01  #bit23
            data_payload_fmt_event_tag_size = (value1 >> 20) & 0x07  #bit20-22
            data_payload_fmt_channel_tag_size = (value1 >> 16) & 0x0F  #bit16-19

            #only fully decode if DIFI compliant
            if not self.is_difi10_standard_context_packet(cif, data_payload_fmt_pk_mh, data_payload_fmt_real_cmp_type, data_payload_fmt_data_item_fmt, data_payload_fmt_rpt_ind, data_payload_fmt_event_tag_size, data_payload_fmt_channel_tag_size):
                raise NoncompliantDifiPacket("non-compliant DIFI standard context packet.", DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf, cif0=cif, data_payload_fmt_pk_mh=data_payload_fmt_pk_mh, data_payload_fmt_real_cmp_type=data_payload_fmt_real_cmp_type, data_payload_fmt_data_item_fmt=data_payload_fmt_data_item_fmt, data_payload_fmt_rpt_ind=data_payload_fmt_rpt_ind, data_payload_fmt_event_tag_size=data_payload_fmt_event_tag_size, data_payload_fmt_channel_tag_size=data_payload_fmt_channel_tag_size))

            ##########################
            # OUI
            ##########################
            (value,) = struct.unpack(">I", data[4:8])
            value = value & 0x00FFFFFF
            self.oui = value

            #########################
            # Information Class Code / Packet Class Code
            ########################
            (icc,pcc) = struct.unpack(">HH", data[8:12])
            self.information_class_code = icc
            self.packet_class_code = pcc

            #######################
            # Context Indicator Field(CIF 0)
            #######################
            (value,) = struct.unpack(">I", data[12:16])
            self.context_indicator_field_cif0 = value

            ###################
            # Bandwidth
            ###################
            (value,) = struct.unpack(">Q", data[16:24])
            value /= 2.0 ** 20
            self.bandwidth = value

            ################################
            # IF Reference Frequency
            ################################
            (value,) = struct.unpack(">q", data[24:32])
            value /= 2.0 ** 20
            self.if_ref_freq = value

            #################################
            # RF Reference Frequency
            #################################
            (value,) = struct.unpack(">q", data[32:40])
            value /= 2.0 ** 20
            self.rf_ref_freq = value

            #########################
            # Not sure if this is Reference Level or Gain or IF band offset, but it seems to be 0's for the examples anyway
            ########################
            # ??? = struct.unpack(">hh", data[40:48])

            ######################
            # Sample Rate 
            ######################
            (value,) = struct.unpack(">Q", data[48:56])
            value /= 2.0 ** 20
            self.sample_rate = value

            #####################################
            # State and Event Indicators 
            #####################################
            (value,) = struct.unpack(">I", data[56:60])
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

            #####################################
            # Data Packet Payload Format
            #####################################
            (value1,value2) = struct.unpack(">II", data[60:68])
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

        except NoncompliantDifiPacket as e:
            raise e
        except Exception as e:
            raise e

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


    ##############################
    # DIFI packet validation checks
    ##############################

    #standard context packet header
    def is_difi10_standard_context_packet_header(self, packet_type, packet_size, class_id, rsvd, tsm, tsf):
        return (packet_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT
            and packet_size == 18
            and class_id == DIFI_CLASSID
            and rsvd == DIFI_RESERVED
            and tsm == DIFI_TSM_GENERAL_TIMING
            and tsf == DIFI_TSF_REALTIME_PICOSECONDS)

    #standard context packet
    def is_difi10_standard_context_packet(self, cif, data_payload_fmt_pk_mh, data_payload_fmt_real_cmp_type, data_payload_fmt_data_item_fmt, data_payload_fmt_rpt_ind, data_payload_fmt_event_tag_size, data_payload_fmt_channel_tag_size):
        return (data_payload_fmt_pk_mh == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_PACKING_METHOD
            and cif == 0x39a18000
            and data_payload_fmt_real_cmp_type == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_REAL_COMPLEX_TYPE
            and data_payload_fmt_data_item_fmt == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_DATA_ITEM_FORMAT
            and data_payload_fmt_rpt_ind == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_SAMPLE_COMPONENT_REPEAT_IND
            and data_payload_fmt_event_tag_size == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_EVENT_TAG_SIZE
            and data_payload_fmt_channel_tag_size == DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_CHANNEL_TAG_SIZE)


