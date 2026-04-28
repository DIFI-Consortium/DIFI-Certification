# DIFI Standard v1.3.0 — AI Reference

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
| Default Controllee/Controller ID when single device | `0x00000000` |

### 0.2 Information Classes (summary)

| Code | Name | First in | Purpose | Packet Classes Used |
|---|---|---|---|---|
| `0x0000` | Basic Data Plane | v1.0 | Convey I/Q + context (Real-Time TSF) | `0x0000`, `0x0001` |
| `0x0001` | Version Flow | v1.0 | Type/version + time-of-day (legacy sync) | `0x0004` |
| `0x0002` | Data Plane plus Upstream Flow Control, Sample Count | v1.2 | I/Q + context + sink-master flow control (Sample Count TSF) | `0x0002`, `0x0003`, `0x0005` |
| `0x0003` | Data Plane plus Upstream Flow Control, Real Time TSF | v1.2 | Same as `0x0002` but Real-Time TSF | `0x0000`, `0x0001`, `0x0006` |
| `0x0004` | Basic Data Plane, Sample Count TSF | v1.2.1 | Same as `0x0000` but Sample Count TSF | `0x0002`, `0x0003` |
| `0x0005` | Data Plane plus Downstream Flow Control, Sample Count | v1.2 | Source-master flow control variant of `0x0002` | `0x0002`, `0x0003`, `0x0005` |
| `0x0006` | Data Plane plus Downstream Flow Control, Real Time TSF | v1.2 | Source-master flow control, Real-Time TSF | `0x0000`, `0x0001`, `0x0006` |
| `0x0100` | Basic Data Plane with Link Establishment | v1.3 | `0x0000` + LE | `0x0000`, `0x0001`, `0x0007`, `0x0008`, `0x0009` |
| `0x0101` | Standalone Link Establishment | v1.3 | LE for `0x00XX` Info Classes (no signal data) | `0x0007`, `0x0008` |
| `0x0102` | Data Plane plus Upstream Flow Control, Sample Count with LE | v1.3 | `0x0002` + LE | `0x0002`, `0x0003`, `0x0005`, `0x0007`, `0x0008`, `0x0009` |
| `0x0103` | Data Plane plus Upstream Flow Control, Real Time TSF with LE | v1.3 | `0x0003` + LE | `0x0000`, `0x0001`, `0x0006`, `0x0007`, `0x0008`, `0x0009` |
| `0x0104` | Data Plane plus Downstream Flow Control, Sample Count with LE | v1.3 | `0x0005` + LE | `0x0002`, `0x0003`, `0x0007`, `0x0008`, `0x0009` |
| `0x0105` | Data Plane plus Downstream Flow Control, Real Time TSF with LE | v1.3 | `0x0006` + LE | `0x0000`, `0x0001`, `0x0006`, `0x0007`, `0x0008`, `0x0009` |
| `0x0106` | Data Plane, Sample Count with LE | v1.3 | `0x0004` + LE | `0x0002`, `0x0003`, `0x0007`, `0x0008`, `0x0009` |

### 0.3 Packet Classes (summary)

| Code | Name | Type | TSF | Size (words) | First in |
|---|---|---|---|---|---|
| `0x0000` | Standard Flow Signal Data | Data | Real Time (ps) | 7 + N | v1.0 |
| `0x0001` | Standard Flow Signal Context | Context | Real Time (ps) | 27 | v1.0 |
| `0x0002` | Sample Count Signal Flow Data | Data | Sample Count | 7 + N | v1.2 |
| `0x0003` | Sample Count Signal Flow Context | Context | Sample Count | 27 | v1.2 |
| `0x0004` | Version Flow Signal Context | Context | Real Time (ps) | 11 | v1.0 |
| `0x0005` | Sample Count Timing Flow Control | Command | Sample Count | 21 | v1.2 |
| `0x0006` | Real Time TSF Timing Flow Control | Command | Real Time (ps) | 21 | v1.2 |
| `0x0007` | Sink Capability Query Control | Extension Command | per TSF | 13 (long) / 12 (short) | v1.3 |
| `0x0008` | Sink Capability Response Acknowledge | Extension Acknowledge | per TSF | Variable (long) / 18 (short) | v1.3 |
| `0x0009` | Status Report Control | Extension Command | per TSF | 15 / 17 / 21 | v1.3 |

### 0.4 Reference Point Codes

| Decimal | Hex | Meaning |
|---|---|---|
| 100 | `0x00000064` | IF Converter analog port (input on Rx, output on Tx) — preferred when device has IF analog interface |
| 75  | `0x0000004B` | RF Converter analog port — preferred when device has RF analog interface |
| 25  | `0x00000019` | Antenna feed — used when Tx/Rx timing is critical (e.g., ranging) |
| 15  | `0x0000000F` | Air interface — for ESAs without single-point RF reference |

### 0.5 v1.3.0 vs v1.2.1 Delta (what changed)

- **Added** Information Classes `0x0100`–`0x0106` (Link Establishment variants of `0x00XX`)
- **Added** Information Class `0x0101` (Standalone Link Establishment)
- **Added** Packet Class `0x0007` (Sink Capability Query Control) — long & short form
- **Added** Packet Class `0x0008` (Sink Capability Response Acknowledge) — long & short form
- **Added** Packet Class `0x0009` (Status Report Control)
- **Added** Section 6 — Link Establishment / Negotiation (state diagram)
- **Added** Information Classes `0x0005`/`0x0006` (Downstream Flow Control: source-master timing)
- **Added** Buffer Size field deviation: in v1.3 the Buffer Size field is **three** 32-bit words (VITA 49.2 has two)
- **Added** TDMA best-practices appendix (use cases 1.a, 1.b, 2.a, 2.b, 2.c)
- **Renamed** `0x0002`/`0x0003` to "Upstream Flow Control" (sink → source) to distinguish from new `0x0005`/`0x0006` "Downstream"

---

## 1. Introduction

The data plane interface transmits and receives digitized RF/IF data plus metadata over standard IP networks. Substantially compliant with VITA 49.2 (deviations in §1.5).

### 1.3 DIFI Standard Definitions

| Term | Definition |
|---|---|
| **DIFI Device** | Any hardware, firmware, or software that creates a Source or Sink using the DIFI protocol |
| **Endpoint** | A Source or a Sink |
| **Flow** | Transmission of data as packets/packet stream from Source to Sink |
| **Full Scale Amplitude** | For an I (Q) sample with N bits: `2^(N-1) − 1` |
| **Full Scale Complex Sinusoid** | Peak magnitude `√(I² + Q²)` equals available full-scale amplitude `R` of `I` or `Q` separately |
| **IF Converter (IFC)** | Device that transmutes signals between digital IF and analog IF |
| **Intermediate Frequency (IF) Signal** | Any signal after frequency translation; zero-IF = complex baseband |
| **Information Class** | Group of one or more Packet Classes plus packet stream associations |
| **Information Stream** | Flow of Packet Streams containing signal data, metadata, and/or control |
| **[IP] Socket** | IP address and port number |
| **Link Efficient Packing** | Signal Data Payload packed to maximise Ethernet link efficiency |
| **Packet Class** | Set of rules and structures defining packet format and content |
| **Packet Type** | Type of packet: Data, Context, or Command |
| **Packet Stream** | Flow of packets carrying data Source → Sink |
| **Process Efficient Packing** | Signal Data Payload packed to minimise processing load (at expense of link bandwidth) |
| **Receive (Rx) Direction** | Away from the RF communications aperture |
| **Reference Point** | Location to which parameters (time/frequency/phase) refer |
| **RF Converter (RFC)** | Device that transmutes signals between digital IF and analog RF |
| **Signal Data Packet Sink** | Packet Stream signal destination socket — VITA 49.2 packet "consumer" |
| **Signal Data Packet Source** | Packet Stream signal origination socket — VITA 49.2 packet "emitter" |
| **Stream Identifier (SID)** | Field that (i) groups packets by type and Stream ID, (ii) associates Context/Command streams with Data streams, (iii) defines the SID location used with timestamping |
| **Transmit (Tx) Direction** | Towards the RF communications aperture |

### 1.4 Abbreviations

