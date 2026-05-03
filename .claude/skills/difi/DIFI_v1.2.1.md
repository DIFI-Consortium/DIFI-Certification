# DIFI Standard v1.2.1 — AI Reference

## 0. Quick Reference (Lookup Tables)

### 0.1 DIFI Constants

| Constant | Value |
|---|---|
| DIFI Organizationally Unique Identifier (OUI / CID) | `0x6A621E` (canonical: `6A-62-1E`) |
| Class Identifier Indicator (Word 1, bit 27) | Always `1` for DIFI |
| Reserved bits (Word 3, bits 26-24) | Always `0` |
| Word 1 bits 23-22 (TSI) value `00` | Not allowed in DIFI |
| Word 1 bits 21-20 (TSF) value `00` | Not allowed in DIFI |
| Word 1 bits 21-20 (TSF) value `11` (Free Running) | Not used in DIFI |
| Ethernet jumbo frame max | 9000 bytes |
| Min UDP payload (IPv4) overhead | IP 20 + UDP 8 + VITA 28 = 56 octets |
| Min UDP payload (IPv6) overhead | IP 40 + UDP 8 + VITA 28 = 76 octets |

### 0.2 Information Classes (summary)

| Code | Name | First in | Purpose | Packet Classes Used |
|---|---|---|---|---|
| `0x0000` | Basic Data Plane | v1.0 | Convey I/Q data + context (Real-Time TSF) | `0x0000`, `0x0001` |
| `0x0001` | Version Flow | v1.0 | Type/version + time-of-day (legacy sync use) | `0x0004` |
| `0x0002` | Data Plane plus Flow Control | v1.2 | I/Q + context + flow-control sync (Sample Count TSF) | `0x0002`, `0x0003`, `0x0005` |
| `0x0003` | Data Plane plus Flow Control, Real Time TSF | v1.2 | Same as 0x0002 but Real-Time TSF | `0x0000`, `0x0001`, `0x0006` |
| `0x0004` | Basic Data Plane, Sample Count TSF | v1.2.1 | Same as 0x0000 but Sample Count TSF | `0x0002`, `0x0003` |

### 0.3 Packet Classes (summary)

| Code | Name | Type | TSF | Size (words) |
|---|---|---|---|---|
| `0x0000` | Standard Flow Signal Data | Data | Real Time (ps) | 7 + N |
| `0x0001` | Standard Flow Signal Context | Context | Real Time (ps) | 27 |
| `0x0002` | Sample Count Signal Flow Data | Data | Sample Count | 7 + N |
| `0x0003` | Sample Count Signal Flow Context | Context | Sample Count | 27 |
| `0x0004` | Version Flow Signal Context | Context | Real Time (ps) | 11 |
| `0x0005` | Sample Count Timing Flow Control | Command | Sample Count | 21 |
| `0x0006` | Real Time TSF Timing Flow Control | Command | Real Time (ps) | 21 |

### 0.4 Reference Point Codes

| Decimal | Hex | Meaning |
|---|---|---|
| 100 | `0x00000064` | IF Converter analog port (input on Rx, output on Tx) — preferred when device has IF analog interface |
| 75 | `0x0000004B` | RF Converter analog port — preferred when device has RF analog interface |
| 25 | `0x00000019` | Antenna feed — used when Tx/Rx timing is critical (e.g., ranging) |
| 15 | `0x0000000F` | Air interface — for ESAs without single-point RF reference |

---

## 1. Introduction

The data plane interface transmits and receives digitized RF/IF data plus metadata over standard IP networks. Substantially compliant with VITA 49.2 (deviations in §1.5).

### 1.3 DIFI Standard Definitions (Figure 1)

| Term | Definition |
|---|---|
| **DIFI Device** | Any hardware, firmware, or software that creates a Source or Sink using the DIFI protocol |
| **Endpoint** | A Source or a Sink |
| **Flow** | Transmission of data as packets/packet stream from Source to Sink |
| **Full Scale Amplitude** | For an I (Q) sample component with N bits: `2^(N-1) - 1` |
| **Full Scale Complex Sinusoid** | One whose peak magnitude `√(I² + Q²)` equals available full scale amplitude `R` of `I` or `Q` separately (peak magnitude lies on circle of radius R in complex IQ plane) |
| **IF Converter (IFC)** | Device that transmutes signals between digital IF and analog IF |
| **Intermediate Frequency (IF) Signal** | Any signal after frequency translation. Frequency may or may not be a typical IF; a zero-IF signal equals a complex baseband signal |
| **Information Class** | Group of one or more Packet Classes plus packet stream associations defining structure and information exchange between DIFI devices |
| **Information Stream** | Flow of Packet Streams containing signal data, metadata, and/or control |
| **[IP] Socket** | IP address and port number |
| **Link Efficient Packing** | Signal Data Payload packed to maximise Ethernet link efficiency |
| **Packet Class** | Set of rules and structures defining packet format and content |
| **Packet Type** | Type of packet: Data, Context, or Command |
| **Packet Stream** | Flow of packets carrying data Source → Sink |
| **Process Efficient Packing** | Signal Data Payload packed to minimise processing load (at expense of link bandwidth) |
| **Receive (Rx) Direction** | Away from the RF communications aperture or its intended location |
| **Reference Point** | Location from which data is measured/referenced; common baseline for time, frequency, phase parameters |
| **RF Converter (RFC)** | Device that transmutes signals between digital IF and analog RF |
| **Signal Data Packet Sink** | Packet Stream signal destination socket — VITA 49.2 packet "consumer" |
| **Signal Data Packet Source** | Packet Stream signal origination socket — VITA 49.2 packet "emitter" |
| **Stream Identifier (SID)** | Field in DIFI header that (i) groups packets of same type/Stream ID into a sequence, (ii) associates Context/Command streams with Data streams, (iii) defines the SID location used with timestamping |
| **Transmit (Tx) Direction** | Towards the RF communications aperture or its intended location |

### 1.4 Abbreviations & Acronyms

