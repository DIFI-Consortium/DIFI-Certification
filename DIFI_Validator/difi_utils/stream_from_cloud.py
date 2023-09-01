import dpkt
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient, StorageStreamDownloader
import io
import struct
import time
from azure.storage.blob import BlobClient
import dpkt
import pandas as pd
from difi_utils.noncompliant_class import DifiInfo
from difi_utils.difi_data_packet_class import DifiDataPacket
from difi_utils.difi_context_packet_class import DifiStandardContextPacket
from difi_utils.legacy_difi_context_packet_class import DifiStandardContextPacket as LegacyDifiStandardContextPacket
from difi_utils.difi_version_packet_class import DifiVersionContextPacket
from difi_utils.custom_error_types import NoncompliantDifiPacket
from difi_utils.difi_constants import *
import numpy as np

def process_packet(data: bytes, difi_format: str=None):
    if data is None:
        print("packet received, but data empty.")
        return

    stream = io.BytesIO(data)

    # packet type and stream ID
    packet_type, stream_id = struct.unpack(">II", data[:8])
    packet_type = (packet_type >> 28) & 0x0f   #(bit 28-31)

    # create instance of packet class for packet type and parse packet
    if packet_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT and len(data) == 108: # DIFI 1.0 context packets
        pkt = DifiStandardContextPacket(stream)
    elif packet_type == DIFI_STANDARD_FLOW_SIGNAL_CONTEXT and (len(data) == 84 or len(data) == 72): # Legacy DIFI context packets
        pkt = LegacyDifiStandardContextPacket(stream)
    elif packet_type == DIFI_VERSION_FLOW_SIGNAL_CONTEXT:
        pkt = DifiVersionContextPacket(stream)
    elif packet_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID:
        pkt = DifiDataPacket(stream, return_iq=True)
    elif packet_type == DIFI_STANDARD_FLOW_SIGNAL_DATA_NO_STREAMID: # DIFI doesnt support this type of packet
        raise NoncompliantDifiPacket("non-compliant DIFI data packet type [data packet without stream ID packet type: 0x%1x]  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (packet_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type=packet_type, stream_id=stream_id))
    else:
        raise NoncompliantDifiPacket("non-compliant DIFI packet type [0x%1x]  (must be [0x%1x] standard context packet, [0x%1x] version context packet, or [0x%1x] data packet)" % (packet_type, DIFI_STANDARD_FLOW_SIGNAL_CONTEXT, DIFI_VERSION_FLOW_SIGNAL_CONTEXT, DIFI_STANDARD_FLOW_SIGNAL_DATA_WITH_STREAMID), DifiInfo(packet_type, stream_id=stream_id))

    return pkt

def process_pcap(pcap_stream, packet_offset_bytes=0, max_time_spent=None):
    compliance_logs = []
    compliance_logs_keys = ["pcap_timestamp", "pcap_index", "pkt_type"]

    common_field_logs = []
    common_field_logs_keys = ["pcap_timestamp", "pcap_index", "pkt_type", "class_id", "tsm", "tsi", "tsf", "seq_num", "pkt_size"]

    packet_logs = {}
    ffts = []
    start_t = time.time()
    for pkt_count, (ts, buf) in enumerate(pcap_stream):
        #print(f"ts {ts}, buflen {len(buf)}")
        if pkt_count % 100 == 0:
            print(f"processed {pkt_count} packets so far")
        if max_time_spent and (time.time() - start_t) > max_time_spent:
            return compliance_logs, common_field_logs, packet_logs, ffts
        try:
            eth = dpkt.ethernet.Ethernet(buf)
            ip_payload = eth.data.data
            if type(ip_payload) is dpkt.udp.UDP: # and len(ip_payload.data) > 100:
                try:
                    difi_pkt = process_packet(data=ip_payload.data[packet_offset_bytes:])
                    if hasattr(difi_pkt, "samples"):
                        ffts.append(10*np.log10(np.abs(np.fft.fftshift(np.fft.fft(difi_pkt.samples[0:512])))**2))
                    difi_pkt_dict = vars(difi_pkt)
                    difi_pkt_dict.update({
                        "pcap_timestamp": ts,
                        "pcap_index": pkt_count
                    } )

                    compliance_logs.append(
                        {k: difi_pkt_dict[k] for k in compliance_logs_keys}
                    )

                    common_field_logs.append(
                        {k: difi_pkt_dict[k] for k in common_field_logs_keys}
                    )

                    if difi_pkt.pkt_type not in packet_logs:
                        packet_logs[difi_pkt.pkt_type] = []


                    packet_logs[difi_pkt.pkt_type].append(difi_pkt_dict)


                except NoncompliantDifiPacket as err:
                    #print(f"NoncompliantDifiPacket: {err}")
                    compliance_logs.append({
                        "pcap_timestamp": ts,
                        "pcap_index": pkt_count,
                        "pkt_type": -1
                    })

        except dpkt.UnpackError as err:
            print(f"error at pkt_count {pkt_count}, ts: {ts}, buf len {len(buf)}")
            raise err

    return compliance_logs, common_field_logs, packet_logs, ffts


def process_pcap_from_blob(blob_client: BlobClient, packet_offset_bytes=0, max_time_spent=None):
    streamer = BlobPcapPacketStreamer(blob_client=blob_client)
    compliance_logs, common_field_logs, packet_logs, ffts = process_pcap(pcap_stream=streamer,
                                                                   packet_offset_bytes=packet_offset_bytes,
                                                                   max_time_spent=max_time_spent)
    return compliance_logs, common_field_logs, packet_logs, ffts


def process_pcap_from_file(filename: str, packet_offset_bytes=0, max_time_spent=None):
    with open(filename, 'rb') as f:
        pcap_stream = dpkt.pcap.Reader(f)
        compliance_logs, common_field_logs, packet_logs, ffts = process_pcap(pcap_stream=pcap_stream,
                                                                       packet_offset_bytes=packet_offset_bytes,
                                                                       max_time_spent=max_time_spent)
    return compliance_logs, common_field_logs, packet_logs, ffts


class BlobPcapPacketStreamer(object):
    def __init__(self, blob_client: BlobClient):
        self.blob_client = blob_client
        self.max_buf_size = 2**32
        self.blob_stream = self.blob_client.download_blob()
        self.__iter = iter(self)

    def __next__(self):
        return next(self.__iter)

    def __iter__(self):
        chunks = self.blob_stream.chunks()
        partial_packet_buf = bytes()

        handle_partial_packet = False
        packet_residue_len = 0
        hdr = None
        old_ts = None

        pcap_stream = None
        pkt_count = 0

        for chunk_num, chunk in enumerate(chunks):
            #print(f"chunk num {chunk_num} size {len(chunk)}")
            chunk_buf = io.BytesIO(initial_bytes=chunk)
            if handle_partial_packet:
                if hdr is None:
                    missing_bytes = pcap_stream.pcap_header_len() - len(partial_packet_buf)
                    #print(f"{missing_bytes} missing bytes from header, {len(chunk)-chunk_buf.tell()} bytes left in buffer")
                    residue_buf = chunk_buf.read(missing_bytes)
                    #print(f"read {len(residue_buf)} bytes to complete buffer")
                    hdr = pcap_stream.parse_pcap_header(partial_packet_buf + residue_buf)
                    ts = pcap_stream.get_ts(hdr)
                    buf = chunk_buf.read(hdr.caplen)
                else:
                    packet_residue = chunk_buf.read(packet_residue_len)
                    buf = partial_packet_buf + packet_residue
                    ts = old_ts

                handle_partial_packet = False
                if len(buf) == 0:
                    print(f"hdr caplen: {hdr.caplen}, packet_residue_len {packet_residue_len}, chunk len {len(chunk)}")
                yield ts, buf

                #print(f"buf position after reading packet residue of {packet_residue_len} bytes: {chunk_buf.tell()}")
                #print(f"chunk: {chunk_num} pkt_count {pkt_count} stitching packets together at ts {ts}")
                pkt_count = pkt_count + 1

            if pcap_stream is None:
                pcap_stream = ReaderWithHeader(chunk_buf)
            else:
                pcap_stream.update_file(chunk_buf)

            # how far in the buffer to try to read
            read_limit = len(chunk) - pcap_stream.pcap_header_len()
            while pcap_stream.tell() < read_limit:
                ts, hdr, buf = next(pcap_stream)
                #print(f"ts {ts}, hdr caplen: {hdr.caplen}, len buf {len(buf)}")
                pcap_packet_len = hdr.caplen
                pcap_buf_len = len(buf)
                # do we have the full packet?
                if pcap_packet_len == pcap_buf_len:
                    #print(f"chunk: {chunk_num} pkt_count {pkt_count} ts {ts} pkt_len {pcap_packet_len} buf_len {pcap_buf_len}")
                    yield ts, buf
                    pkt_count = pkt_count + 1
                # do we have a partial packet buffer at a chunk boundary?
                elif pcap_packet_len > pcap_buf_len and pcap_stream.tell() == len(chunk):
                    #print(f"partial packet at chunk boundary, {len(buf)} bytes in buffer")
                    #print(f"chunk: {chunk_num} pkt_count {pkt_count} ts {ts} pkt_len {pcap_packet_len} buf_len {pcap_buf_len}")
                    partial_packet_buf = buf
                    old_ts = ts
                    packet_residue_len = min(self.max_buf_size, pcap_packet_len-pcap_buf_len)
                    handle_partial_packet = True
                    break
            else:
                # check if we ended in the middle of a pcap header
                if pcap_stream.tell() < len(chunk):
                    #print(f"header not decoded, {len(chunk)-pcap_stream.tell()} bytes left")
                    partial_packet_buf = chunk_buf.read()
                    handle_partial_packet = True
                    hdr = None
        return


class ReaderWithHeader(dpkt.pcap.Reader):
    def get_ts(self, hdr):
        return hdr.tv_sec + (hdr.tv_usec / self._divisor)

    def __iter__(self):
        while 1:
            __buf = self._Reader__f.read(self._Reader__ph.__hdr_len__)
            if not __buf:
                break
            __hdr = self._Reader__ph(__buf)
            __buf = self._Reader__f.read(__hdr.caplen)
            yield (self.get_ts(__hdr), __hdr, __buf)

    def update_file(self, fileobj):
        self._Reader__f = fileobj

    def pcap_header_len(self):
        return self._Reader__ph.__hdr_len__

    def parse_pcap_header(self, buf):
        hdr = self._Reader__ph(buf[:self.pcap_header_len()])
        return hdr

    def tell(self):
        return self._Reader__f.tell()
