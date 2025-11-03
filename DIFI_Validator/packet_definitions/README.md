# Overview of the Packet Definitions

All .py files in this directory using the filename difi-type-version.py (eg difi_context_v1_1.py) are packet definitions using the [Construct](https://construct.readthedocs.io/en/latest/index.html) Python package, along with validations for that packet type.

# Running the Parser

A PCAP or live UDP stream can be parsed with either
`python parse_difi.py --pcap ../examples/Example1_1Msps_8bits.pcapng`
or for UDP, 
`python parse_difi.py --udp-port 50003`

One option is to use the gr-difi example `pn11_over_difi_tx.grc` to test the UDP mode.

# Running the Generator

The following examples generate a live UDP stream of DIFI with 10 context packets per second, 2 version packets per second, and data packets corresponding to the requested sample rate and samples-per-packet:

`python generate_difi.py --port 50003 --sample-rate 100e3 --samples-per-packet 150 --bit-depth 8`