| Abbr | Meaning |
|---|---|
| ADC | Analog to Digital Converter |
| ARP | Address Resolution Protocol |
| CIF | Control Indicator Field |
| DAC | Digital to Analog Converter |
| dBFS | Decibels Full Scale (full-scale sinusoid = 0 dBFS) |
| DIFI | Digital Intermediate Frequency Interoperability |
| FPGA | Field-Programmable Gate Array |
| GPS | Global Positioning System |
| I | In-phase component |
| ICD | Interface Control Document |
| ID | Identifier |
| IEEE ISTO | IEEE Industry Standards and Technology Organization |
| IF | Intermediate Frequency |
| IFC | IF Converter |
| IP | Internet Protocol |
| IPv4 / IPv6 | Internet Protocol v4 / v6 |
| IRIG | Inter-range Instrumentation Group |
| LAN | Local Area Network |
| MAC | Media Access Control |
| Msps | Mega-samples per second |
| NIC | Network Interface Controller |
| NTP | Network Time Protocol |
| NTR | Non-Time Release |
| OUI | Organizationally Unique Identifier |
| POSIX | Portable Operating System Interface |
| PTP | Precision Time Protocol |
| Q | Quadrature component |
| RF | Radio Frequency |
| TC | Time Continuous |
| TOD | Time of Day |
| TSF | Timestamp Fractional |
| TSI | Timestamp Integer |
| TSM | Timestamp Mode |
| UDP | User Datagram Protocol |
| UTC | Coordinated Universal Time |
| VLAN | Virtual LAN |
| VRL | VITA Radio Link Protocol |
| VRT | VITA Radio Transport |

---

## 2. Data Plane Implementation

The data plane is where digital RF/IF data and corresponding metadata are formed into packets for transmission. DIFI defines two independent data plane flows:

1. **Receive:** RF/IF input → IP-network output
2. **Transmit:** IP-network input → RF/IF output

VITA 49.2 trailers and VRL framing are NOT used for any DIFI flows.

### 2.1 Protocol Overview

DIFI supports three packet types:
1. **Context Packets** — metadata
2. **Signal Data Packets** — IQ samples
3. **Command Packets** — control & timing (Control + Acknowledge sub-types; only Control used in v1.2.1)

DIFI protocol stack (top → bottom):
```
DIFI Application
DIFI Protocol Layer (Command / Context / Signal Data Packet)
User Datagram Protocol (UDP)
IPv4 | IPv6
Ethernet
```

### 2.2 Ethernet Requirements

- DIFI packets MUST be in standard 802.3 Ethernet frames
- MUST support jumbo frames with MTU 9000 bytes
- MUST support 802.1Q (VLAN) and 802.1ad (QinQ)
- A DIFI endpoint MUST have at least one Ethernet MAC address
- Fixed Ethernet overhead per packet:
  - IP header: 20 octets (IPv4) / ≥ 40 octets (IPv6)
  - UDP header: 8 octets
  - VITA header: 28 octets
- Ethernet frame payload: 128–9000 octets

### 2.3 IP Requirements

- DIFI packets MUST be in standard IPv4 (RFC 791) or IPv6 (RFC 8200) frames
- For a given DIFI stream, source IP address MUST be the same for context and data packets
- IPv4 fragmentation MUST NOT be produced at source; sink MAY discard fragmented packets
- DIFI MUST support IPv6 extension headers; implementations MAY ignore content of extension headers but MUST process the IPv6 payload regardless

### 2.4 UDP Requirements

- Each DIFI packet MUST be in a standard UDP datagram
- UDP checksums: mandatory for IPv6, optional for IPv4 (DIFI imposes no further requirement); if used, MUST be valid for the packet transport type
- UDP datagram payload contains exactly one of: DIFI context, DIFI control, or DIFI data packet

---

## 3. Information Classes

An **Information Stream** conveys user information from one point to another. It is a collection of Packet Streams (each with a single Stream ID). The structure is defined by an **Information Class**.

A DIFI Information Class consists of one or more Packet Classes. Packet Streams in an Information Stream share the same Stream Identifier.

The eight components of an Information Class:
1. Class Name and Code
2. Information Stream Purpose
3. Names of included VRT Packet Streams
4. Purpose of each included Packet Stream
5. Packet Classes
6. Packet Stream Details
7. Reference Points
8. Packet Stream Associations

### 3.1 Information Class `0x0000` — Basic Data Plane

| Component | Specification |
|---|---|
| Name / Code | "Basic Data Plane" / `0x0000` |
| Stream Purpose | Convey digitized I and Q samples; control/reference config conveyed in advance or via non-VRT streams |
| Packet Stream Names | 1. Signal Data; 2. Signal Context |
| Packet Stream Purposes | 1. Convey I/Q samples; 2. Convey data stream context |
| Packet Classes | 1. Standard Flow Signal Data (`0x0000`); 2. Standard Flow Signal Context (`0x0001`) |
| Packet Stream Details | Data packet size unrestricted, subject to: link-efficient packing (bit padding NOT permitted in Class 0); max Ethernet packet size 9000 bytes. Context packets required, issued on field change OR user periodicity (whichever first) |
| Reference Points | Tx: analog output of conversion device (default); Rx: analog input. IF analog interface: default ref 100 (`0x0064`). RF analog interface: default ref 75 (`0x004B`) |
| Packet Stream Associations | Signal Context ↔ Signal Data |

The Basic Data Plane is the original DIFI Information Class. Uses Real Time (picoseconds) for Fractional Seconds Timestamp. Contains data + metadata only — no Command Packet Stream.

### 3.2 Information Class `0x0001` — Version Flow

| Component | Specification |
|---|---|
| Name / Code | "Version Flow" / `0x0001` |
| Stream Purpose | Convey type/version info and precise time-of-day for software synchronization |
| Packet Stream Names | 1. Version Flow Signal Context Packet |
| Packet Stream Purposes | 1. Convey type/version; 2. Convey time-of-day |
| Packet Classes | 1. Version Flow Signal Context (`0x0004`) |
| Packet Stream Details | Packet size = 11 words. Does not use data packets. Context packets may be issued at any rate from 0 (off) to 100 packets/sec |
| Reference Points | Reference Point field NOT included; reference is to the SID |
| Packet Stream Associations | No associations |

Use of `0x0001` for timing purposes is **legacy**. Applications requiring a DIFI Sink to emit timestamped packets for synchronization SHOULD use `0x0002` or `0x0003`.

### 3.3 Information Class `0x0002` — Data Plane plus Flow Control

| Component | Specification |
|---|---|
| Name / Code | "Data Plane plus Flow Control" / `0x0002` |
| Stream Purpose | Convey I/Q samples (Tx or Rx) plus Flow Control Command Packets conveying timing for sink-master-Sample-Rate configurations |
| Packet Stream Names | 1. Signal Data; 2. Signal Context; 3. Timing Flow Control |
| Packet Stream Purposes | 1. I/Q samples; 2. Data stream context; 3. Timing for source to sync to sink sample rate |
| Packet Classes | 1. Sample Count Signal Data (`0x0002`); 2. Sample Count Signal Context (`0x0003`); 3. Sample Count Timing Flow Control (`0x0005`) |
| Packet Stream Details | Bit padding permitted on final word in payload. Flow Control Packets at uniform user-determined rate, ≤ 1000/sec |
| Reference Points | Same defaults as `0x0000` |
| Associations | Signal Context ↔ Signal Data; Timing Flow Command ↔ Signal Data |

