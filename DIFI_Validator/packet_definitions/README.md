# Overview of the Packet Definitions

All .py files in this directory using the filename difi-type-version.py (eg difi_context_v1_1.py) are packet definitions using the [Construct](https://construct.readthedocs.io/en/latest/index.html) Python package, along with validations for that packet type.

# Running the Parser

A PCAP or live UDP stream can be parsed with either
`parse_pcap.py --pcap ../examples/Example1_1Msps_8bits.pcapng`
or for UDP, 
`python parse_pcap.py --udp-port 50003`

One option is to use the gr-difi example `pn11_over_difi_tx.grc` to test the UDP mode.

# Running the Generator

TODO
