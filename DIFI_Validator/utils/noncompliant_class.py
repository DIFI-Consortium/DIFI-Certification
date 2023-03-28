from .difi_constants import *
import json

############
# class used to store non-compliance info for DIFI custom non-compliant exception and to write json object of info out to file
############
class DifiInfo():
    def __init__(self,
                 packet_type:int,
                 stream_id:int=None,
                 packet_size=None,
                 class_id=None,
                 reserved=None,
                 tsm=None,
                 tsf=None,
                 icc=None,
                 pcc=None,
                 cif0=None,
                 cif1=None,
                 v49_spec=None,
                 data_payload_fmt_pk_mh=None,
                 data_payload_fmt_real_cmp_type=None,
                 data_payload_fmt_data_item_fmt=None,
                 data_payload_fmt_rpt_ind=None,
                 data_payload_fmt_event_tag_size=None,
                 data_payload_fmt_channel_tag_size=None):

        #################
        #standard context
        #################
        if packet_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT:
            #stream id
            if stream_id is not None:
                self.stream_id = stream_id
            else:
                self.stream_id = "no-stream-id"
            #header
            self.packet_type = ("0x%1x" % packet_type)
            self.packet_type_display =  (("must be: 0x%1x, 0x%1x, 0x%1x -> was: 0x%1x" % (DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID, packet_type)), True)
            if packet_size is not None: self.packet_size = (("must be: %d -> was: %d" % (DIFI_STANDARD_FLOW_SIGNAL_CONTEXT_SIZE, packet_size)), DIFI_STANDARD_FLOW_SIGNAL_CONTEXT_SIZE==packet_size)
            if class_id is not None: self.class_id = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_CLASSID, class_id)), DIFI_CLASSID==class_id)
            if reserved is not None: self.reserved = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_RESERVED, reserved)), DIFI_RESERVED==reserved)
            if tsm is not None: self.tsm = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSM_GENERAL_TIMING, tsm)), DIFI_TSM_GENERAL_TIMING==tsm)
            if tsf is not None: self.tsf = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSF_REALTIME_PICOSECONDS, tsf)), DIFI_TSF_REALTIME_PICOSECONDS==tsf)
            #packet
            if cif0 is not None: self.context_indicator_field_0 = (("must be: 0x%07x -> was: 0x%07x" % (DIFI_CONTEXT_INDICATOR_FIELD_STANDARD_FLOW_CONTEXT, cif0)), DIFI_CONTEXT_INDICATOR_FIELD_STANDARD_FLOW_CONTEXT==cif0)
            if data_payload_fmt_pk_mh is not None: self.data_packet_payload_format_packing_method = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_PACKING_METHOD, data_payload_fmt_pk_mh)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_PACKING_METHOD==data_payload_fmt_pk_mh)
            if data_payload_fmt_real_cmp_type is not None: self.data_packet_payload_format_real_complex_type = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_REAL_COMPLEX_TYPE, data_payload_fmt_real_cmp_type)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_REAL_COMPLEX_TYPE==data_payload_fmt_real_cmp_type)
            if data_payload_fmt_data_item_fmt is not None: self.data_packet_payload_format_data_item_format = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_DATA_ITEM_FORMAT, data_payload_fmt_data_item_fmt)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_DATA_ITEM_FORMAT==data_payload_fmt_data_item_fmt)
            if data_payload_fmt_rpt_ind is not None: self.data_packet_payload_format_repeat_indicator = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_SAMPLE_COMPONENT_REPEAT_IND, data_payload_fmt_rpt_ind)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_SAMPLE_COMPONENT_REPEAT_IND==data_payload_fmt_rpt_ind)
            if data_payload_fmt_event_tag_size is not None: self.data_packet_payload_format_event_tag_size = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_EVENT_TAG_SIZE, data_payload_fmt_event_tag_size)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_EVENT_TAG_SIZE==data_payload_fmt_event_tag_size)
            if data_payload_fmt_channel_tag_size is not None: self.data_packet_payload_format_channel_tag_size = (("must be: %d -> was: %d" % (DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_CHANNEL_TAG_SIZE, data_payload_fmt_channel_tag_size)), DIFI_DATA_PACKET_PAYLOAD_FORMAT_FIELD_CHANNEL_TAG_SIZE==data_payload_fmt_channel_tag_size)

        ################
        #version context
        ################
        elif packet_type == DIFI_VERSION_FLOW_SIGNAL_CONTEXT:
            #stream id
            if stream_id is not None:
                self.stream_id = stream_id
            else:
                self.stream_id = "no-stream-id"
            #header
            self.packet_type = ("0x%1x" % packet_type)
            self.packet_type_display =  (("must be: 0x%1x, 0x%1x, 0x%1x -> was: 0x%1x" % (DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID, packet_type)), True)
            if packet_size is not None: self.packet_size = (("must be: %d -> was: %d" % (DIFI_VERSION_FLOW_SIGNAL_CONTEXT_SIZE, packet_size)), DIFI_VERSION_FLOW_SIGNAL_CONTEXT_SIZE==packet_size)
            if class_id is not None: self.class_id = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_CLASSID, class_id)), DIFI_CLASSID==class_id)
            if reserved is not None: self.reserved = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_RESERVED, reserved)), DIFI_RESERVED==reserved)
            if tsm is not None: self.tsm = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSM_GENERAL_TIMING, tsm)), DIFI_TSM_GENERAL_TIMING==tsm)
            if tsf is not None: self.tsf = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSF_REALTIME_PICOSECONDS, tsf)), DIFI_TSF_REALTIME_PICOSECONDS==tsf)
            #packet
            if icc is not None: self.information_class_code = (("must be: 0x%04x -> was: 0x%04x" % (DIFI_INFORMATION_CLASS_CODE_VERSION_FLOW_CONTEXT, icc)), DIFI_INFORMATION_CLASS_CODE_VERSION_FLOW_CONTEXT==icc)
            if pcc is not None: self.packet_class_code = (("must be: 0x%04x -> was: 0x%04x" % (DIFI_PACKET_CLASS_CODE_VERSION_FLOW_CONTEXT, pcc)), DIFI_PACKET_CLASS_CODE_VERSION_FLOW_CONTEXT==pcc)
            if cif0 is not None: self.context_indicator_field_0 = (("must be: 0x%07x -> was: 0x%07x" % (DIFI_CONTEXT_INDICATOR_FIELD_0_VERSION_FLOW_CONTEXT, cif0)), DIFI_CONTEXT_INDICATOR_FIELD_0_VERSION_FLOW_CONTEXT==cif0)
            if cif1 is not None: self.context_indicator_field_1 = (("must be: 0x%08x -> was: 0x%08x" % (DIFI_CONTEXT_INDICATOR_FIELD_1_VERSION_FLOW_CONTEXT, cif1)), DIFI_CONTEXT_INDICATOR_FIELD_1_VERSION_FLOW_CONTEXT==cif1)
            if v49_spec is not None: self.v49_spec_version = (("must be: 0x%08x -> was: 0x%08x" % (DIFI_V49_SPEC_VERSION_VERSION_FLOW_CONTEXT, v49_spec)), DIFI_V49_SPEC_VERSION_VERSION_FLOW_CONTEXT==v49_spec)

        ############
        #data packet
        ############
        elif packet_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID:
            #stream id
            if stream_id is not None:
                self.stream_id = stream_id
            else:
                self.stream_id = "no-stream-id"
            #header
            self.packet_type = ("0x%1x" % packet_type)
            self.packet_type_display =  (("must be: 0x%1x, 0x%1x, 0x%1x -> was: 0x%1x" % (DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID, packet_type)), True)
            if class_id is not None: self.class_id = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_CLASSID, class_id)), DIFI_CLASSID==class_id)
            if reserved is not None: self.reserved = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_RESERVED, reserved)), DIFI_RESERVED==reserved)
            if tsm is not None: self.tsm = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSM_DATA, tsm)), DIFI_TSM_DATA==tsm)
            if tsf is not None: self.tsf = (("must be: 0x%1x -> was: 0x%1x" % (DIFI_TSF_REALTIME_PICOSECONDS, tsf)), DIFI_TSF_REALTIME_PICOSECONDS==tsf)
            #packet

        ############
        #unknown packet type
        ############
        else:
            #stream id
            if stream_id is not None:
                self.stream_id = stream_id
            else:
                self.stream_id = "no-stream-id"
            #header
            self.packet_type = ("0x%1x" % packet_type)
            self.packet_type_display =  (("must be: 0x%1x, 0x%1x, 0x%1x -> was: 0x%1x" % (DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID, packet_type)), False)


    #json encoder to change stream id to hex string
    class DifiInfoJSONEncoder(json.JSONEncoder):

        def encode(self, o):
            d = o.copy()

            if type(d["stream_id"]) is int:
                d.update(stream_id = "0x%08x" % d["stream_id"])

            return json.JSONEncoder.encode(self, d)

    def to_json(self):
        return json.dumps(self.__dict__, indent=4, cls=self.DifiInfoJSONEncoder)
        #return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    def __str__(self):
        return self.to_json()