Provides full sample-rate / timestamp synchronization between Source and Sink beyond what `0x0000` provides. Uses Command Packets which can be emitted by a Packet Stream Sink (sharing Stream ID with the Data Packet Stream from another device). Command Packets have two sub-types: **Control** and **Acknowledge** — `0x0002` does NOT use Acknowledge. Any device may emit Control Packets ("Controller"); any device(s) may consume them ("Controllee").

### 3.4 Information Class `0x0003` — Data Plane plus Flow Control, Real Time TSF

| Component | Specification |
|---|---|
| Name / Code | "Data Plane plus Flow Control packets, Real Time TSF" / `0x0003` |
| Packet Classes | 1. Standard Flow Signal Data (`0x0000`); 2. Standard Flow Signal Context (`0x0001`); 3. Real Time TSF Timing Flow Control (`0x0006`) |

Identical to `0x0002` except uses **Real Time (picoseconds)** for Fractional Seconds Timestamp instead of Sample Count.

### 3.5 Information Class `0x0004` — Basic Data Plane, Sample Count TSF

| Component | Specification |
|---|---|
| Name / Code | "Basic Data Plane" (Sample Count TSF) / `0x0004` |
| Packet Classes | 1. Sample Count Signal Data (`0x0002`); 2. Sample Count Signal Context (`0x0003`) |

Identical to `0x0000` except uses **Sample Count** for Fractional Seconds Timestamp instead of Real Time (picoseconds).

---

## 4. Packet Classes

DIFI defines three Packet Types:
- **Data Packets** — standardize signal data transport
- **Context Packets** — standardize transport of metadata (sample rate, bit depth, etc.)
- **Command Packets** — Control + Acknowledge subtypes; provide and acknowledge device settings, support timing control

### 4.1 DIFI Packet Prologue (common to all packet types)

All DIFI packets contain a prologue (Words 1–7) followed by a payload. Prologue structure is nearly identical across types.

#### Prologue word layout

| Word | Contents |
|---|---|
| 1 | Packet Header |
| 2 | Stream Identifier (SID) |
| 3 | Class Identifier — Pad Bit Count, Reserved, OUI |
| 4 | Class Identifier — Information Class Code, Packet Class Code |
| 5 | Integer-Seconds Timestamp |
| 6, 7 | Fractional-Seconds Timestamp (64-bit) |

#### Word 1: Packet Header bit-fields

| Bits | Field | Notes |
|---|---|---|
| 31–28 | Packet Type | DIFI uses `0x1` (Data + SID), `0x4` (Context), `0x6` (Command). See Table 4-4 |
| 27 | Class Identifier Indicator | MUST be `1` for DIFI |
| 26–24 | Packet-type-dependent | See per-class sections |
| 23–22 | Timestamp Integer (TSI) | See Table 4-5 |
| 21–20 | Timestamp Fractional (TSF) | See Table 4-6 |
| 19–16 | SeqNum | 4-bit, mod-16 incremented per successive packet in each Packet Stream (Context and Data each have separate sequences) |
| 15–0 | Packet Size | Total 32-bit words (header + payload), excluding UDP encapsulation |

#### Table 4-4 — Packet Type Codes

| Code | Meaning | DIFI uses |
|---|---|---|
| `0x0` | Signal Data Packet without Stream Identifier | No |
| `0x1` | Signal Data Packet with Stream Identifier | **Yes** |
| `0x2` | Extension Data Packet without Stream Identifier | No |
| `0x3` | Extension Data Packet with Stream Identifier | No |
| `0x4` | Context Packet | **Yes** |
| `0x5` | Extension Context packet | No |
| `0x6` | Command Packet | **Yes** |
| `0x7` | Extension Command Packet | No |
| `0x8`–`0xF` | Reserved | No |

#### Table 4-5 — TSI Codes

| Code | Meaning |
|---|---|
| `00` | NOT ALLOWED in DIFI (would mean Integer Seconds omitted) |
| `01` | UTC — epoch Jan 1 1970, includes leap seconds |
| `10` | GPS — epoch Jan 6 1980, no leap seconds |
| `11` | POSIX — epoch Jan 1 1970, no leap seconds |

#### Table 4-6 — TSF Codes

| Code | Meaning | Used by Packet Classes |
|---|---|---|
| `00` | NOT ALLOWED in DIFI (would mean Fractional Seconds omitted) | — |
| `01` | Sample Count Timestamp | `0x0002`, `0x0003`, `0x0005` |
| `10` | Real Time (Picoseconds) Timestamp | `0x0000`, `0x0001`, `0x0004`, `0x0006` |
| `11` | Free Running Count Timestamp | NOT USED in DIFI |

#### Word 2: Stream ID (SID)

- Defaults to `0` if unused; any unsigned 32-bit value otherwise
- Settable before or at run time
- Associated Data + Context + Command streams share Stream IDs
- SID location MUST be documented; per DIFI it shall be at the digital interface of the IFC/RFC: point of generation of samples out of ADC (Rx path) or point of consumption of samples within DAC (Tx path)
- For systems with intermediate digital-in/digital-out devices (e.g., combiner/splitter), Tx-direction SIDs should be at the downstream end of the digital link (the point where samples are consumed)

See §5.1 and VITA 49.2 §5.1.2.

#### Words 3 & 4: Class Identifier

| Bits | Field | Value |
|---|---|---|
| W3, 31–27 | Pad Bit Count | Unsigned 5-bit integer, 0–31, count of non-data pad bits in final data-payload word. Set to 0 in Context/Command packets (no payload). For Data: see Table 4-12 |
| W3, 26–24 | Reserved | Always `0` (VITA 49.2 Rule 5.1.3-5) |
| W3, 23–0 | OUI | Always `0x6A621E` (DIFI CID) |
| W4, 31–16 | Information Class Code | See §3 / Table 3-1 |
| W4, 15–0 | Packet Class Code | See Table 4-7 |

The hierarchy is: **Stream → Information Class → Packet Class**.

#### Table 4-7 — Packet Class Codes

| Code | Meaning |
|---|---|
| `0x0000` | Standard Flow Signal Data |
| `0x0001` | Standard Flow Signal Context |
| `0x0002` | Sample Count Signal Flow Data |
| `0x0003` | Sample Count Signal Flow Context |
| `0x0004` | Version Flow Signal Context |
| `0x0005` | Sample Count Timing Flow Control |
| `0x0006` | Real Time TSF Timing Flow Control |