ADC, ARP, CIF, DAC, dBFS, DIFI, FPGA, GPS, I/Q, ICD, IEEE-ISTO, IF, IFC, IP, IPv4/IPv6, IRIG, LAN, MAC, Msps, NIC, NTP, NTR, OUI, POSIX, PTP, RF, TC, TOD, TSF, TSI, TSM, UDP, UTC, VLAN, VRL (VITA Radio Link), VRT (VITA Radio Transport).

### 1.5 Deviations from VITA 49.2

| Field | Deviation |
|---|---|
| Reference Level Field | Split into mandatory bits 15–0 (Reference Level, dBm at RP) and optional bits 31–16 ("Scaling" sub-field, dBFS) |
| Reference Level reserved bits | Converted to optional Scaling sub-field |
| Buffer Size field | DIFI uses **three** 32-bit words: first two = buffer size in bytes (64-bit), third = buffer level/status. (VITA 49.2 uses two 32-bit words.) |

### 1.6 System Integrator Subtleties

Compare the following between DIFI-compatible equipment to ensure interoperability: **Bit Depth, Reference Level, Sample Rate, Reference Plane**.

---

## 2. Data Plane Implementation

Two independent flows: **Receive** (RF/IF input → IP-network output) and **Transmit** (IP-network input → RF/IF output). VITA 49.2 trailers and VRL framing are NOT used.

### 2.1 Protocol Overview

DIFI supports three packet types:
1. **Context Packets** — metadata
2. **Signal Data Packets** — IQ samples
3. **Command Packets** — Control + Acknowledge subtypes; provide/acknowledge device settings, support timing control, link establishment

Stack (top → bottom):
```
DIFI Application
DIFI Protocol Layer (Command / Context / Signal Data Packet)
User Datagram Protocol (UDP)
IPv4 | IPv6
Ethernet
```

### 2.2 Ethernet Requirements

- Standard 802.3 Ethernet frames
- MUST support jumbo frames (MTU 9000)
- MUST support 802.1Q (VLAN) and 802.1ad (QinQ)
- DIFI endpoint MUST have at least one Ethernet MAC address
- Fixed Ethernet overhead: IP 20 (IPv4) / ≥40 (IPv6) + UDP 8 + VITA 28
- Ethernet frame payload: 128–9000 octets

### 2.3 IP Requirements

- IPv4 (RFC 791) or IPv6 (RFC 8200)
- Source IP address MUST be the same for context and data packets in a given DIFI stream
- IPv4 fragmentation MUST NOT be produced at source; sink MAY discard fragmented packets
- IPv6 extension headers: implementations MAY ignore content but MUST process IPv6 payload regardless

### 2.4 UDP Requirements

- Each DIFI packet in standard UDP datagram
- UDP checksums: mandatory for IPv6, optional for IPv4; if used MUST be valid
- UDP datagram payload contains exactly one of: DIFI context, control, or data packet

---

## 3. Information Classes

An **Information Stream** is a collection of Packet Streams (each with a single Stream ID). Structure is defined by an **Information Class**.

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
| Stream Purpose | Convey digitized I/Q samples; control/reference config conveyed in advance or via non-VRT streams |
| Packet Stream Names | 1. Signal Data; 2. Signal Context |
| Packet Classes | 1. Standard Flow Signal Data (`0x0000`); 2. Standard Flow Signal Context (`0x0001`) |
| Packet Stream Details | Data packet size unrestricted; bit padding NOT permitted in Class 0; max 9000 bytes; Context packets required, on field change OR user periodicity (whichever first) |
| Reference Points | Tx: analog output of conversion device (default); Rx: analog input. IF: 100 (`0x0064`). RF: 75 (`0x004B`) |
| Associations | Signal Context ↔ Signal Data |

Uses Real Time (picoseconds) TSF. Contains data + metadata only — no Command Packet Stream.

**Rule 3.1-1:** A DIFI Source certifying to this class shall be capable of issuing Standard Flow Signal Context Packets.
**Rule 3.1-2:** A DIFI Sink certifying to this class shall be capable of receiving and processing Standard Flow Signal Context Packets.

### 3.2 Information Class `0x0001` — Version Flow

| Component | Specification |
|---|---|
| Name / Code | "Version Flow" / `0x0001` |
| Stream Purpose | Convey type/version + precise time-of-day for software synchronization |
| Packet Classes | Version Flow Signal Context (`0x0004`) |
| Packet Stream Details | 11 words; no data packets; rate 0–100 packets/sec |
| Reference Points | Reference Point field NOT included; reference is to the SID |
| Associations | None |

Use of `0x0001` for timing is **legacy**. For DIFI-Sink-emitted timestamped packets use `0x0002` or `0x0003`.

**Rule 3.2-1:** A DIFI Device certifying to this class shall be capable of issuing and receiving Version Flow Context Packets.

### 3.3 Information Class `0x0002` — Data Plane plus Upstream Flow Control (Sample Count)

| Component | Specification |
|---|---|
| Name / Code | "Data Plane plus Flow Control" / `0x0002` |
| Stream Purpose | I/Q + context + Flow Control conveying timing for sink-master Sample-Rate configurations |
| Packet Classes | Sample Count Signal Data (`0x0002`); Sample Count Signal Context (`0x0003`); Sample Count Timing Flow Control (`0x0005`) |
| Packet Stream Details | Bit padding permitted on final word; Flow Control rate ≤ 1000/sec |
| Associations | Signal Context ↔ Signal Data; Timing Flow Command ↔ Signal Data |

Provides full sample-rate / timestamp synchronization. Command Packets emitted by Packet Stream **Sink** (sink is Controller). Two sub-types: **Control** and **Acknowledge** — `0x0002` does NOT use Acknowledge.

**Rule 3.3-1:** Sinks shall issue Sample Count Timing Flow Control Packets and receive/process Sample Count Signal Context Packets.
**Rule 3.3-2:** Sources shall issue Sample Count Signal Context Packets and receive/process Sample Count Timing Flow Control Packets.

### 3.4 Information Class `0x0003` — Data Plane plus Upstream Flow Control, Real Time TSF

Identical to `0x0002` except uses **Real Time (picoseconds)** TSF instead of Sample Count.

| Packet Classes | Standard Flow Signal Data (`0x0000`); Standard Flow Signal Context (`0x0001`); Real Time TSF Timing Flow Control (`0x0006`) |
|---|---|

### 3.5 Information Class `0x0004` — Basic Data Plane, Sample Count TSF

Identical to `0x0000` except uses **Sample Count** TSF instead of Real Time (picoseconds).

| Packet Classes | Sample Count Signal Data (`0x0002`); Sample Count Signal Context (`0x0003`) |
|---|---|

### 3.6 Information Class `0x0005` — Data Plane plus Downstream Flow Control (Sample Count)

Like `0x0002` but **Source** is the Controller (Source emits Flow Control to Sink).

| Packet Classes | Sample Count Signal Data (`0x0002`); Sample Count Signal Context (`0x0003`); Sample Count Timing Flow Control (`0x0005`) |
|---|---|

**Rule 3.6-1:** Sources shall issue Sample Count Signal Context Packets **and** Sample Count Timing Flow Control Packets (Source = Controller).
**Rule 3.6-2:** Sinks shall receive/process both, synchronizing to the Source.

### 3.7 Information Class `0x0006` — Data Plane plus Downstream Flow Control, Real Time TSF

Like `0x0003` but Source-master. Source emits Standard Flow Signal Context + Real Time TSF Timing Flow Control.

**Rule 3.7-1 / 3.7-2:** Sources issue Standard Flow Signal Context + Real Time TSF Timing Flow Control; Sinks receive/process and synchronize.

### 3.8 Information Classes `0x01XX` — With Link Establishment

`0x01XX` Information Classes are parallel to `0x00XX` and add packet classes for link establishment and maintenance:
- Communicate Sink capabilities to Sources
- Characterize link latency/jitter; "heartbeat"
- Report errors and warnings

| Code | Parallel of | Adds |
|---|---|---|
| `0x0100` | `0x0000` | LE |
| `0x0102` | `0x0002` | LE |
| `0x0103` | `0x0003` | LE |
| `0x0104` | `0x0005` (Downstream FC, Sample Count) | LE |
| `0x0105` | `0x0006` (Downstream FC, Real-Time) | LE |
| `0x0106` | `0x0004` | LE |

