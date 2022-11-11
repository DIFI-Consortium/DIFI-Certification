# Licensed under the MIT License.
# SPDX-License-Identifier: MIT

# This is a sample packet, used in dds.py

def sample_data(difi_packet: bytearray()):

    for _ in range(1, 2):
        packetchunk = bytearray.fromhex('1de8fcd507ec1130192135f62d1009360a3b0f3605370439fd36e52ed914f0e203c015d029e61814002f06ee04c41deb3103f900c30dd81de6270a0737f90917df2b0b262b1e0bfbf8d006f807360209')
        difi_packet.extend(packetchunk)
        packetchunk = bytearray.fromhex('fecae6d3dae4eef4072df439dc22db10f6d9f6dbde21f52c231a161ee0f2d9d1f8d001c3fabf06ca1dcc30e12e07241e0df0ffcf03130241ee2bd31fcb06dfd809e336fb2fe51fda0e05e42601123bfd')
        difi_packet.extend(packetchunk)
        packetchunk = bytearray.fromhex('2219ff37093c0433ec1cd9e5d5d5dae0f4e51f1524340130ee27dff0ddc7f6d0fbc8e2d1e1ebff180a3a1e24291a1ffa22d012d504cd2be03d0239fa3aff3b0537fc1ee6fdcde6e4ca02cee7e1d4fcdf')
        difi_packet.extend(packetchunk)
        packetchunk = bytearray.fromhex('33fe390f211e0817e3e3f2ec2323190900cc00c803d1fbdde413d22cda1fce20c509d205ef2b0b3719251f1c08ee02d20619fc3102e802c4fbcd0cc920ca26daffdbd9d5dfdae6dbecfefe39ec35d421')
        difi_packet.extend(packetchunk)
        packetchunk = bytearray.fromhex('d02ad225d122d225d324d823f7142f0037f626e237e63c013c043a03200ae207c3fccf00cb01cd13da13f2dc06bfffccfbcfe4e9d1f50cde27dbf3dde1da1103262426f92bd82ce52ae020d10bd01af2')
        difi_packet.extend(packetchunk)
        packetchunk = bytearray.fromhex('292827092ddf1b07fb3aef33da1fca09dede00d92b001ffce8d8f7df34002cf40aca06c609d0ffd9e30be21f22022c00efead9dfde10dd26051c1b27edfcd6d2d5efd0f7ffde2de7fd06d21cf2f609c5')
        difi_packet.extend(packetchunk)
        packetchunk = bytearray.fromhex('ebccdddcf3fcfe32112232fe10fee4dc07df34091407d6f6e8fc2f051c07d0f8c5fbd0ffdefd0d1b102cd405cfe7f9da02cfd4eac5fbd2f6d1fde51e04321e17300af721cc21eb30f33add2ad41ef727')
        difi_packet.extend(packetchunk)
        packetchunk = bytearray.fromhex('212a230626e50f07d921ff0e37060ef5e1d406d32ee610e6d4f1e6ef2fe538e830ff31ff15d414d8201d0e23f1e4e8c805d310dafe0fe838da05d5f3011d22311a29162311f50bc40dcd0ed708fdf138')
        difi_packet.extend(packetchunk)
        packetchunk = bytearray.fromhex('dc15d2eaf3ea31e221d208c715cb10cbfec8e9cde1cfe9cee5cde9ccffd228dc2bdf11c81dd73501380331e819ece0f8dceb21e43ced2ffd3a0d36f42ede1ddb07d4eb01cd1fd013d219db29f035ed37')
        difi_packet.extend(packetchunk)

        packetchunk = bytearray.fromhex('ee34ef3be834db1bc7f4cb01cd19d3f4e4cbe6cce8d10edd3109171bd712e80929f216f2d114dc0410d70de1f3230232')
        difi_packet.extend(packetchunk)

    # Add more to set size
    packetchunk = bytearray.fromhex('3a091b24f934e50c')
    difi_packet.extend(packetchunk)
    return difi_packet
# End