#### Word 5: Integer-Seconds Timestamp

- Seconds since epoch for selected TSI reference (UTC/GPS/POSIX)
- Only UTC includes leap seconds
- For Sample Count TSF Packet Classes: incremented each time Fractional Timestamp reaches the Sample Rate value (nominally once per second)
- See VITA 49.2 §5.1.4–5.1.5

#### Words 6 & 7: Fractional-Seconds Timestamp

- 64-bit unsigned integer
- For Real Time TSF Classes: number of picoseconds since most recent increment/reset of Integer-Seconds Timestamp
- For Sample Count TSF Classes: number of sample counts since most recent increment/reset of Integer-Seconds Timestamp
- Reset to 0 whenever Integer Seconds is incremented or reset

---

### 4.2 Data Packet Classes (`0x0000`, `0x0002`)

Both classes are nearly identical; differ only in TSF (Real Time ps for `0x0000`, Sample Count for `0x0002`) and bit-padding rules.

#### Common conventions

- Header per §4.1
- SID location: Rx — point of generation of digital samples; Tx — point of consumption of digital samples (see §5.1)

#### Table 4-9 — Data Packet Class Content (key parameters)

| Parameter | Class `0x0000` | Class `0x0002` |
|---|---|---|
| Packet Type | Signal Data Packet with Stream ID | (same) |
| Packet Size | Variable (7 prologue + N data) | (same) |
| Stream Identifier | Yes, runtime-selected | (same) |
| Class ID | Present (W3: Pad+OUI; W4: Info Class + Packet Class) | (same) |
| Integer-Seconds TS | UTC/POSIX/GPS per Header | Routinely incremented when Fractional reaches Sample Rate count |
| Fractional Seconds TS | Real time, picoseconds | Sample Count |
| Packing | Link Efficient | (same) |
| Data Item Size | Variable, user-selected | I/Q components: 4–16 bits each (pairs 8–32 bits) |
| Packing Field Size | = Data Item Size | (same) |
| Real/Complex Type | Complex Cartesian | (same) |
| Data Item Format | Signed integer (V49.2 Signed Fixed-Point code `00000`, no fractional component) | (same) |
| Sample/Channel repeating | None | None |
| Repeat Count | 0 | 0 |
| Packet Trailer | Not used | Not used |

#### Data Packet Format (Word layout)

| Word | Contents | Notes |
|---|---|---|
| 1 | Packet Header (Type=`0x1`, ...) | See bit-field table below |
| 2 | Stream Identifier | Run-time |
| 3 | Pad Bit Count + Reserved + 24-bit DIFI CID `0x6A621E` | |
| 4 | Information Class Code + Packet Class Code | |
| 5 | Integer Seconds Timestamp (per TSI) | |
| 6 | Fractional Seconds Timestamp (per TSF, MSW) | |
| 7 | Fractional Seconds Timestamp (per TSF, LSW) | |
| 8 … N+7 | Signal Data Payload | Complex Cartesian, signed integers, 4–16 bits, link-efficient packing |

Total Packet Size = N + 7 words.

#### Word 1 details for Data Packets

| Bits | Field | Value |
|---|---|---|
| 31–28 | Packet Type | `0x1` (Data with SID) |
| 27 | Class Identifier | `1` |
| 26 | Trailer Indicator | `0` (no trailer) |
| 25 | VITA 49.0 Indicator | `0` |
| 24 | VITA 49.2 Spectrum/Time | `0x0` (time data; spectrum unsupported, per VITA 49.2 Rule 6.3.1-2) |
| 23–22 | TSI | (see Table 4-5) |
| 21–20 | TSF | `0x2` for Class `0x0000`; `0x1` for Class `0x0002` |
| 19–16 | SeqNum | Mod-16 incremented |
| 15–0 | Packet Size | 7 + N words |

#### Sample padding (Class `0x0000` in Information Class `0x0000` only)

When Class `0x0000` is used in Information Class `0x0000`, **no bit padding** allowed — every packet contains an integer number of I/Q pairs, and pairs (each `2 × sample-depth` bits) must fit into a whole number of 32-bit units.

#### Table 4-11 — Sample Padding (sample/word granularity)

For each `bits per sample`, every value is whole:
`2 × <bits per sample> × <sample count granularity> = 32 × <32-bit unit granularity>`

| bits per sample | sample count granularity | 32-bit unit granularity |
|---|---|---|
| 4 | 4 | 1 |
| 5 | 16 | 5 |
| 6 | 8 | 3 |
| 7 | 16 | 7 |
| 8 | 2 | 1 |
| 9 | 16 | 9 |
| 10 | 8 | 5 |
| 11 | 16 | 11 |
| 12 | 4 | 3 |
| 13 | 16 | 13 |
| 14 | 8 | 7 |
| 15 | 16 | 15 |
| 16 | 1 | 1 |

Examples:
- 5-bit samples → 10-bit complex pairs → 16 samples = 5 × 32 bits = 160 bits (any multiple of 16 samples is legal)
- 6-bit samples → 12-bit pairs → 8 samples = 3 × 32 = 96 bits
- 7-bit samples → 14-bit pairs → 16 samples = 7 × 32 = 224 bits

#### Table 4-12 — Bit Padding Permission

| Information Class | Data Packet Class | Bit Padding Permitted |
|---|---|---|
| `0x0000` | `0x0000` | **No** |
| `0x0002` | `0x0002` | Yes |
| `0x0003` | `0x0000` | Yes |

(`0x0004` uses Data Packet Class `0x0002` and follows Sample Count rules.)

#### Words 8 to N+7 — Data Payload

- Complex Cartesian; each sample pair is I (in-phase) followed by Q (quadrature), left-to-right
- Signed integer format; bit depth specified by the **Data Packet Payload Format Field** in the associated Context Packet
- "Link-efficient" packing: pairs packed with no padding bits between them; samples may wrap from one 32-bit word to next
- Bit padding 0–31 bits permitted at end of final 32-bit word **except** when Class `0x0000` is used in Information Class `0x0000`
- Unless otherwise stated in the Packet Class Documentation, the timestamp field values indicate the time the **first** data sample in the data payload is present at the SID location. Relationship to Reference Point and Timestamp Adjustment described in §5.1 and §5.2.

---

### 4.3 Context Packet Classes (`0x0001`, `0x0003`, `0x0004`)

Context Packets provide metadata permitting interpretation of Data Packet payloads (e.g., bit depth, sample rate, frequency, level).