For single-Source/single-Sink streams, LE packets share the data Stream ID. In multi-stream/multi-source aggregation, LE packets may bear the SID of any component or the combined stream.

**Rule 3.8-1:** `0x01XX` Sources shall issue Sink Capability Query Control Packets (`0x0007`, long+short form) and receive/process Sink Capability Response Acknowledge Packets (`0x0008`, long+short form).
**Rule 3.8-2:** `0x01XX` Sinks shall receive/process `0x0007` and issue `0x0008`. Sinks shall issue `0x0008` in response to `0x0007` containing the Sink's Controllee ID (or `0x00000000` if Controllee IDs not used). Long-form responses match long-form queries; same for short-form.
**Rule 3.8-3:** `0x01XX` Sinks (except `0x0101`) shall issue Status Report Control Packets (`0x0009`) at user-defined rate 1–1000/sec, and on any change in status fields.
**Rule 3.8-4:** `0x01XX` Sources (except `0x0101`) shall receive/process `0x0009`.

### 3.9 Information Class `0x0101` — Standalone Link Establishment

Standalone mechanism for `0x00XX` streams to use basic LE without converting to `0x01XX`. Uses only Sink Capabilities Extension Control Packet and Sink Capabilities Extension Acknowledge Packet. Stream ID = `0x00000000` (not tied to a specific Data Stream).

**Rule 3.9-1:** `0x0101` Sources shall issue `0x0007` and receive/process `0x0008`.
**Rule 3.9-2:** `0x0101` Sinks shall receive/process `0x0007` and issue `0x0008`. Sinks shall issue `0x0008` in response to `0x0007` containing the Sink's Controllee ID (or `0x00000000`).

---

## 4. Packet Classes

DIFI uses four VITA 49.2 packet types:

| Type Code | Description | DIFI Packet Class Codes |
|---|---|---|
| `0x1` | Data packet w/ Stream ID | `0x0000`, `0x0002` |
| `0x4` | Context packet w/ Stream ID | `0x0001`, `0x0003`, `0x0004` |
| `0x6` | Command packet w/ Stream ID | `0x0005`, `0x0006` |
| `0x7` | Extension Command packet | `0x0007`, `0x0008`, `0x0009` |

### Table 4-2 — Information Class ↔ Packet Class Membership

(`R` = Required, `O*` = issuance rate may be zero but non-zero recommended, `O**` = may be omitted in some Source-synchronized use cases)

| Info Class | `0x0000` | `0x0001` | `0x0002` | `0x0003` | `0x0004` | `0x0005` | `0x0006` | `0x0007` | `0x0008` | `0x0009` |
|---|---|---|---|---|---|---|---|---|---|---|
| `0x0000` | R | O* | | | | | | | | |
| `0x0001` | | | | | R | | | | | |
| `0x0002` | | | R | O* | | O** | | | | |
| `0x0003` | R | O* | | | | | O** | | | |
| `0x0004` | | | R | O* | | | | | | |
| `0x0005` | | | R | O* | | | | | | |
| `0x0006` | R | O* | | | | | | | | |
| `0x0100` | R | O* | | | | | | R | R | R |
| `0x0101` | | | | | | | | R | R | |
| `0x0102` | | | R | O* | | | | R | R | R |
| `0x0103` | R | O* | | | | | | R | R | R |
| `0x0104` | | | R | O* | | | R | R | R | R |
| `0x0105` | R | O* | | | | | O** | R | R | R |
| `0x0106` | | | R | O* | | | | R | R | R |

### 4.1 DIFI Packet Prologue (common)

All DIFI packets contain a prologue (Words 1–7) followed by a payload.

#### Prologue word layout

| Word | Contents |
|---|---|
| 1 | Packet Header |
| 2 | Stream Identifier (SID) |
| 3 | Pad Bit Count + Reserved + 24-bit OUI |
| 4 | Information Class Code + Packet Class Code |
| 5 | Integer-Seconds Timestamp |
| 6, 7 | Fractional-Seconds Timestamp (64-bit) |

#### Word 1: Packet Header bit-fields

| Bits | Field | Notes |
|---|---|---|
| 31–28 | Packet Type | DIFI uses `0x1` (Data + SID), `0x4` (Context), `0x6` (Command), `0x7` (Extension Command) |
| 27 | Class Identifier Indicator | MUST be `1` for DIFI |
| 26–24 | Packet-type-dependent | See per-class sections |
| 23–22 | TSI | See Table 4-4 |
| 21–20 | TSF | See Table 4-5 |
| 19–16 | SeqNum | 4-bit, mod-16 per successive packet in each Packet Stream (separate sequences per type) |
| 15–0 | Packet Size | Total 32-bit words (header + payload), excluding UDP encapsulation |

#### Table 4-4 — TSI Codes

| Code | Meaning |
|---|---|
| `00` | NOT ALLOWED in DIFI (would mean Integer Seconds omitted) |
| `01` | UTC — epoch Jan 1 1970, includes leap seconds |
| `10` | GPS — epoch Jan 6 1980, no leap seconds |
| `11` | POSIX — epoch Jan 1 1970, no leap seconds |

#### Table 4-5 — TSF Codes

| Code | Meaning | Used by Packet Classes |
|---|---|---|
| `00` | NOT ALLOWED in DIFI | — |
| `01` | Sample Count Timestamp | `0x0002`, `0x0003`, `0x0005` |
| `10` | Real Time (Picoseconds) Timestamp | `0x0000`, `0x0001`, `0x0004`, `0x0006` |
| `11` | Free Running Count Timestamp | NOT USED in DIFI |

#### Word 2: Stream ID (SID)

- 32-bit unsigned, default `0` if unset; settable before/at run time
- Associated Data + Context + Command streams share SIDs
- For Time Release use cases: SID location at IFC/RFC digital interface (ADC out on Rx; DAC in on Tx)
- For Non-Time Release use cases: SID location is output of the packetizer in the DIFI Source
- See §5.1 and VITA 49.2 §5.1.2

#### Words 3 & 4: Class Identifier

| Bits | Field | Value |
|---|---|---|
| W3, 31–27 | Pad Bit Count | Unsigned 5-bit, 0–31. Set to 0 in Context/Command packets. For Data: see Table 4-10 |
| W3, 26–24 | Reserved | Always `0` (VITA 49.2 Rule 5.1.3-5) |
| W3, 23–0 | OUI | Always `0x6A621E` (DIFI CID) |
| W4, 31–16 | Information Class Code | See §3 |
| W4, 15–0 | Packet Class Code | See §0.3 |

Hierarchy: **Stream → Information Class → Packet Class**.

#### Word 5: Integer-Seconds Timestamp

- Seconds since epoch for selected TSI reference (UTC/GPS/POSIX)
- Only UTC includes leap seconds
- For Sample Count TSF Packet Classes: incremented when Fractional Timestamp reaches Sample Rate (nominally once per second)
- See VITA 49.2 §5.1.4–5.1.5

#### Words 6 & 7: Fractional-Seconds Timestamp

- 64-bit unsigned integer
- Real Time TSF Classes: picoseconds since most recent increment/reset of Integer Seconds
- Sample Count TSF Classes: sample counts since most recent increment/reset
- Reset to 0 when Integer Seconds increments or resets

---

### 4.2 Data Packet Classes (`0x0000`, `0x0002`)

Both classes are nearly identical; differ only in TSF (Real Time ps for `0x0000`, Sample Count for `0x0002`) and bit-padding rules.

#### Table 4-7 — Data Packet Class Content

