from datetime import timezone, datetime
import struct
from io import BytesIO
import json
import os

from utils.difi_constants import *
from utils.custom_error_types import *

##################
# data packet class - object that is filled from the decoded data packet stream
##################

DEBUG = False

if os.getenv("SAVE_IQ"):
    SAVE_IQ = True
else:
    SAVE_IQ = False

class DifiDataPacket():
    """
    DIFI Data Packet.
      -Standard Flow Signal Data Packet

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
        if DEBUG: print("DifiDataPacket header data in constructor:")
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

        if self.pkt_type != DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID:
            raise NoncompliantDifiPacket("non-compliant packet type [0x%1x] for DIFI data packet  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (self.pkt_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))

        #only decode if header is valid
        if self.is_difi10_data_packet_header(self.pkt_type, self.class_id, self.reserved, self.tsm, self.tsf):
            packet_size_in_bytes = (self.pkt_size - 1) * 4  #less header (-1)
            context_data = stream.read1(packet_size_in_bytes)

            if DEBUG: print("Decoding.....")
            try:
                #######################
                # Stream ID (5.1.2)
                #######################
                if DEBUG: print(context_data[0:4].hex())
                #already unpacked in constructor __init__
                #(value,) = struct.unpack(">I", context_data[0:4])
                #if DEBUG: print(" Stream ID = 0x%08x (ID)" % (value))
                #self.stream_id = value
                if DEBUG: print(" Stream ID = 0x%08x (ID)" % (self.stream_id))

                ##########################
                # OUI (5.1.3)
                ##########################
                if DEBUG: print(context_data[4:8].hex())
                #h = b'\x00\x7C\x38\x6C'
                #h = b'\x00\x00\x12\xa2'
                (value,) = struct.unpack(">I", context_data[4:8])
                value = value & 0x00FFFFFF
                if DEBUG: print(" OUI = 0x%06x" % (value))
                self.oui = value

                #########################
                # Information Class Code / Packet Class Code (5.1.3)
                ########################
                if DEBUG: print(context_data[8:12].hex())
                #h = b'\x00\x00\x00\x00'
                (icc,pcc) = struct.unpack(">HH", context_data[8:12])
                if DEBUG: print(" Information Class Code = 0x%04x - Packet Class Code = 0x%04x" % (icc, pcc))
                self.information_class_code = icc
                self.packet_class_code = pcc

                #######################
                # Integer-seconds Timestamp (5.1.4 and 5.1.5)
                #######################
                if DEBUG: print(context_data[12:16].hex())
                (value,) = struct.unpack(">I", context_data[12:16])
                if DEBUG: print(" Integer-seconds Timestamp (seconds since epoch) = %d (%s)" % (value, datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z'))) #.strftime('%a, %d %b %Y %H:%M:%S +0000')))
                self.integer_seconds_timestamp = value
                self.integer_seconds_timestamp_display = datetime.fromtimestamp(value, tz=timezone.utc).strftime('%m/%d/%Y %r %Z')

                #######################
                # Fractional-seconds Timestamp (5.1.4 and 5.1.5)
                #######################
                if DEBUG: print(context_data[16:24].hex())
                (value,) = struct.unpack(">Q", context_data[16:24])
                if DEBUG: print(" Fractional-seconds Timestamp (picoseconds past integer seconds) = %d" % (value))
                self.fractional_seconds_timestamp = value

                #######################
                # Signal Data Payload
                #######################
                #payload size is size minus 28 bytes for difi headers
                # (7 words * 4 bytes per word) = 28 bytes
                #already removed 1st word of header earlier above
                # (28 bytes - 4 bytes) = 24 bytes
                self.payload_data_size_in_bytes = len(context_data) - 24
                self.payload_data_num_32bit_words = (len(context_data) - 24) / 4
                if DEBUG: print(". . .")
                if DEBUG: print(" Payload Data Size = %d (bytes), %d (32-bit words)" % (self.payload_data_size_in_bytes, self.payload_data_num_32bit_words))

                # Save IQ samples to a file if enabled
                if SAVE_IQ:
                    import numpy as np
                    data_type = np.int8 # CURRENTLY THIS HAS TO BE MANUALLY SET!
                    f_out_name = '/tmp/samples.iq'
                    signal_bytes = context_data[24:]
                    samples =  np.frombuffer(signal_bytes, dtype=data_type) # MAKE SURE THIS MATCHES THE DATA ITEM SIZE FIELD IN TEH CONTEXT PACKET!
                    f_out = open(f_out_name, 'ab') # APPEND, MAKE SURE TO DELETE OR RENAME THE FILE
                    samples.tofile(f_out) # its creating a binary IQ file
                    f_out.close()

                #self.payload_raw_data = context_data[24:]  #str(context_data[24:]) for json
                #self.payload_raw_hex_data = context_data[24:].hex()
                #words_list = [context_data[24:].hex()[i:i+8] for i in range(0,len(context_data[24:].hex()),8)]
                #print(type(words_list).__name__)
                #print(len(words_list))
                #print(words_list)
                #self.payload_raw_data_as_word_list = words_list
                #if DEBUG: print(" Payload Raw Data = %s" % (self.payload_raw_data))
                #if DEBUG: print(" Payload Raw Hex Data = %s" % (self.payload_raw_hex_data))
                #if DEBUG: print(" Payload Raw Data (list of words) = %s" % (self.payload_raw_data_as_word_list))

            except NoncompliantDifiPacket as e:
                raise e
            except Exception as e:
                raise e
            if DEBUG: print("Finished decoding.\r\n---\r\n")

        else:
            raise NoncompliantDifiPacket("non-compliant DIFI data packet header [packet type: 0x%1x]" % self.pkt_type, DifiInfo(packet_type=self.pkt_type, stream_id=self.stream_id, class_id=self.class_id, reserved=self.reserved, tsm=self.tsm, tsf=self.tsf))


    #json encoder to change applicable int's to hex string
    class DataPacketHexJSONEncoder(json.JSONEncoder):

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
            return json.JSONEncoder.encode(self, d)


    def to_json(self, hex_values=False):
        #s = json.dumps(self, default=vars, indent=4)
        #s = json.loads(zlib.decompress(data))
        if hex_values is True:
            return json.dumps(self.__dict__, indent=4, cls=self.DataPacketHexJSONEncoder)
        else:
            return json.dumps(self, default=lambda o: o.__dict__, indent=4)


    def __str__(self):

        return ("Stream ID: 0x%08x (ID)\r\n\
OUI: 0x%06x\r\n\
Information Class Code: 0x%04x\r\n\
Packet Class Code: 0x%04x\r\n\
Integer-seconds Timestamp (seconds since epoch): %d (%s)\r\n\
Fractional-seconds Timestamp (picoseconds past integer-seconds): %d\r\n\
Payload Data Size: %d (bytes), %d (32-bit words)\r\n\
" % (self.stream_id,
    self.oui,
    self.information_class_code,
    self.packet_class_code,
    self.integer_seconds_timestamp,
    datetime.fromtimestamp(self.integer_seconds_timestamp, tz=timezone.utc).strftime('%m/%d/%Y %r %Z'),
    self.fractional_seconds_timestamp,
    self.payload_data_size_in_bytes,
    self.payload_data_num_32bit_words))

        #TODO: should we include RAW data fields in console output???????
        #Payload Raw Data: %s\r\n\
        #Payload Raw Hex Data: %s\r\n\
        #Payload Raw Data (list of words): %s\r\n\
        #self.payload_raw_data,
        #self.payload_raw_hex_data,
        #self.payload_raw_data_as_word_list


    ##############################
    # DIFI packet validation checks
    ##############################

    #data packet header
    def is_difi10_data_packet_header(self, packet_type, class_id, rsvd, tsm, tsf):
        return (packet_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID
            and class_id == DIFI_CLASSID
            and rsvd == DIFI_RESERVED
            and tsm == DIFI_TSM_DATA
            and tsf == DIFI_TSF_REALTIME_PICOSECONDS)