While VITA 49.2 has Command Packets, for backward compatibility with extant equipment, Standard Flow Signal Context Packets MAY be used as a pseudo-control emitted by the signal data stream emitter. Acting on these in real time depends on application and out-of-band management beyond this Standard.

#### Common conventions

- All frequency / sample rate fields in Hz
- VITA 49.2 64-bit two's-complement format with radix point right of bit 20 in second 32-bit word (Figure 8). DIFI requires integer Hz values — all bits right of radix point set to 0
- SID location for Context Packets matches associated Data Packet Stream

#### Table 4-13 — Class Headlines

| Class | Code | Name | Stream Purpose |
|---|---|---|---|
| `0x0001` | Standard Flow Signal Context | Convey context for paired DIFI IQ Data Stream (paired by SID) |
| `0x0003` | Sample Count Signal Context | (same as `0x0001` but Sample Count TSF) |
| `0x0004` | Version Flow Signal Context Packet | Convey type/version + precise time-of-day for software apps |

#### Table 4-14 — Context Packet Class Content

| Parameter | `0x0001` | `0x0003` | `0x0004` |
|---|---|---|---|
| Packet Type | Context Packet w/ SID | (same) | (same; SID defined by emitter, may be unrelated to signal-data Stream SID) |
| Packet Size | 27 words | 27 words | 11 words |
| Stream Identifier | Yes (matches paired Data Stream SID) | (same) | (independent SID) |
| Class ID | Present | Present | Present |
| Integer Seconds TS | Present | Present (incremented at sample-rate) | Present |
| Fractional Seconds TS | Real Time ps | Sample Count | Real Time ps |
| CIF 0 | Present | Present | Present |
| CIF 1 | Not Present | Not Present | **Present** |
| VITA 49 Version | Not Present | Not Present | Present |
| Year/Day/Revision/Type/ICD Version | Not Present | Not Present | Present |
| Reference Point Identifier | Present | Present | Not present |
| Bandwidth | Present | Present | Not Present |
| IF Reference Frequency | Present | Present | Not present |
| RF Reference Frequency | Present | Present | Not present |
| IF Band Offset | Present | Present | Not present |
| Scaling Level (in Reference Level word) | Present | Present | Not present |
| Reference Level | Present | Present | Not present |
| Gain (Gain1, Gain2 reserved 0x0000) | Present | Present | Not present |
| Sample Rate | Present | Present | Not present |
| Timestamp Adjustment | Present | Present | Not present |
| Timestamp Calibration | Present | Present | Not present |
| State and Event Indicators | Present | Present | Not present |
| Data Packet Payload Format | Present | Present | Not present |
| Data Item Format | Signed integer | Signed integer | Not present |
| Packet Trailer | Not present | Not present | Not present |

#### 4.3.1 Signal Context Packets — Format (Classes `0x0001` and `0x0003`)

Table 4-15 layout (27 words):

| Word | Contents |
|---|---|
| 1 | Packet Header |
| 2 | Stream Identifier |
| 3 | Pad Bit Count (=0) + Reserved + 24-bit DIFI CID |
| 4 | Information Class Code + Packet Class Code |
| 5 | Integer Seconds Timestamp |
| 6, 7 | Fractional Seconds Timestamp |
| 8 | Context Indicator Field (CIF 0) |
| 9 | Reference Point |
| 10, 11 | Bandwidth |
| 12, 13 | IF Reference Frequency |
| 14, 15 | RF Reference Frequency |
| 16, 17 | IF Band Offset |
| 18 | Scaling (bits 31–16) + Reference Level (bits 15–0) |
| 19 | Gain 2 (bits 31–16) + Gain 1 (bits 15–0) |
| 20, 21 | Sample Rate |
| 22, 23 | Timestamp Adjustment |
| 24 | Timestamp Calibration Time |
| 25 | State and Event Indicators |
| 26, 27 | Data Packet Payload Format |

##### Word 1 — Header bit fields for `0x0001` / `0x0003`

| Bits | Field | Value |
|---|---|---|
| 31–28 | Packet Type | `0x4` (Context with SID) |
| 27 | Class ID Indicator | `1` |
| 26–25 | Reserved | `0x0` |
| 24 | TSM (Timestamp Mode) | See Table 4-16 |
| 23–22 | TSI | per §4.1 |
| 21–20 | TSF | `0x2` (Real Time ps) for `0x0001`; `0x1` (Sample Count) for `0x0003` |
| 19–16 | SeqNum | mod-16 |
| 15–0 | Packet Size | `27` |

##### Table 4-16 — TSM values

| Information Class | Timestamp Mode |
|---|---|
| `0x0000` | Coarse (TSM = 1) |
| `0x0003` | Fine (TSM = 0) |

For Packet Class `0x0003`, TSM = `0` → precise timing.

##### Word 8 — CIF 0 (Context Indicator Field 0)

- Bit 31: change indicator. Set = new info; clear = no change
- Other bits indicate which Context fields are present in the packet
- Bits 1, 2, 3 set → CIF 1, 2, 3 word(s) included, respectively

For Classes `0x0001` and `0x0003`, only specific values are valid (Figure 9):
- `0xFBB98000` — change in any context value
- `0x7BB98000` — no change

##### Word 9 — Reference Point Field

Allowed values:
- `100` (`0x00000064`) — IF Converter analog port (input on Rx, output on Tx)
- `75` (`0x0000004B`) — RF Converter analog port (input on Rx, output on Tx)
- `25` (`0x00000019`) — Antenna feed (when Tx/Rx timing is critical, e.g., ranging)
- `15` (`0x0000000F`) — Air interface (active electronically scanned arrays)

##### Words 10 & 11 — Bandwidth

- Useable bandwidth of digitized signal
- 1 Hz increments
- See VITA 49.2 §9.5.1

##### Words 12 & 13 — IF Reference Frequency

- For systems with accessible analog IF: sampling center frequency for IF conversion
- For systems with RF in/out and no accessible IF: `0x00000000` at source; sink ignores
- Use determined by Reference Point field
- Defaults to `0` for zero-IF architectures
- See VITA 49.2 §9.5.5

##### Words 14 & 15 — RF Reference Frequency

- For systems with analog IF: intended RF center frequency realized through analog conversion
- For systems with direct RF conversion only: sampling center frequency for direct RF
- Use determined by Reference Point field
- For Class `0x0003`: RF center freq on RF input (Rx) or RF output (Tx). Tx RF reference frequency is **status only** — output center frequency is independently programmed (allowing frequency translation)
- See VITA 49.2 §9.5.10

##### Words 16 & 17 — IF Band Offset