| Parameter | `0x0000` | `0x0002` |
|---|---|---|
| Packet Type | Signal Data Packet w/ Stream ID | (same) |
| Packet Size | Variable (7 prologue + N data) | (same) |
| Stream Identifier | Yes, runtime | (same) |
| Class ID | Present (W3: Pad+OUI; W4: Info Class + Packet Class) | (same) |
| Integer-Seconds TS | UTC/POSIX/GPS per Header | Routinely incremented when Fractional reaches Sample Rate count |
| Fractional Seconds TS | Real time, picoseconds | Sample Count |
| Packing | Link Efficient | (same) |
| Data Item Size | Variable, user-selected; I/Q components 4–16 bits each (pairs 8–32 bits) | (same) |
| Real/Complex Type | Complex Cartesian | (same) |
| Data Item Format | Signed Integer (V49.2 Signed Fixed-Point code `00000`) | (same) |
| Sample/Channel repeating | None | None |
| Repeat Count | 0 | 0 |
| Packet Trailer | Not used | Not used |

#### Table 4-8 — Data Packet Format

| Word | Contents |
|---|---|
| 1 | Packet Header (Type=`0x1`, ...) |
| 2 | Stream Identifier |
| 3 | Pad Bit Count + Reserved + 24-bit DIFI CID `0x6A621E` |
| 4 | Information Class Code + Packet Class Code |
| 5 | Integer Seconds Timestamp (per TSI) |
| 6, 7 | Fractional Seconds Timestamp (per TSF, 64-bit) |
| 8 … N+7 | Signal Data Payload (Complex Cartesian, 4–16-bit signed integers, link-efficient) |

Total Packet Size = N + 7 words.

#### Word 1 details for Data Packets

| Bits | Field | Value |
|---|---|---|
| 31–28 | Packet Type | `0x1` |
| 27 | Class Identifier | `1` |
| 26 | Trailer Indicator | `0` |
| 25 | VITA 49.0 Indicator | `0` |
| 24 | VITA 49.2 Spectrum/Time | `0` (time data; spectrum unsupported) |
| 23–22 | TSI | (per Table 4-4) |
| 21–20 | TSF | `0x2` for `0x0000`; `0x1` for `0x0002` |
| 19–16 | SeqNum | mod-16 |
| 15–0 | Packet Size | 7 + N words |

#### Sample padding (Class `0x0000` in Information Class `0x0000` only)

When Class `0x0000` is used in Information Class `0x0000`, **no bit padding** allowed — every packet contains an integer number of I/Q pairs, and pairs (each `2 × sample-depth` bits) must fit into a whole number of 32-bit units.

#### Table 4-9 — Sample Padding Granularity

For each `bits per sample`: `2 × <bps> × <sample count granularity> = 32 × <32-bit unit granularity>`

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

#### Table 4-10 — Bit Padding Permission

| Information Class | Data Packet Class | Bit Padding Permitted |
|---|---|---|
| `0x0000` | `0x0000` | **No** |
| `0x0002` | `0x0002` | Yes |
| `0x0003` | `0x0000` | Yes |
| `0x0004` | `0x0002` | Yes |

(`0x01XX` LE classes inherit padding rules from their `0x00XX` parallel; same for `0x0005`/`0x0006`.)

#### Words 8 to N+7 — Data Payload

- Complex Cartesian; each pair is I followed by Q
- Signed integer, bit-depth specified by Data Packet Payload Format Field in associated Context Packet
- Link-efficient packing (no padding bits between pairs; samples may wrap 32-bit words)
- Bit padding 0–31 permitted at end of final 32-bit word **except** when Class `0x0000` is in Information Class `0x0000`
- Unless otherwise stated, Prologue Timestamp = time the **first** data sample appears at the SID location

---

### 4.3 Context Packet Classes (`0x0001`, `0x0003`, `0x0004`)

Context Packets convey metadata permitting interpretation of Data Packet payloads.

#### Common conventions

- All frequency / sample rate fields in Hz; VITA 49.2 64-bit two's-complement format with radix point right of bit 20 in second word; DIFI requires integer Hz (bits right of radix = 0)
- All Reference Level fields in dBm; VITA 49.2 16-bit two's-complement with radix 9 left + 7 right (Figure 9). Scaling fields same format, in dBFS
- SID location matches associated Data Packet Stream

#### Context Effectivity

When Context values change, Source SHALL issue a Context Packet with the new values. Context values SHALL NOT change mid-Data-Payload — the first sample using the new values must be the first sample of a new Data Packet. The new Context Packet and the corresponding first Data Packet using the new Context values **share the same Timestamp**.

#### Table 4-12 — Context Packet Class Content

| Parameter | `0x0001` | `0x0003` | `0x0004` |
|---|---|---|---|
| Packet Type | Context Packet w/ SID | (same) | (same; SID independent of signal data SID) |
| Packet Size | 27 words | 27 words | 11 words |
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
| Data Item Format | Signed integer | Signed integer | N/A |
| Packet Trailer | Not used | Not used | Not used |

#### 4.3.1 Signal Context Packets — Format (Classes `0x0001` and `0x0003`)

Table 4-13 layout (27 words):

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
| 24 | TSM (Timestamp Mode) | See Table 4-14 |
| 23–22 | TSI | per §4.1 |
| 21–20 | TSF | `0x2` for `0x0001`; `0x1` for `0x0003` |
| 19–16 | SeqNum | mod-16 |
| 15–0 | Packet Size | `27` |

##### Table 4-14 — TSM (Timestamp Mode) Values

| Information Class | Timestamp Mode |
|---|---|
| `0x0000`, `0x0004` | Coarse (TSM = 1) |
| `0x0002`, `0x0003` | Fine (TSM = 0) |

For Packet Class `0x0003`, TSM SHALL be `0` (precise timing). Fine TSM implies new Context info applies at Context-packet timestamp, AND that timestamp matches the Data Packet timestamp containing the first data using the new Context. Coarse TSM should only be used for static Context with periodic validation.

##### Word 8 — CIF 0 (Context Indicator Field 0)

- Bit 31: change indicator (set = new info; clear = no change)
- Other set bits indicate which Context fields are present
- Bits 1, 2, 3 set → CIF 1, 2, 3 word(s) included

For Classes `0x0001` and `0x0003`, valid values:
- `0xFBB98000` — change in any context value
- `0x7BB98000` — no change

##### Word 9 — Reference Point Field

Allowed values: `100` (`0x00000064`), `75` (`0x0000004B`), `25` (`0x00000019`), `15` (`0x0000000F`). See §0.4.

##### Words 10 & 11 — Bandwidth

Useable bandwidth of digitized signal; 1 Hz increments. VITA 49.2 §9.5.1.

##### Words 12 & 13 — IF Reference Frequency

- Systems with accessible analog IF: sampling center frequency for IF conversion
- Systems with RF in/out and no accessible IF: `0x00000000` at source; sink ignores
- Use determined by Reference Point field
- Defaults to 0 for zero-IF
- VITA 49.2 §9.5.5

##### Words 14 & 15 — RF Reference Frequency

- Systems with analog IF: intended RF center frequency from analog conversion
- Direct RF conversion: sampling center frequency for direct RF
- For Class `0x0003`: RF center freq on RF input (Rx) or output (Tx). Tx RF reference freq is **status only**
- VITA 49.2 §9.5.10

##### Words 16 & 17 — IF Band Offset

- Stream offset from IF center frequency; default 0 Hz
- Always 0 for zero-IF
- Signed, 1 Hz resolution; settable anywhere in system bandwidth
- IF Band Offset = Stream Offset (Rx); default Stream Offset for Tx (overridable)
- VITA 49.2 §9.5.4

##### Word 18 — Reference Level

**Bits 31–16 — Scaling Level (optional, Tx only):**
- Scaling applied to digital signal to prevent overflow of 4–16 bit sample words
- Default `0x0000` when unused
- When used: dBFS of a sine wave with same average power as the data payload signal

**Bits 15–0 — Reference Level (mandatory):**
- Relates physical analog amplitude at Reference Point to data samples
- Rx: power level dBm at RP; AC power of single sine at RP producing full-scale digitized sine in payload
- Tx: power level dBm intended at RP from full-scale digital sine in payload
- ESA on RP 15: intended EIRP in dBm on boresight
- **Observation 4.2.1-1:** ESA gain depends on pointing angles; ESA must dynamically account for pointing-angle and frequency in DAC-output→EIRP mapping

##### Word 19 — Gain/Attenuation

- Gain 1 (bits 15–0) + Gain 2 (bits 31–16); 16-bit each, **reserved**
- Source populates `0x0000`; sink ignores
- Prior-revision usage allowed but Reference Level often more useful; vendor-responsible
- VITA 49.2 §9.5.3

