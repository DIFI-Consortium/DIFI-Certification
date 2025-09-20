The VSCode extension "ASN.1" by Jonathan M. Wilbur is useful for coloring and syntax highlighting

ASN.1 itself doesn’t force bit-packing; encodings (like PER — Packed Encoding Rules) will handle putting them in exactly the bit widths.
So I think we need to use PER encoding (vs BER encoding or unaligned-PER aka UPER encoding)

Bitproto has nice looking docs but the python support is designed around compiling a .bitproto definition into a python module, I don't see any runtime compiling option, and I don't want to have to have that extra step. This command generated python code for serial/deserial, but thats not really what i want- `bitproto py DIFI_context_v1.1.bitproto`

The big ASN.1 Python packages are

1. https://github.com/pycrate-org/pycrate
2. https://github.com/etingof/pyasn1
   - Doesn’t include PER encoding/decoding out of the box
   - Doesn't allow reading in of ASN.1 files, they have to be defined within Python...
3. https://github.com/eerimoq/asn1tools