- Stream offset from IF center frequency of digitized signal; default 0 Hz
- IF center frequency is always 0 Hz for zero-IF
- Signed, 1 Hz resolution
- Settable anywhere within system bandwidth so long as no portion of stream bandwidth extends beyond system bandwidth edges
- IF Band Offset = Stream Offset for Rx direction; default Stream Offset for Tx (overridable)
- See VITA 49.2 §9.5.4

##### Word 18 — Reference Level (composed of Scaling + Reference Level)

- See VITA 49.2 §9.5.9 and §B.6

**Bits 31–16 — Scaling Level (optional, Tx only):**
- Describes scaling applied to digital signal representation to prevent overflow of 4–16 bit signal sample words
- Default `0x0000` when unused
- When used: dBFS value of a sine wave with same average power as the signal in the data payload

**Bits 15–0 — Reference Level (mandatory):**
- Relates physical analog signal amplitude at Reference Point to data samples in associated Signal Data packet
- Rx: power level in dBm incident at Reference Point — AC power of a single sine wave at Reference Point producing a full-scale digitized sine wave in paired Data Packet payload
- Tx: power level in dBm intended at Reference Point in response to a full-scale digital sine wave in Data Payload
- For ESA using air interface (Reference Point 15): describes intended EIRP in dBm on boresight
- **Observation 4.2.1-1:** ESA gain depends on pointing angles; ESA must dynamically account for pointing-angle and frequency effects in DAC-output → EIRP relationship to realize Reference Level

##### Word 19 — Gain/Attenuation

- Gain 1 (bits 15–0) + Gain 2 (bits 31–16); 16-bit each, reserved
- Source populates with `0x0000`; sink ignores
- Usage per previous DIFI revisions allowed but Reference Level often more useful; interoperability is vendor responsibility
- See VITA 49.2 §9.5.3, §B.7

##### Words 20 & 21 — Sample Rate

- Sampling rate of samples in Signal Data packets
- For interoperability, see external Sample Rate Vendor Interoperability area on DIFI website
- See VITA 49.2 §9.5.12

##### Words 22 & 23 — Timestamp Adjustment

- 64-bit two's-complement value in **femtoseconds**
- Signal delay between Reference Point and SID location
- Tx: generally positive; Rx: generally negative
- See §5.2

##### Word 24 — Timestamp Calibration Time

- Last time the timestamp was known to be correct
- Populated on Tx side for applications requiring knowledge of when timing signal was last locked
- See VITA 49.2 §9.7.3.3

##### Word 25 — State and Event Indicators

- Conveys state of:
  - Calibrated time reference lock (bit 19) — IRIG-B, IRIG-DC, 1PPS, NTP, GPS
  - Frequency reference lock (bit 17) — 10 MHz, IRIG-B, IRIG-DC, 1PPS, GPS
- Lock statuses updated about once/sec in RF→IP direction
- Tx side uses these to determine if Programmed Delay mode possible and if it can measure end-to-end latency / Network Delay
- Measured/Network Delays set to 0 if calibrated time (bit 19) not locked on RF→IP side
- See VITA 49.2 §9.10.8

##### Words 26 & 27 — Data Packet Payload Format

Required to interpret samples in Signal Data packets.

Word 26 fields (Figure 10):

| Bits | Field | Value |
|---|---|---|
| 31 | Packing Method | `1` (Link Efficient) |
| 30–29 | Real-Complex Data Type | `01` (Complex Cartesian) |
| 28–24 | Data Item Format | `00000` (Signed Fixed Point) |
| 23 | Sample Component Repeat Indicator | `0` (No repeat) |
| 22–20 | Event Tag Size | `000` (No events) |
| 19–17 | Channel Tag Size | `000` |
| 16–12 | Data Item Fraction Size | `0000` |
| 11–6 | Data Item Size | `(# bits per I or Q) − 1` (3–15) |
| 5–0 | Item Packing Field Size | `(# bits per I or Q) − 1` (3–15) |

Word 27: Repeat Count (16 MSBs) + Vector Size (16 LSBs) — both `0`.

Bit depth user-determined; all other sub-field values fixed by this Standard. See VITA 49.2 §9.13.3.

##### Packet Rate

- Standard Flow Signal Context Packet rate: 0 (off) through 20 packets/sec for any stream config
- Standard Flow Signal Context Packet transmission required upon any signal-context-packet field change

#### 4.3.2 Packet Class `0x0004` — Version Flow Signal Context

Conveys type and version information plus precise time-of-day for software applications.

Created on the receive side and used by the transmit side to auto-select compatible packet format. May optionally be used on transmit flow when appropriate.

Table 4-17 layout (11 words):

| Word | Contents |
|---|---|
| 1 | Packet Header |
| 2 | Stream Identifier |
| 3 | Pad Bit Count (=0) + Reserved + 24-bit DIFI CID |
| 4 | Information Class Code + Packet Class Code (`0x0004`) |
| 5 | Integer Seconds Timestamp |
| 6, 7 | Fractional Seconds Timestamp |
| 8 | CIF 0 |
| 9 | CIF 1 |
| 10 | V49 Spec Version Word |
| 11 | Year/Day/Revision/Type/ICD Version Word |

##### Word 1 fields for `0x0004`

| Bits | Field | Value |
|---|---|---|
| 31–28 | Packet Type | `0x4` |
| 27 | Class ID Indicator | `1` |
| 26–25 | Reserved | `0x0` |
| 24 | TSM | `1` (coarse) |
| 23–22 | TSI | per §4.1 |
| 21–20 | TSF | `0x2` (Real Time ps) |
| 19–16 | SeqNum | mod-16 |
| 15–0 | Packet Size | `11` |

##### Word 8 — CIF 0 for `0x0004` (Figure 11)

| Value | Meaning |
|---|---|
| `0x80000002` | Change in any context value |
| `0x00000002` | No change |

##### Word 9 — CIF 1 = `0x0000000C`

Indicates V49 Spec Version Word (bit 3) and Year/Day/Revision/Type/ICD Version Word (bit 2) are present.

##### Word 10 — V49 Spec Version

V49 version MUST be `0x4` (VITA 49.2). Receive side uses version info to auto-configure to a compatible mode if possible.

##### Word 11 — Year / Day / Revision / Type / ICD Version

| Bits | Field | Description |
|---|---|---|
| 31–25 | Year | Years since 2000 (compiled date) |
| 24–16 | Day | Day-of-year (1 = Jan 1) |
| 15–10 | Revision | Same year+day version counter (normally 1) |
| 9–6 | Type | Device type (0–15); SHALL be `0x0` (currently undefined) |
| 5–0 | ICD Version | DIFI data plane standard version (Table 4-18) |

##### Table 4-18 — Version Codes