##### Words 20 & 21 — Sample Rate

Sample rate of Signal Data packets. VITA 49.2 §9.5.12. See external DIFI Sample Rate Vendor Interoperability area.

##### Words 22 & 23 — Timestamp Adjustment

64-bit two's-complement value in **femtoseconds** = signal delay between Reference Point and SID location. Tx: generally positive; Rx: generally negative. See §5.2.

##### Word 24 — Timestamp Calibration Time

Last time the timestamp was known to be correct. Populated on Tx side. VITA 49.2 §9.7.3.3.

##### Word 25 — State and Event Indicators

- Calibrated time reference lock (bit 19): IRIG-B, IRIG-DC, 1PPS, NTP, GPS
- Frequency reference lock (bit 17): 10 MHz, IRIG-B, IRIG-DC, 1PPS, GPS
- Lock status updated ~once/sec in RF→IP direction
- Tx side uses these to determine Programmed Delay mode availability and end-to-end / Network Delay measurement
- Measured/Network Delays = 0 if calibrated time (bit 19) not locked on RF→IP side
- VITA 49.2 §9.10.8

##### Words 26 & 27 — Data Packet Payload Format

Word 26 fields:

| Bits | Field | Value |
|---|---|---|
| 31 | Packing Method | `1` (Link Efficient) |
| 30–29 | Real-Complex Data Type | `01` (Complex Cartesian) |
| 28–24 | Data Item Format | `00000` (Signed Fixed Point) |
| 23 | Sample Component Repeat Indicator | `0` |
| 22–20 | Event Tag Size | `000` |
| 19–17 | Channel Tag Size | `000` |
| 16–12 | Data Item Fraction Size | `0000` |
| 11–6 | Data Item Size | `(# bits per I or Q) − 1` (3–15) |
| 5–0 | Item Packing Field Size | `(# bits per I or Q) − 1` (3–15) |

Word 27: Repeat Count (16 MSBs) + Vector Size (16 LSBs) — both `0`.

##### Packet Rate

- Standard Flow Signal Context Packet rate: 0 (off) through 20 packets/sec
- Transmission required upon any signal-context-packet field change

#### 4.3.2 Packet Class `0x0004` — Version Flow Signal Context

Conveys type/version + precise time-of-day for software apps. Created Rx side; used Tx side to auto-select compatible packet format.

Table 4-15 layout (11 words):

| Word | Contents |
|---|---|
| 1 | Packet Header |
| 2 | Stream Identifier |
| 3 | Pad Bit Count (=0) + Reserved + 24-bit DIFI CID |
| 4 | Information Class Code + Packet Class Code (`0x0004`) |
| 5 | Integer Seconds Timestamp |
| 6, 7 | Fractional Seconds Timestamp |
| 8 | CIF 0 |
| 9 | CIF 1 (= `0x0000000C`) |
| 10 | V49 Spec Version Word (= `0x00000004`) |
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

##### Word 8 — CIF 0 for `0x0004`

| Value | Meaning |
|---|---|
| `0x80000002` | Change in any context value |
| `0x00000002` | No change |

##### Word 9 — CIF 1 = `0x0000000C`

Indicates V49 Spec Version Word (bit 3) and Year/Day/Revision/Type/ICD Version Word (bit 2) are present.

##### Word 10 — V49 Spec Version

MUST be `0x4` (VITA 49.2). Receive side uses to auto-configure if compatible mode found.

##### Word 11 — Year / Day / Revision / Type / ICD Version

| Bits | Field | Description |
|---|---|---|
| 31–25 | Year | Years since 2000 (compiled date) |
| 24–16 | Day | Day-of-year (1 = Jan 1) |
| 15–10 | Revision | Same year+day version counter (normally 1) |
| 9–6 | Type | Device type 0–15; SHALL be `0x0` (currently undefined) |
| 5–0 | ICD Version | DIFI version (Table 4-16) |

##### Table 4-16 — Version Codes

| Code | Meaning |
|---|---|
| `0` | Version 1 corresponds to DIFI v1.x |
| `1`–`31` | Reserved |

---

### 4.4 Command Packet Classes

DIFI v1.3.0 supports five Command Packet Classes:
- `0x0005` Sample Count Timing Flow Control (Command, sync)
- `0x0006` Real Time TSF Timing Flow Control (Command, sync)
- `0x0007` Sink Capability Query Control (Extension Command, link establishment)
- `0x0008` Sink Capability Response Acknowledge (Extension Acknowledge, link establishment)
- `0x0009` Status Report Control (Extension Command, link maintenance)

#### Table 4-17 — Command Packet Class General Information

| Class | `0x0005` / `0x0006` | `0x0007` | `0x0008` | `0x0009` |
|---|---|---|---|---|
| Class Name | Sample Count / Real Time TSF Timing Flow Control | Sink Capabilities Query Control | Sink Capabilities Response Acknowledge | Status Response Control |
| Packet Type | `0x6` Command w/ SID | `0x7` Extension Command | `0x7` Extension Acknowledge | `0x7` Extension Command |
| Purpose | Timing + buffer info for upstream/downstream sync | Source requests Sink capabilities | Sink provides capabilities to Source | Sink reports errors/warnings to Source |

---

#### 4.4.1 Timing Flow Control Packets (`0x0005`, `0x0006`)

##### Table 4-22 — Timing Flow Control Packet Format (21 words)

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
| 10 | Controllee Identifier (default `0x00000000`) |
| 11 | Controller Identifier (default `0x00000000`) |
| 12 | CIF 0 |
| 13 | CIF 1 |
| 14 | Reference Point (default `0x00000064`) |
| 15, 16 | Sample Rate |
| 17, 18 | Timestamp Adjustment (femtoseconds) |
| 19, 20 | Buffer Size (bytes, 64-bit unsigned) |
| 21 | Reserved + Buffer Fill (12-bit) + Buffer Status (4-bit: OF/NF/NE/UF) |

##### Word 1 — Header for `0x0005` / `0x0006`

| Bits | Field | Value |
|---|---|---|
| 31–28 | Packet Type | `0x6` |
| 27 | Class Identifier | `1` |
| 26–24 | Control vs Ack | `0x0` (Command, not cancellation) |
| 23–22 | TSI | per §4.1 |
| 21–20 | TSF | `0x1` (Sample Count) for `0x0005`; `0x2` (Real Time ps) for `0x0006` |
| 19–16 | SeqNum | mod-16 |
| 15–0 | Packet Size | `21` |

##### Table 4-23 — CAM Field Sub-Fields (Word 8)

For Control Packets in Timing Flow Control:

| Bits | Field | Value |
|---|---|---|
| 31 | Controllee ID Indicator | `1` |
| 30 | Controllee ID Format | `0` (32-bit) |
| 29 | Controller ID Indicator | `1` |
| 28 | Controller ID Format | `0` (32-bit) |
| 27 | Partial Packet Implementation | `0` |
| 26 | Warnings | `0` |
| 25 | Errors | `0` |
| 24–23 | Action Mode | `10` (`0x2`, "execute") |
| 22–15 | Various unused | `0` |
| 14–12 | Timestamp Control Mode | `0x0` (Flow Control conveys timing only — no execution time-frame) |
| 11–8 | Acknowledge Bits | `0` (Control packet only) |
| 7–0 | Reserved | `0` |

##### Word 9 — Message ID

Sequentially assigned per stream by Controller.

##### Words 10, 11 — Controllee/Controller IDs

Default `0x00000000` in single-device or all-respond-identically systems.

##### Word 12 — CIF 0

Bits set: 30 (Reference Point), 21 (Sample Rate), 20 (Timestamp Adjustment), 2 (CIF 1).

##### Word 13 — CIF 1

Bit 1: Buffer Size present (only bit set).

##### Word 14 — Reference Point Field

See §0.4 / §5.2.

##### Words 15–16 — Sample Rate Field

Same format as Context Packet; matches associated Context Packet's Sample Rate.

##### Words 17–18 — Timestamp Adjustment

64-bit two's-complement signed, femtoseconds. Tx generally positive, Rx generally negative.

