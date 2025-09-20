import asn1tools
from pycrate_asn1rt.utils import *
from pycrate_asn1c.asnproc import compile_text
from scapy.all import PcapReader, UDP
import struct
#from difi_utils.difi_context_packet_class import DifiStandardContextPacket
from io import BytesIO

pcap_file = "../examples/Example1_1Msps_8bits.pcapng"

for packet in PcapReader(pcap_file):
    payload = bytes(packet[UDP].payload)
    first_4bytes = payload[0:4]
    packet_type = first_4bytes[0] >> 4
    if packet_type == 0x4:
        print("Found first context packet")
        break

#pkt = DifiStandardContextPacket(BytesIO(payload))
#print(hex(pkt.context_indicator_field_cif0))

# asn1tools version, doesnt support CONSTRAIN BY validations =(
spec = asn1tools.compile_files('DIFI_context_v1.1.asn1', 'per')

# Decode
decoded = spec.decode('DIFIContext', payload, check_constraints=True)

# convert decoded["cif0"] from bytes to a hex string
decoded['cif0'] = hex(decoded['cif0'])

# Scaling factors
decoded['bandwidth'] /= 2.0 ** 20
decoded['ifFreq'] /= 2.0 ** 20
decoded['rfFreq'] /= 2.0 ** 20
decoded['ifBandOffset'] /= 2.0 ** 20
decoded['referenceLevel'] /= 2.0 ** 7
decoded['stage1GainAtten'] /= 2.0 ** 7
decoded['stage2GainAtten'] /= 2.0 ** 7
decoded['sampleRate'] /= 2.0 ** 20
decoded['timeStampAdj'] /= 2.0 ** 20
decoded['timeStampCal'] /= 2.0 ** 20
decoded['stateEventInd'] /= 2.0 ** 20
decoded['dataPacketFormat'] /= 2.0 ** 20

print("Decoded dict:", decoded)

# Example of one-liner validations:
if decoded['header']['pktType'] != 4: raise ValueError("pktType must be 4")
if decoded['header']['classId'] != 1: raise ValueError("classId must be 1")
if decoded['header']['reserved'] != 0: raise ValueError("reserved must be 0")


# Example of encoding based on python dict
if False:
    # Example header values
    data = {
        'pktType':  2,
        'classId':  1,
        'reserved': 0,
        'tsm':      1,
        'tsi':      3,
        'tsf':      2,
        'seqNum':   7,
        'pktSize':  512
    }

    # Encode into 4-byte binary (PER)
    encoded = spec.encode('DIFI-Context', data)
    print("Encoded bytes:", encoded.hex())