| Code | Meaning |
|---|---|
| `0` | Version 1 corresponds to DIFI v1.x |
| `1`–`31` | Reserved |

---

### 4.4 Command Packet Classes (`0x0005`, `0x0006`)

VITA 49.2 Command Packet Type has two sub-types:
- **Control Packets**
- **Acknowledge Packets**

DIFI v1.2.1 uses **only Control Packets**.

DIFI Command Packet Classes:
- `0x0005` Sample Count Timing Flow Control
- `0x0006` Real Time TSF Timing Flow Control

Both are intended for synchronization of DIFI sources and sinks.

#### Table 4-20 — Timing Flow Control Packet Classes (`0x0005` / `0x0006`)

| Field | Value |
|---|---|
| **Header** | |
| Packet Type | Control Packet with Stream ID |
| Packet Size | 21 words |
| Stream Identifier | Yes — matches SID for paired Data Stream |
| Class ID | Present, OUI = `0x6A621E`, Packet Class = `0x0005` or `0x0006` |
| Integer-Seconds TS | Present (incremented when fractional reaches Sample Rate) |
| Fractional-Seconds TS | `0x0005`: Sample Count; `0x0006`: Real Time (picoseconds) |
| **Context Fields** | |
| CAM Field | Present |
| Message ID | Present, sequentially assigned by Controller |
| Controllee ID | Pre-assigned per device |
| Controller ID | Pre-assigned per device |
| CIF 0 | Indicates presence of Reference Point, Timestamp Adjustment, CIF1 |
| CIF 1 | Indicates presence of Buffer Size (3-word) Field |
| Reference Point | Present (defaults same as Context Packet) |
| Sample Rate | 64-bit, Hz, integer-only; same format as Context Packet |
| Timestamp Adjustment | 64-bit signed, femtoseconds, RP ↔ SID delay |
| Buffer Size | 64-bit unsigned int, bytes |
| Buffer Level / Buffer Status | Bit fields below |

#### Buffer Level / Buffer Status (Word 21)

| Bits | Field |
|---|---|
| 31–16 | Reserved |
| 15–8 | Buffer Level (8 MSBs of 12-bit fill level) |
| 7–4 | Buffer Status — top 4 bits extend Buffer Level to 12 bits |
| 3 | Buffer Overflow (OF) — set if overflow during current interval |
| 2 | Nearly Full (NF) — set if Buffer Level > nearly-full threshold during interval |
| 1 | Nearly Empty (NE) — set if Buffer Level < nearly-empty threshold during interval |
| 0 | Buffer Underflow (UF) — set if underflow during interval |

"Current interval" = between issuance of previous and present Flow Control Packet.

12-bit fill: `0xFFF` = full, `0x000` = empty; intermediate values proportional. Method of averaging (rolling, exponential, etc.) is implementation-defined. For Information Class `0x0002`, NF/NE thresholds are pre-assigned or set by non-VRT means.

#### Table 4-21 — Timing Flow Control Packet Format (21 words)

| Word | Contents |
|---|---|
| 1 | Packet Header |
| 2 | Stream Identifier |
| 3 | Class Identifier (Pad=0, OUI) |
| 4 | Information Class + Packet Class |
| 5 | Integer Seconds Timestamp |
| 6, 7 | Fractional Seconds Timestamp |
| 8 | Control/Ack Mode (CAM) Field |
| 9 | Message ID |
| 10 | Controllee Identifier (default `0x00000000` if unused) |
| 11 | Controller Identifier (default `0x00000000` if unused) |
| 12 | CIF 0 |
| 13 | CIF 1 |
| 14 | Reference Point (default `0x00000064`) |
| 15, 16 | Sample Rate |
| 17, 18 | Timestamp Adjustment (femtoseconds) |
| 19, 20 | Buffer Size |
| 21 | Reserved + Buffer Fill + Buffer Status (OF/NF/NE/UF) |

##### Word 1 — Header for `0x0005` / `0x0006`

| Bits | Field | Value |
|---|---|---|
| 31–28 | Packet Type | `0x6` (Command with SID) |
| 27 | Class Identifier | `1` |
| 26–24 | Control vs Ack | `0x0` (Command, not cancellation) |
| 23–22 | TSI | per §4.1 |
| 21–20 | TSF | `0x1` (Sample Count) for `0x0005`; `0x2` (Real Time ps) for `0x0006` |
| 19–16 | SeqNum | mod-16 |
| 15–0 | Packet Size | `21` |

##### Word 8 — CAM Field (Table 4-22)

For Control Packets in Timing Flow Control:

| Bits | Field | Value |
|---|---|---|
| 31 | Controllee ID Indicator | `1` (include Controllee ID) |
| 30 | Controllee ID Format | `0` (32-bit) |
| 29 | Controller ID Indicator | `1` (include Controller ID) |
| 28 | Controller ID Format | `0` (32-bit) |
| 27 | Partial Packet Implementation | `0` (unused) |
| 26 | Warnings | `0` (unused) |
| 25 | Errors | `0` (unused) |
| 24–23 | Action Mode | `10` (`0x2`, "execute") |
| 22–15 | Various unused | `0` |
| 14–12 | Timestamp Control Mode | `0x0` (no execution time-frame; Flow Control conveys timing only) |
| 11–8 | Acknowledge Bits | `0` (Control packet only) |
| 7–0 | Reserved | `0` |

##### Word 9 — Message ID

Each Timing Flow Control Packet for any Stream ID is issued with a unique sequential 32-bit Message ID.

##### Words 10, 11 — Controllee/Controller IDs

- Distinct 32-bit IDs in systems with multiple devices needing separate control
- Default `0x00000000`
- Recommendation: Use `0x00000000` in single-device or all-respond-identically systems

##### Word 12 — CIF 0

Bits set:
- Bit 30: Reference Point present
- Bit 21: Sample Rate present
- Bit 20: Timestamp Adjustment present
- Bit 2: CIF 1 present

##### Word 13 — CIF 1

- Bit 1: Buffer Size present (only bit set in CIF 1)

##### Words 19–21 — Buffer Size Field

- Words 19–20: 64-bit unsigned integer = sink's buffer size in bytes
- Word 21: 16 reserved MSBs (set 0) + Buffer Level sub-field (next 8 bits) + Buffer Status sub-field (8 LSBs).
  - DIFI extends Buffer Level to 12 bits using top 4 bits of Buffer Status (see Buffer Level / Buffer Status table above)
  - Bottom 4 bits of Buffer Status: OF, NF, NE, UF

---

## 5. Stream and Reference Point ID

### 5.1 Stream Identifier (SID) and SID Location