##### Words 19–21 — Buffer Size Field (DIFI three-word deviation)

- Words 19–20: 64-bit unsigned int = sink buffer size in bytes
- Word 21:
  - Bits 31–16: Reserved (0)
  - Bits 15–4: 12-bit Buffer Fill (0xFFF = full, 0x000 = empty); average over current interval; averaging method implementation-defined
  - Bit 3: Buffer Overflow (set if overflow during current interval)
  - Bit 2: Nearly Full (set if exceeds nearly-full threshold during interval)
  - Bit 1: Nearly Empty (set if falls below nearly-empty threshold during interval)
  - Bit 0: Buffer Underflow (set if underflow during interval)

"Current interval" = between issuance of previous and present Flow Control Packet.

For Information Class `0x0002`, NF/NE thresholds are pre-assigned or set by non-VRT means.

---

#### 4.4.2 Sink Capability Query (`0x0007`) and Response (`0x0008`)

Two forms: **long form** (full capabilities table) and **short form** (network latency / "heartbeat").

##### Table 4-19 — `0x0007` Header Fields

| Parameter | Value | Comments |
|---|---|---|
| Packet Type | Extension Control (`0x7`) | Requests Sink Capabilities Response |
| Packet Size | 13 words (long) / 12 words (short) | |
| Stream Identifier | Yes; SID = `0x00000000` when used in Information Class `0x0101` | Otherwise matches paired Data Stream SID |
| Class ID | Present (OUI `0x6A621E`, Packet Class `0x0007`) | |
| CIF 0 | Bit 31 = 0 → long form; bit 31 = 1 → short form | Long form: bit 30 (Reference Point), 21 (Sample Rate), 20 (Timestamp Adjustment), 2 (CIF 1). Short form: only bit 31 set |
| CIF 1 | Present in long form | Bit 1: Buffer Size |

##### `0x0007` Word Layout (long form, 13 words)

| Word | Contents |
|---|---|
| 1 | Header (Type=`0x7`) |
| 2 | Stream ID (or `0x00000000` for `0x0101`) |
| 3 | Pad + Reserved + OUI |
| 4 | Information Class + Packet Class (`0x0007`) |
| 5 | Integer Seconds Timestamp (issue time) |
| 6, 7 | Fractional Seconds Timestamp (issue time) |
| 8 | CAM Field |
| 9 | Message ID |
| 10 | Controllee ID |
| 11 | Controller ID |
| 12 | CIF 0 |
| 13 | CIF 1 |

##### `0x0007` Short Form Word Layout (12 words)

Replaces CIF 1 with: Word 12 = CIF 0 (bit 31 = 1); short form uses no further CIF/data fields beyond timing. Total = 12 words. (See note: alternate short-form variant carries Sink Time Calibration in Words 13–15 per §4.4.3 — used by Source to convey approximate Source-clock vs Sink-clock offset.)

##### CAM Field for `0x0007`

| Bits | Field | Value | Notes |
|---|---|---|---|
| 31, 29 | Controllee/Controller ID Indicator | `1` | Include 32-bit IDs |
| 30, 28 | ID Format | `0` | 32-bit IDs |
| 27–25 | Unused | `0` | |
| 24–23 | Action Mode | `10` (`0x2`) | Execute (implied = respond with `0x0008`) |
| 22–21 | Unused / Reserved | `0` | |
| 20–18 | Acknowledge Type Requested | `100` | Validation Acknowledgement |
| 17–16 | Req-W / Req-Er | `0` | N/A |
| 15 | Reserved | `0` | |
| 14–12 | Timestamp Control Mode | `0` | Sink responds as quickly as timing allows |
| 11–8 | Acknowledge Bits | `0` | Control packet |
| 7–0 | Reserved | `0` | |

##### Sink Time Calibration Field (Short Form, Words 13–15)

Source conveys approximate offset between Source Clock (TOD) and Sink Clock:
- Word 13: integer-second portion of offset
- Words 14–15: fractional-second portion (sample periods if TSF=Sample Count; picoseconds if TSF=Real Time)

##### Table 4-20 — `0x0008` Sink Capabilities Response Acknowledge

Two forms: long (variable length, capabilities table) and short (18 words, latency/heartbeat).

###### Short form (18 words)

| Word | Contents |
|---|---|
| 1 | Header (Type=`0x7`, Ack indicators set) |
| 2 | Stream ID |
| 3, 4 | Pad/OUI/Info+Packet Class |
| 5 | Integer Timestamp |
| 6, 7 | Fractional Timestamp |
| 8 | CAM (Acknowledge mode bits set) |
| 9 | Message ID (matches Query) |
| 10 | Controllee ID |
| 11 | Controller ID |
| 12 | CIF 0 (bit 31 = 1 → short form) |
| 13 | Integer-Second Timestamp of Control Packet (echoed) |
| 14, 15 | Fractional-Second Timestamp of Control Packet (echoed) |
| 16 | Integer-Second Time at Sink at Reception of Control Packet |
| 17, 18 | Fractional-Second Time at Sink at Reception of Control Packet |

###### Long form (variable length, full capabilities)

Contents (illustrative — actual word numbers depend on counts):

| Section | Field | Notes |
|---|---|---|
| Header | Words 1–7 | Same as short form |
| Identity | CAM (W8), Message ID (W9), Controllee ID (W10), Controller ID (W11) | |
| CIFs | CIF 0 (W12, bit 31 = 0 → long form; same bits as `0x0007` long form), CIF 1 (W13, bit 1 set for Buffer Size) | |
| **Information Classes** | Word 14 bits 31–16: count N (uint16); next N×16-bit codes = supported Info Classes | Pad final 16 bits with 0 if N is even |
| **Reference Points** | Word: bits 31–16 reserved (0); bits 15–0 = count; next 32-bit words list Reference Point IDs | |
| **Sample Rates and Bandwidths** (discrete) | bit 15 = 1 → discrete; bits 14–0 = count N. Followed by N×Sample Rate (64-bit) then N×Maximum Bandwidth (64-bit) | |
| **Sample Rates and Bandwidths** (range) | bit 15 = 0; bit 0 = 0 (fixed spacing) or 1 (fixed ratio). Min Sample Rate (64-bit), Max Sample Rate (64-bit), Resolution OR Ratio (64-bit), Min Sample-Rate-to-Bandwidth ratio (32-bit unsigned fixed point, radix at bit 15) | |
| **IF Reference Frequencies** (discrete) | bit 15 = 1; count N; N×64-bit IF Reference Frequencies | |
| **IF Reference Frequencies** (range) | bit 15 = 0; count N ranges; per-range: Min Freq (64-bit), Max Freq (64-bit), Resolution (64-bit) | Multiple ranges support band cutouts |
| **RF Reference Frequencies** (discrete or range) | Same format as IF Reference Frequencies | |
| **IF Band Offsets** (discrete) | bit 15 = 1; count N; N×64-bit IF Band Offsets (signed) | |
| **IF Band Offsets** (range) | bit 15 = 0; Min (64-bit, signed), Max (64-bit), Resolution (64-bit unsigned) | |
| **Reference Level Capabilities** | Word X bits 31–16: Min Reference Level (dBm, unsigned fixed point, radix at bit 23). Bits 15–0: Max Reference Level (radix at bit 7). Word X+1 bits 31–16: Resolution (dB, radix at bit 23); bits 15–0 = `0x0000` reserved | |
| **Timestamp Adjustment** (optional) | 64-bit two's-complement signed, femtoseconds. SID-to-Reference-Point delay. Set to 0 if not provided (Source disregards) | |
| **Data Payload Format & Stream Capability** | Bits 31–19: 13-bit Bit-Depth Indicator (bit 31 = 16-bit, bit 19 = 4-bit support). Bits 18–16: reserved. Bits 15–0: Max Number of Simultaneous Streams (uint16) | |
| **Buffer Size** | 64-bit unsigned int, bytes | |
| **Nearly Late Time Threshold** | 64-bit signed two's-complement; ps if TSF=Real Time, sample periods if TSF=Sample Count | Negative threshold → Late error if packet timestamp > Sink time; warn if within threshold. Positive threshold → Late error at TS + threshold; warn between TS and TS + threshold |
| **Link Active Timeout Period** | 64-bit | Time Sink waits in Link Active without valid packet before issuing Status Report (Link Active Timeout) and entering Link Tear Down |
| **Context Error Timeout Period** | 64-bit | Time Sink waits in Context Error without valid Context Packet before issuing Status Report (Context Error Timeout) and entering Link Tear Down |

