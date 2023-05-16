from datetime import timezone, datetime
import struct
from io import BytesIO
import json

from difi_utils.difi_constants import *
from difi_utils.custom_error_types import *

#############################
# version context packet class - object that is filled from the decoded version context packet stream
#############################

DEBUG = False

class DifiVersionContextPacket():
    """
    DIFI Context Packet.
      -Version Flow Signal Context Packet

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
        if DEBUG: print("DifiVersionContextPacket header data in constructor:")
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

        #only allow if version context packet type
        if self.pkt_type == DIFI_VERSION_FLOW_SIGNAL_CONTEXT:

            #only decode if header is valid
            if self.is_difi10_version_context_packet_header(self.pkt_type, self.pkt_size, self.class_id, self.reserved, self.tsm, self.tsf):
                packet_size_in_bytes = (self.pkt_size - 1) * 4  #less header (-1)
                context_data = stream.read1(packet_size_in_bytes)
                self._decode_version_flow_signal_context(context_data)
            else:
                raise NoncompliantDifiPacket("non-compliant DIFI version context packet header [packet type: 0x%1x]" % self.pkt_type, DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))
        else:
            raise NoncompliantDifiPacket("non-compliant packet type [0x%1x] for DIFI version context packet  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (self.pkt_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))


    #function to decode version context packet
    def _decode_version_flow_signal_context(self, data):

        if DEBUG: print("Decoding.....")
        #print(data.hex())

        try:
            #only fully decode if DIFI compliant
            #  -check Information Class Code/Packet Class Code
            #  -check Context Indicator Field 0
            #  -check Context Indicator Field 1
            #  -check V49 Spec Version
            (icc,pcc) = struct.unpack(">HH", data[8:12])
            (cif0,) = struct.unpack(">I", data[24:28])
            cif0 = (cif0 & 0x0fffffff)
            (cif1,) = struct.unpack(">I", data[28:32])
            (v49_spec,) = struct.unpack(">I", data[32:36])
            if not self.is_difi10_version_context_packet(icc, pcc, cif0, cif1, v49_spec):
                raise NoncompliantDifiPacket("non-compliant DIFI version context packet.", DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, packet_size=self.pkt_size, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf, icc=icc, pcc=pcc, cif0=cif0, cif1=cif1, v49_spec=v49_spec))


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
            if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')))
            #if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')))
            self.integer_seconds_timestamp = value
            self.integer_seconds_timestamp_display = datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')

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
            # Context Indicator Field(CIF 1) (9)
            #######################
            if DEBUG: print(data[28:32].hex())
            (value,) = struct.unpack(">I", data[28:32])
            if DEBUG: print(" Context Indicator Field (CIF 1) = 0x%08x" % (value))
            self.context_indicator_field_cif1 = value

            #######################
            # V49 Spec Version (9)
            #######################
            if DEBUG: print(data[32:36].hex())
            (value,) = struct.unpack(">I", data[32:36])
            if DEBUG: print(" V49 Spec Version = 0x%08x" % (value))
            self.v49_spec_version = value

            #######################
            # Year, Day, Revision, Type, ICD Version (9.10.4)
            #######################
            if DEBUG: print(data[36:40].hex())
            (value,) = struct.unpack(">I", data[36:40])
            self.year = (value >> 25) & 0x7f         #(bit 25-31)
            self.year+=2000
            self.day  = (value >> 16) & 0x1ff        #(bit 16-24)
            self.revision = (value >> 10) & 0x3f     #(bit 10-15)
            self.type = (value >> 6) & 0xf           #(bit 6-9)
            self.icd_version = (value >> 0) & 0x3f   #(bit 0-5)
            if DEBUG: print(" Year=%d - Day=%d - Revision=%d - Type=%d - ICDVersion=%d" % (self.year,self.day,self.revision,self.type,self.icd_version))

        except NoncompliantDifiPacket as e:
            raise e
        except Exception as e:
            raise e

        if DEBUG: print("Finished decoding.\r\n---\r\n")

        #debug
        #print("JSON dump object 'DifiVersionContextPacket'-version flow:\r\n\r\n", self.to_json())
        #print("String dump object 'DifiVersionContextPacket'-version flow:\r\n", str(self))


    #json encoder to change applicable int's to hex string
    class VersionContextPacketHexJSONEncoder(json.JSONEncoder):

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
            if type(d["context_indicator_field_cif1"]) is int:
                d.update(context_indicator_field_cif1 = "0x%08x" % d["context_indicator_field_cif1"])
            if type(d["v49_spec_version"]) is int:
                d.update(v49_spec_version = "0x%08x" % d["v49_spec_version"])

            return json.JSONEncoder.encode(self, d)


    def to_json(self, hex_values=False):
        #s = json.dumps(self, default=vars, indent=4)
        #s = json.loads(zlib.decompress(data))
        if hex_values is True:
            return json.dumps(self.__dict__, indent=4, cls=self.VersionContextPacketHexJSONEncoder)
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
Context Indicator Field (CIF 1): 0x%08x\r\n\
V49 Spec Version: 0x%08x\r\n\
Year: %d\r\n\
Day: %d\r\n\
Revision: %d\r\n\
Type: %d\r\n\
ICD Version: %d\r\n\
" % (self.stream_id,
    self.oui,
    self.information_class_code,
    self.packet_class_code,
    self.integer_seconds_timestamp,
    datetime.fromtimestamp(self.integer_seconds_timestamp, tz=timezone.utc).strftime('%m/%d/%Y %r %Z'),
    self.fractional_seconds_timestamp,
    self.context_indicator_field_cif0,
    self.context_indicator_field_cif1,
    self.v49_spec_version,
    self.year,
    self.day,
    self.revision,
    self.type,
    self.icd_version))


    ##############################
    # DIFI packet validation checks
    ##############################

    #version context packet header
    def is_difi10_version_context_packet_header(self, packet_type, packet_size, class_id, rsvd, tsm, tsf):
        return (packet_type == DIFI_VERSION_FLOW_SIGNAL_CONTEXT
            and packet_size == DIFI_VERSION_FLOW_SIGNAL_CONTEXT_SIZE
            and class_id == DIFI_CLASSID
            and rsvd == DIFI_RESERVED
            and tsm == DIFI_TSM_GENERAL_TIMING
            and tsf == DIFI_TSF_REALTIME_PICOSECONDS)

    #version context packet
    def is_difi10_version_context_packet(self, icc, pcc, cif0, cif1, v49_spec):
        return (icc == DIFI_INFORMATION_CLASS_CODE_VERSION_FLOW_CONTEXT
            and pcc == DIFI_PACKET_CLASS_CODE_VERSION_FLOW_CONTEXT
            and cif0 == DIFI_CONTEXT_INDICATOR_FIELD_0_VERSION_FLOW_CONTEXT
            and cif1 == DIFI_CONTEXT_INDICATOR_FIELD_1_VERSION_FLOW_CONTEXT
            and v49_spec == DIFI_V49_SPEC_VERSION_VERSION_FLOW_CONTEXT)