The SID has three functions:
1. Indicates that a Data/Context/Command Packet is part of a sequence sharing the same Stream ID
2. Indicates which Context/Command streams are associated with which Data streams
3. Defines a specific location (the **SID location**) — generally source or destination of stream — used with timestamping

#### Mandatory inclusion

DIFI mandates the SID, Integer Seconds Timestamp, and Fractional Seconds Timestamp ("Prologue Timestamp") in Data Packets.

#### Prologue Timestamp meaning

Prologue Timestamp = time first sample in a Data Packet is present at the SID location.
First sample at Reference Point = Prologue Timestamp + Timestamp Adjustment (see §5.2).

#### SID Location Rules (by device category)

| Device Category | SID Location |
|---|---|
| (i) Analog → DIFI converter (source) | Point of generation of digital samples within the ADC (Figures 12, 13) |
| (ii) DIFI → analog converter (sink) | Point of consumption of samples within the DAC (Figures 14, 15) |
| (iii) Intermediate digital-in/digital-out device | If on Rx path (e.g., splitter): point of generation of digital samples. If on Tx path (e.g., combiner): point of operation on samples (e.g., combining), after any buffering (Figures 16, 17) |
| IF replication ("bookend": IF→DIFI→IF) | Point of generation of digital samples within the category-(i) device (Figure 18) |

### 5.2 Reference Point Identifier and Timestamp Adjustment

The Reference Point Identifier identifies a location, **other than the SID location**, to which certain parameters apply (Timestamp Adjustment, Reference Level, reference frequencies).

The Reference Point Identifier, Reference Level, reference frequency fields, and Timestamp Adjustment field are mandatory.

**Recommended Reference Point assignments:**

| Reference Point | Recommended for |
|---|---|
| 100 (`0x0064`) | Analog input/output of an IF Converter |
| 75 (`0x004B`) | Analog output (Tx) / input (Rx) of an RF device |
| 25 (`0x0019`) | Antenna feed (when timing critical) |
| 15 (`0x000F`) | Air interface (ESAs without single-point RF reference or feed port) |

**Field semantics:**

- **Reference Level field** = analog value in dBm at the Reference Point
- **IF Reference Frequency field** = frequency at Reference Point 100 (when accessible)
- **RF Reference Frequency field** = frequency at Reference Point 75

#### Timestamp Adjustment

- Physical signal delay between Reference Point and SID, in **femtoseconds**
- Generally negative on Rx path, positive on Tx path

Example (Figure 26, Reference Point 100): Timestamp Adjustment = `T100 - TSID`.

#### Reference Configuration Examples (Figures 19–25)

- **Figure 19** — Receive with IFC; Reference Point 100 preferred. Context Packet contains RP=100, Reference Level (analog dBm at RP producing full-scale sine in DIFI payload), pre-conversion analog gain, post-conversion digital gain
- **Figure 20** — Transmit with IFC; RP 100 preferred. Context Packet contains RP=100, Reference Level (analog dBm at RP from full-scale sine input at DIFI input)
- **Figure 21** — Receive with RFC; RP 75 preferred
- **Figure 22** — Transmit with RFC; RP 75 preferred. Reference Level = intended power dBm at RP
- **Figure 23** — Transmit with DIFI-interface ESA; RP 15 (air interface) preferred. Reference Level = intended EIRP in dBm at air interface
- **Figure 24** — Tx with intermediate DIFI→DIFI device + IFC; RP 100 used by Combiner output stream. Reference Level for the other two streams has no meaning; their RP and SID location still used for timing/sync
- **Figure 25** — Like Figure 24 but with RFC; RP 75 used by Combiner output stream

---

## Cross-Reference Index

### By Field — where defined

| Field | Section / Word |
|---|---|
| Bandwidth | §4.3.1 / Words 10, 11 |
| Buffer Level / Status | §4.4 / Word 21 |
| Buffer Size | §4.4 / Words 19, 20 |
| CAM Field | §4.4 / Word 8 (Table 4-22) |
| CIF 0 | §4.3.1 / Word 8 (Figure 9); §4.3.2 / Word 8 (Figure 11); §4.4 / Word 12 |
| CIF 1 | §4.3.2 / Word 9; §4.4 / Word 13 |
| Class Identifier | §4.1 / Words 3, 4 |
| Controllee ID | §4.4 / Word 10 |
| Controller ID | §4.4 / Word 11 |
| Data Item Format | §4.3.1 / Words 26, 27 |
| Data Packet Payload Format | §4.3.1 / Words 26, 27 (Figure 10) |
| Fractional-Seconds Timestamp | §4.1 / Words 6, 7 |
| Gain | §4.3.1 / Word 19 |
| IF Band Offset | §4.3.1 / Words 16, 17 |
| IF Reference Frequency | §4.3.1 / Words 12, 13 |
| Information Class Code | §4.1 / Word 4 bits 31–16 |
| Integer-Seconds Timestamp | §4.1 / Word 5 |
| Message ID | §4.4 / Word 9 |
| OUI | §4.1 / Word 3 bits 23–0 (always `0x6A621E`) |
| Packet Class Code | §4.1 / Word 4 bits 15–0 |
| Packet Header | §4.1 / Word 1 |
| Packet Size | §4.1 / Word 1 bits 15–0 |
| Packet Type | §4.1 / Word 1 bits 31–28 |
| Pad Bit Count | §4.1 / Word 3 bits 31–27 |
| Reference Level | §4.3.1 / Word 18 bits 15–0 |
| Reference Point | §4.3.1 / Word 9; §4.4 / Word 14 |
| RF Reference Frequency | §4.3.1 / Words 14, 15 |
| Sample Rate | §4.3.1 / Words 20, 21; §4.4 / Words 15, 16 |
| Scaling Level | §4.3.1 / Word 18 bits 31–16 |
| SeqNum | §4.1 / Word 1 bits 19–16 |
| State and Event Indicators | §4.3.1 / Word 25 |
| Stream Identifier (SID) | §4.1 / Word 2 |
| Timestamp Adjustment | §4.3.1 / Words 22, 23; §4.4 / Words 17, 18 |
| Timestamp Calibration Time | §4.3.1 / Word 24 |
| Timestamp Fractional (TSF) | §4.1 / Word 1 bits 21–20 |
| Timestamp Integer (TSI) | §4.1 / Word 1 bits 23–22 |
| Timestamp Mode (TSM) | §4.3.1 / Word 1 bit 24 (Table 4-16) |
| V49 Spec Version | §4.3.2 / Word 10 |
| Year/Day/Revision/Type/ICD Version | §4.3.2 / Word 11 |