##### Long Form vs Short Form Selection

- **Long form** (`0x0007` bit 31 = 0 in CIF 0): Source queries detailed Sink capabilities; Sink responds with full table
- **Short form** (`0x0007` bit 31 = 1): network latency/jitter characterization or heartbeat; only timestamp echoed

---

#### 4.4.3 Status Report Control Packet (`0x0009`)

##### Table 4-21 — `0x0009` Header / Field Summary

| Parameter | Value | Comments |
|---|---|---|
| Packet Type | Extension Control (`0x7`) | Sink → Source status |
| Packet Size | 15 / 17 / 21 words (depends on Status Code Payload + optional Quantitative Flags) | |
| Stream Identifier | Yes (matches paired Data Stream SID) | |
| Class ID | Present (OUI, Packet Class `0x0009`) | |
| CAM Field | Present | Acknowledge mode bits |
| Error Code Payload | Present | Format per Table 4-30 |

##### `0x0009` Word Layout

| Word | Contents |
|---|---|
| 1–7 | Standard prologue (Type=`0x7`, ...) |
| 8 | CAM Field |
| 9 | Message ID |
| 10 | Controllee ID/UUID (default `0x00000000`) |
| 11 | Controller ID/UUID (default `0x00000000`) |
| 12 | CIF 0 |
| 13–14 | Status Code Payload (2, 4, or 8 words) |
| 15+ | Quantitative Flags (optional): Reference Level Limit, Sample Rate Limit, Bandwidth Limit |

##### Issuance

Sinks shall issue `0x0009` promptly when a new error is detected. Periodically issue at user-determined rate 1–100 packets/sec. When no errors active, issue with all bits 0 ("all clear"). Persistent errors flagged in subsequent periodic packets until resolved.

##### Table 4-30 — Error Code Fields (Word 1 of Status Code Payload)

**Packet-Related Errors (Word 1):**

| Bit | Error |
|---|---|
| 31 | Selected Packet Type not defined |
| 30 | Selected TSM not allowed |
| 29 | Selected TSI not allowed |
| 28 | Selected TSF not allowed |
| 27 | Incorrectly Specified Packet Size |
| 26 | Specified Pad Bit Count not permitted |
| 25 | Specified Information Class not defined |
| 24 | Specified Packet Class not in Information Class |
| 23 | Packet Class not defined |
| 22 | Late Context Packet arrival |
| 21 | Late Data Packet arrival |
| 20 | Reference Point not recognized |
| 19 | Bandwidth too large for sample rate |
| 18 | Fractional Hz specified |
| 17 | IF Reference Frequency resolution error |
| 16 | IF Reference Frequency out of range |
| 15 | RF Reference Frequency resolution error |
| 14 | RF Reference Frequency out of range |
| 13 | IF Offset too large |
| 12 | Reference Level mismatch |
| 11 | Sample rate resolution error |
| 10 | Sample rate out of range |
| 9 | Data Payload Config incorrectly specified |
| 8 | Unsupported Bit Depth |
| 7 | Frequency Allocation Conflict |
| 6 | Simultaneous Stream Capacity Exceeded |
| 5 | Sink bandwidth capability exceeded |
| 4 | Timeout/Link Termination |
| 3–0 | Reserved |

**Sink-Related Errors (Word 2, bits 31–25):**

| Bit | Error |
|---|---|
| 31 | Frequency LOL (loss of lock) causing data stoppage |
| 30 | Time base LOL causing data stoppage |
| 29 | Buffer Underflow |
| 28 | Buffer Overflow |
| 27 | Beam Interference (Tx blocked) |
| 26 | Context Error Timeout (S4 → S5 transition) |
| 25 | Link Termination (S5 → S1 transition) |
| 24–16 | Reserved |

**Warnings (Word 2, bits 15–0):**

| Bit | Warning |
|---|---|
| 15 | Probable Context Packet Drop |
| 14 | Probable Data Packet Drop |
| 13 | Nearly Late Context Packet Arrival |
| 11 | Nearly Late Data Packet Arrival |
| 10–5 | Reserved |
| 4 | Reference Level Limit (quantitative field included) |
| 3 | Sample Rate & Bandwidth Limits (quantitative fields included) |
| 2–0 | Reserved |

**Quantitative Flag Fields (Words 5–8 of Status Code Payload, optional):**

| Word | Field |
|---|---|
| 5 | Reference Level Maximum Supported (dBm) + Reference Level Minimum Supported (dBm) |
| 6 | Reference Level Resolution (dB) + Reserved |
| 7 | Maximum Sample Rate Supported (64-bit, two words) |
| 8 | Maximum Bandwidth Supported (64-bit, two words) |

---

## 5. Stream and Reference Point ID

### 5.1 Stream Identifier (SID) and SID Location

Three functions:
1. Indicates Data/Context/Command Packet is part of a sequence sharing the same Stream ID
2. Indicates which Context/Command streams are associated with which Data streams
3. Defines the **SID location** — used with timestamping

DIFI mandates the SID, Integer Seconds Timestamp, and Fractional Seconds Timestamp ("Prologue Timestamp") in Data Packets.

#### Prologue Timestamp meaning

Prologue Timestamp = time first sample in a Data Packet is present at the SID location.
First sample at Reference Point = Prologue Timestamp + Timestamp Adjustment (see §5.2).

#### SID Location Rules (by device category)

| Device Category | SID Location |
|---|---|
| (i) Analog → DIFI converter (source) | Point of generation of digital samples within the ADC (Figures 13, 14) |
| (ii) DIFI → analog converter (sink) | Point of consumption of samples within the DAC (Figures 15, 16) |
| (iii) Intermediate digital-in/digital-out device | Rx path: point of generation of digital samples; Tx path: point of operation on samples (e.g., combining), after any buffering (Figures 17, 18) |
| IF replication ("bookend": IF→DIFI→IF) | Point of generation of digital samples within the category-(i) device (Figure 19) |

For Use Cases that are non-Time Release, the SID location shall be the output of the packetizer in the DIFI Source.

### 5.2 Reference Point Identifier and Timestamp Adjustment

The Reference Point Identifier identifies a location, **other than the SID location**, to which certain parameters apply (Timestamp Adjustment, Reference Level, reference frequencies). Mandatory fields.

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
- Example (Figure 27, Reference Point 100): Timestamp Adjustment = `T100 − TSID`

#### Reference Configuration Examples

- **Figure 20** — Receive with IFC; RP 100 preferred. Context contains RP=100, Reference Level (dBm at RP producing full-scale sine in payload), pre-conversion analog gain, post-conversion digital gain
- **Figure 21** — Transmit with IFC; RP 100 preferred. Context contains RP=100, Reference Level (dBm at RP from full-scale sine input)
- **Figure 22** — Receive with RFC; RP 75 preferred
- **Figure 23** — Transmit with RFC; RP 75 preferred. Reference Level = intended power dBm at RP
- **Figure 24** — Tx with DIFI-interface ESA; RP 15 (air interface). Reference Level = intended EIRP in dBm at air interface
- **Figure 25** — Tx with intermediate DIFI→DIFI device + IFC; RP 100 used by Combiner output. Reference Level for the other two streams has no meaning; their RP/SID location still used for timing/sync
- **Figure 26** — Like Figure 25 but with RFC; RP 75 used by Combiner output stream

---

## 6. Link Establishment / Negotiation

### 6.1 Background

DIFI link establishment sets up streams between devices, negotiating parameters in-band. There is no system master; each device is configured by the system designer as Controller or Controllee. Devices may be physical or virtual — there is no 1:1 IP-to-Controller/Controllee relationship. Each (physical or logical) device must have a unique Controller ID and Controllee ID (§6.3).

**Configured out-of-band:** IP addresses (management + data), UDP ports, Stream IDs.

Link establishment heavily leverages Command Packet capability and the CAM mode (VITA 49.2 §8).

