# Copyright (C) 2022 Kratos Technology & Training Solutions, Inc.
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT
# DIFI
DIFI verification

These scripts send and recieve VITA/DIFI packets.  There are examples of Context, Dat and Version packets.

# See Also:
https://dificonsortium.org/  </BR>
https://ieee-isto.org/press-releases/difi-announcement/

# Send a DIFI Context Packet
# python3 dcs.py

# Receive DIFI Packets
# python3 drx.py

# Send a DIFI Data Packet
# python3 dds.py

# DIFI Headers (based on VITA)
# python protocol --no-numbers "Pckt Type:4,C:1,Indicators:3, TSI:2,TSF:2,Pckt Ct:4,Packet Size:16" 
   3                   2                   1                   0
 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Pckt T.|C|Indi.|TSI|TSF|Pckt Ct|          Packet Size          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

# Expanded VRT Packet Header showing 32 bit and field width details.

# VITA 49.2
#      3                                       2                                       1                                       0
#  1   0   9   8   7   6   5   4   3   2   1   0   9   8   7   6   5   4   3   2   1   0   9   8   7   6   5   4   3   2   1   0
#+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
#|   Packet Type | C |Indicators |  TSI  |  TSF  |  Packet Count |                            Packet Size                        |
#+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

# Errata, DIFI 1.x  (CB 12/6/2021)
# Context  Packet Type 0100
# Version  Packet Type 0101
# Data     Packet Type 0001
#      3                                       2                                       1                                       0
#  1   0   9   8   7   6   5   4   3   2   1   0   9   8   7   6   5   4   3   2   1   0   9   8   7   6   5   4   3   2   1   0
#+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
#| 0   1   0   0 | 1 | 0  0/1  1 |  TSI  | 1   0 |  Packet Count |                            Packet Size (27 words)             |
#+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
#| 0   1   0   1 | 1 | 0  0/1? 1 |  TSI  | 1   0 |    SeqNum     |                            Packet Size (11 words)             |
#+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
#| 0   0   0   1 | 1 | 0  0/1? 0 |  TSI  | 1   0 |  Packet Count |                            Packet Size (M Words)              |
#+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+

<B> Footnote: M Words = N + 7 Words. There are always </B>
<B> seven header 32-bit words so the final packet size will be the data  </B>
# payload length in words (N) + 7.



# Device Identifer Field
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Reserved   |                Manufacurer OUI                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            Reserved           |          Device Code          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

# python protocol --no-numbers "Reserved:8,Manufacurer OUI:24, Reserved:16,Device Code:16"
3                   2                   1                   0
 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Most-significant Upper 32-bits                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                Least-significant Lower 32-bits                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


# Fractional Seconds Timestamp

python protocol --no-numbers "Most-significant Upper 32-bits:32,Least-significant Lower 32-bits:32"
3                   2                   1                   0
 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Most-significant Upper 32-bits                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                Least-significant Lower 32-bits                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+



# python protocol --no-numbers "Pckt Type:4,C:1,Indicators:3, TSI:2,TSF:2,Packet Count:4,Packet Size:16,Stream ID:32, Pad:5, Res:3,OUI:24,Info Class:16,Packet Class:16, Integer Sec Timestamp:32, Fractional-Seconds Timestamp:64, Context Indicators:32, Reference Point:32, Bandwidth:64,IF Reference Freqency:64,RF Reference Freq:64,IF Band Offset:64, Reference Level:32,Gain & Attenuation:32,Sample Rate:64,Timestamp Adjustment:64, Timestamp Calibration Time (sec):32, State and Event Indicators:32, Data Packet Payload Format:64" 

# DIFI Context Packet
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Pckt T.|C|Indi.| T.|TSF|Packet.|          Packet Size          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Stream ID                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Pad  |  Res|                      OUI                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Info Class          |          Packet Class         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Integer Sec Timestamp                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                  Fractional-Seconds Timestamp                 +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Context Indicators                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Reference Point                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                            Bandwidth                          +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                     IF Reference Freqency                     +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                       RF Reference Freq                       +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                         IF Band Offset                        +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Reference Level                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Gain & Attenuation                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                          Sample Rate                          +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                      Timestamp Adjustment                     +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                Timestamp Calibration Time (sec)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   State and Event Indicators                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                   Data Packet Payload Format                  +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

# DIFI Version Packet
# python protocol --no-numbers "Pckt Type:4,C:1,Indicators:3, TSI:2,TSF:2,Seq Num:4,Packet Size:16,Stream ID:32, Pad:5, Res:3,OUI:24,Info Class:16,Packet Class:16, Integer Sec Timestamp:32, Fractional-Seconds Timestamp:64,Context Indicator Field 0:32,Context Indicator Field 1:32, V49 Spec Version:32, Year:7, Day:9, Rev:6,Type:4,ICD Version:6" 

+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Pckt T.|C|Indi.| T.|TSF|Seq Num|          Packet Size          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Stream ID                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Pad  |  Res|                      OUI                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Info Class          |          Packet Class         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Integer Sec Timestamp                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                  Fractional-Seconds Timestamp                 +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Context Indicator Field 0                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Context Indicator Field 1                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        V49 Spec Version                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Year    |        Day      |     Rev   |  Type |ICD Version|
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

# DIFI Data Packet
# python protocol --no-numbers "Pckt Type:4, C:1, Indicators:3, TSI:2, TSF:2, Seq Num:4, Packet Size:16,Stream ID:32, Pad:5, Res:3,OUI:24, Info Class:16, Packet Class:16, Integer Sec Timestamp:32, Fractional-Seconds Timestamp:64, Signal Data Payload Complex 4-16 bit signed N Words:128" 

+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Pckt T.| | Ind.| T.| T.| Seq N.|           Packet Size         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Stream ID                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Pad  |  Res|                      OUI                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Info Class          |          Packet Class         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Integer Sec Timestamp                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                  Fractional-Seconds Timestamp                 +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                                                               |
+       Signal Data Payload Complex 4-16 bit signed N Words     +
|                                                               |
+                                                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+