### 6.2 Link Establishment Process — State Diagram

States (apply per-link, not per-device):

| State | Purpose |
|---|---|
| **S1: Link Idle** | Initial state; no link established |
| **S2: Link Capabilities Query** | Source has issued `0x0007` (long-form); awaiting `0x0008` |
| **S3: Link Active** | Context + Data flowing; optional Timing Flow Control + Status Reports |
| **S4: Context Error** | Sink detected error in Context; awaiting valid Context |
| **S5: Link Tear Down** | Sink announcing end of session |

#### Transition Rules

| From | To | Trigger |
|---|---|---|
| S1 | S2 | Source issues Sink Capabilities Query Control Packet (long form) |
| S2 | S1 | Sink Capabilities Response Acknowledge Packet not received by Source |
| S2 | S3 | Query success + compatible parameters; first Signal Flow Context Packet sent |
| S3 | S3 | Short-form Query/Response packets exchanged; Sink/Source emit Timing Flow Control; Sink issues clear Status Report Control Packets at user-defined rate |
| S3 | S4 | Sink detects Context Packet error; issues Status Report Control Packet |
| S4 | S3 | Source issues corrected/subsequent Context Packet |
| S4 | S5 | Valid Context Packet not received within Context Error Timeout; Sink issues Status Report with Context Error Timeout |
| S3 | S5 | No valid packet for time exceeding Link Active Timeout; OR Sink initiates Tear Down with Link Termination bit |
| S5 | S1 | Sink issues Status Report with Link Termination bit (or two Status Reports for UDP redundancy: one Timeout + one Termination, or two Termination); Source transitions on receipt of either |

#### State-by-state details

**S1 — Link Idle:** Initial. Transition to S2 via long-form `0x0007`.

**S2 — Link Capabilities Query:** Sink responds with long-form `0x0008` listing power, bandwidth, IF freq, bit widths, etc. Failure → back to S1. Compatibility found → S3.

**S3 — Link Active:**
- Context + Data packets sent/received
- Signal data processing **muted** until valid Context received
- Context out-of-bounds → Status Report + transition to S4
- Data Packet error → Status Report; **stay in S3**
- Sink Tx errors (e.g., loss of lock) → Sink mutes + Status Report; stays in S3. Sink should issue Status Reports at rate similar to Signal Context packet rate during Sink Error
- Timeout exceeded (no valid packets) → S5
- Sink may enter S5 at any time if controlling continuation

**S4 — Context Error:**
- Sink sends Status Report with all parameter errors detected
- Sink **disregards** Data Packets timestamped concurrently with or after errant Context until valid Context received
- Source responds with valid Context Packet (may re-issue corresponding Data Packets if appropriate). Transition to S3 on valid Context
- Timeout without valid Context → S1 via S5

**S5 — Link Teardown:** Three triggers:
1. **Source initiated:** Source intentionally sends no packets for Timeout period. Sink enters S5, issues Status Report with Timeout Error bit
2. **Sink initiated:** Sink directly enters S5, issues Status Report with Link Termination bit
3. **Link quality:** Network problem prevents valid packets for Timeout. Sink → S5, Status Report with Timeout Error bit

Sink issues Status Report with Link Termination bit signaling transition to S1. Because UDP packets may drop and there's no Acknowledge to Status Report Control Packets, Sink issues either:
- One Status Report with Timeout Error bit + one with Link Termination bit, OR
- (Sink-initiated tear down) two Status Reports with Link Termination bit

Source transitions to S1 on receipt of either.

### 6.3 Controller / Controllee UUID Assignment

Devices initially assigned numbers but not specifically as Controller/Controllee — the role is configured out-of-band per Control Packet exchange. Each device is identified by its number (32-bit numbers MUST NOT be reused). The issuer of a Control Packet places its number in the Controller ID field and the recipient's number in the Controllee ID field.

---

## Cross-Reference Index

### By Field — where defined

| Field | Section / Word |
|---|---|
| Bandwidth | §4.3.1 / Words 10, 11 |
| Buffer Level / Status | §4.4.1 / Word 21 |
| Buffer Size | §4.4.1 / Words 19–21 (3 words, DIFI deviation) |
| CAM Field | §4.4.1 / Word 8 (Table 4-23) |
| CIF 0 | §4.3.1 / Word 8; §4.3.2 / Word 8; §4.4.1 / Word 12; §4.4.2 / Word 12 (`0x0007`/`0x0008`) |
| CIF 1 | §4.3.2 / Word 9; §4.4.1 / Word 13; §4.4.2 / Word 13 (`0x0007`/`0x0008`) |
| Class Identifier | §4.1 / Words 3, 4 |
| Context Error Timeout Period | §4.4.2 (`0x0008` long form) |
| Controllee ID | §4.4.1 / Word 10 |
| Controller ID | §4.4.1 / Word 11 |
| Data Item Format | §4.3.1 / Words 26, 27 |
| Data Packet Payload Format | §4.3.1 / Words 26, 27 |
| Error Code Payload | §4.4.3 / Table 4-30 |
| Fractional-Seconds Timestamp | §4.1 / Words 6, 7 |
| Gain | §4.3.1 / Word 19 |
| IF Band Offset | §4.3.1 / Words 16, 17 |
| IF Reference Frequency | §4.3.1 / Words 12, 13 |
| Information Class Code | §4.1 / Word 4 bits 31–16 |
| Integer-Seconds Timestamp | §4.1 / Word 5 |
| Link Active Timeout Period | §4.4.2 (`0x0008` long form) |
| Maximum Number of Simultaneous Streams | §4.4.2 (`0x0008` long form) |
| Message ID | §4.4.1 / Word 9 |
| Nearly Late Time Threshold | §4.4.2 (`0x0008` long form) |
| OUI | §4.1 / Word 3 bits 23–0 (always `0x6A621E`) |
| Packet Class Code | §4.1 / Word 4 bits 15–0 |
| Packet Header | §4.1 / Word 1 |
| Packet Size | §4.1 / Word 1 bits 15–0 |
| Packet Type | §4.1 / Word 1 bits 31–28 |
| Pad Bit Count | §4.1 / Word 3 bits 31–27 |
| Reference Level | §4.3.1 / Word 18 bits 15–0 |
| Reference Level Capabilities | §4.4.2 (`0x0008` long form) |
| Reference Point | §4.3.1 / Word 9; §4.4.1 / Word 14 |
| RF Reference Frequency | §4.3.1 / Words 14, 15 |
| Sample Rate | §4.3.1 / Words 20, 21; §4.4.1 / Words 15, 16 |
| Scaling Level | §4.3.1 / Word 18 bits 31–16 |
| SeqNum | §4.1 / Word 1 bits 19–16 |
| Sink Time Calibration | §4.4.2 (`0x0007` short form Words 13–15) |
| State and Event Indicators | §4.3.1 / Word 25 |
| Stream Identifier (SID) | §4.1 / Word 2 |
| Supported Bit Depths | §4.4.2 (`0x0008` long form, 13-bit Bit-Depth Indicator) |
| Supported Information Classes | §4.4.2 (`0x0008` long form) |
| Supported IF Reference Frequencies | §4.4.2 (`0x0008` long form) |
| Supported RF Reference Frequencies | §4.4.2 (`0x0008` long form) |
| Supported IF Band Offsets | §4.4.2 (`0x0008` long form) |
| Supported Reference Points | §4.4.2 (`0x0008` long form) |
| Supported Sample Rates and Bandwidths | §4.4.2 (`0x0008` long form) |
| Timestamp Adjustment | §4.3.1 / Words 22, 23; §4.4.1 / Words 17, 18; §4.4.2 (`0x0008` long form) |
| Timestamp Calibration Time | §4.3.1 / Word 24 |
| Timestamp Fractional (TSF) | §4.1 / Word 1 bits 21–20 |
| Timestamp Integer (TSI) | §4.1 / Word 1 bits 23–22 |
| Timestamp Mode (TSM) | §4.3.1 / Word 1 bit 24 |
| V49 Spec Version | §4.3.2 / Word 10 |
| Year/Day/Revision/Type/ICD Version | §4.3.2 / Word 11 |
