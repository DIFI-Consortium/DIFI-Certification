# DIFI Standard v1.1 — AI Reference

## 0. Quick Reference (Cheat Sheet)

### DIFI Constants

| Item | Value | Notes |
|---|---|---|
| DIFI OUI / CID | `0x6A621E` (canonical `6A-62-1E`) | Issued to DIFI by IEEE; goes in OUI field of every Class Identifier |
| Reference Point ID | `0x64` (decimal 100) | RF input (RF-to-IP) or RF output (IP-to-RF) |
| V49 Spec Version code | `0x4` | Indicates VITA 49.2 |
| ICD Version code | `0` | Means DIFI v1.x |
| TSF (fractional timestamp) | `0x2` | Always picoseconds |
| TSM (timestamp mode) on context | `0x1` | "general timing" for context changes |
| Context-packet header packet-type | `0x4` | Context packet with stream ID |
| Data-packet header packet-type | `0x1` | Data packet with stream ID |
| Class ID present bit | `0x1` | Set in header bit 27 |

### Packet Classes

| Packet | Class Code | Information Class | Fixed Size |
|---|---|---|---|
| DIFI IQ Signal Data | `0x0000` | `0x0000` | Variable (header + payload) |
| DIFI IQ Signal Context | `0x0001` | `0x0000` | 27 words (108 bytes) |
| DIFI Version Flow Signal Context | `0x0004` | `0x0001` | 11 words (44 bytes) |

### Packet Rates

| Stream | Allowed Rate |
|---|---|
| Standard Flow Signal Context | 0–20 packets/sec (also: send on any field change) |
| Version Flow Signal Context | 0–100 packets/sec |
| Standard Flow Signal Data | As needed for sample rate / packet size |

### Stream ID Convention

- **Even-numbered** stream IDs → RF-to-IP direction
- **Odd-numbered** stream IDs → IP-to-RF direction
- Purpose: avoid Reference Point ambiguity. Context and Data packets sharing a stream MUST share the same Stream ID.

### Header Layout (common to all DIFI packets, Word 1)

| Bits | Field | Data Packet | Context Packet (Standard / Version) |
|---|---|---|---|
| 31–28 | Packet Type | `0x1` | `0x4` |
| 27 | Class ID present | `0x1` | `0x1` |
| 26–25 | Reserved | `0x0` | `0x0` |
| 24 | TSM / Spectrum-Time | `0x0` (= time, not spectrum) | `0x1` (= general timing) |
| 23–22 | TSI (Timestamp Integer source) | UTC/GPS/POSIX | UTC/GPS/POSIX |
| 21–20 | TSF (Timestamp Fractional) | `0x2` (picoseconds) | `0x2` (picoseconds) |
| 19–16 | Sequence Number | mod 16 per stream | mod 16 per stream |
| 15–0 | Packet Size (32-bit words) | header + payload | 27 (Standard) / 11 (Version) |

### TSI Codes (Timestamp Integer source — Word 1, bits 23-22)

| Code | Meaning |
|---|---|
| `00` | Not allowed (because TSI is used in data packets) |
| `01` | UTC — epoch 1970-01-01, includes leap seconds |
| `10` | GPS — epoch 1980-01-06, no leap seconds |
| `11` | POSIX — epoch 1970-01-01, no leap seconds |

### ICD Version Codes (Version packet, bits 5-0 of Version word)

| Code | Meaning |
|---|---|
| `0` | DIFI v1.x |
| `1`–`31` | Reserved |

---

## 1. Introduction

DIFI defines a data-plane interface for transmitting digitized RF or IF samples (and corresponding metadata) over standard IP networks. It is **fully compliant with VITA 49.2**.

Two independent flows are defined:
1. **RF-to-IP** — RF/IF input → IP-network output
2. **IP-to-RF** — IP-network input → RF/IF output

All digitized RF/IF samples are **complex, fixed-point signed numbers**, with I and Q each ranging from **4 through 16 bits**.

VITA trailers and VRL framing are **not used** in any DIFI flow.

### 1.4 Abbreviations

| Acronym | Meaning |
|---|---|
| ADC | Analog to Digital Converter |
| ARP | Address Resolution Protocol |
| CIF | Context Indicator Field |
| DAC | Digital to Analog Converter |
| FPGA | Field-Programmable Gate Array |
| GPS | Global Positioning System |
| I | In-phase component |
| Q | Quadrature component |
| ICD | Interface Control Document |
| ID | Identifier |
| IEEE ISTO | IEEE Industry Standards and Technology Organization |
| IF | Intermediate Frequency (any signal after frequency translation; zero-IF = complex baseband) |
| IFC | IF Converter |
| IP / IPv4 / IPv6 | Internet Protocol (v4 / v6) |
| IRIG | Inter-range Instrumentation Group timecodes (e.g., IRIG-B, IRIG-C) |
| LAN | Local Area Network |
| MAC | Media Access Control |
| NIC | Network Interface Controller |
| NTP | Network Time Protocol |
| OUI | Organizationally Unique Identifier |
| POSIX | Portable Operating System Interface |
| RF | Radio Frequency |
| TSF | Timestamp Fractional |
| TSI | Timestamp Integer |
| TSM | Timestamp Mode |
| UDP | User Datagram Protocol |
| UTC | Coordinated Universal Time |
| VITA | VME bus International Trade Association |
| VLAN | Virtual LAN |
| VRL | VITA Radio Link Protocol |
| VRT | VITA Radio Transport |

---

## 2. Data Plane Implementation

### 2.1 Protocol Stack

```
+----------------------------------+
| DIFI Protocol Layer              |   Context Packet | Signal Data Packet
+----------------------------------+
| User Datagram Protocol (UDP)     |
+----------------------------------+
| IPv4   or   IPv6                 |
+----------------------------------+
| Ethernet (802.3)                 |
+----------------------------------+
```

### Packet Layout (Frame Overhead)

| Layer | Size |
|---|---|
| IP header | 20 octets (IPv4) / 40 octets minimum (IPv6) |
| UDP header | 8 octets |
| VITA header | 28 octets (= 7 × 32-bit words) |
| **Total fixed overhead inside Ethernet frame** | **56 octets (IPv4) / 76 octets minimum (IPv6)** |

Other size constants:
- Signal Data Packet = `7 + N` words (header + N-word payload)
- Signal Context Packet = `7 + 20` = 27 words
- Version Context Packet = `7 + 4` = 11 words
- Ethernet payload size: 128 octets to 9000 octets (jumbo); upper limit vendor-dependent.

### 2.1.1 Ethernet (Requirements)

- DIFI packets **shall** be in standard 802.3 Ethernet frames.
- **Shall** support jumbo frames (MTU 9000 bytes).
- **Shall** support 802.1Q (VLAN) and 802.1ad (QinQ).
- A DIFI endpoint **shall** have at least one Ethernet MAC address.

### 2.1.2 IP

- DIFI packets **shall** be in IPv4 (RFC 791) or IPv6 (RFC 8200) frames.
- For a given DIFI stream, the **source IP address shall be the same** for both context and data packets.
- **IPv4 fragmentation shall not be supported.**
- **IPv6 extension headers shall be supported** (i.e., their presence accepted). Implementations **may** ignore extension-header content but **shall** still process the IPv6 payload.

### 2.1.3 UDP

- Each DIFI packet **shall** be in a standard UDP datagram.
- **UDP checksums are mandatory in DIFI** (required by IPv6, optional in plain IPv4 — DIFI tightens this to "always required and valid" for both IPv4 and IPv6).
- UDP payload contains exactly one DIFI context packet OR one DIFI data packet.

---

## 2.2 Context Packets

Two types of context packet exist in DIFI:

| Data Flow | Context Packet | Class Code |
|---|---|---|
| Standard | Signal Context | `0x0001` |
| Version | Version Signal Context | `0x0004` |

VITA 49.2 renamed the original "IF Context" packet to **Signal Context Indicator Field 0 (CIF 0)**.

Although VITA 49.2 has true control packets, DIFI uses Standard Flow Signal Context Packets as a **pseudo-control mechanism** for backwards compatibility. Real-time action on context packets is application-dependent (out-of-band management beyond this standard's scope).

Context packets may also be consumed passively by monitoring devices (e.g., a virtual spectrum analyzer) that are not the addressed recipient.

### 2.2.1 Packet Rate

- The standard flow signal data stream emitter **shall** be capable of producing Standard Flow Signal Context Packets.
- **Standard Flow Signal Context Packet rate**: 0 (off) through 20 packets/sec, for any stream-rate / sample-size / data-packet-size combination.
- **Standard Flow Signal Context Packet shall additionally be transmitted on change of any context field** (e.g., Reference Amplitude).
- **Version Flow Signal Context Packet rate**: 0 (off) through 100 packets/sec.

---

### 2.2.2 Standard Flow Signal Context Packet (Class `0x0001`)

Same format for RF-to-IP and IP-to-RF directions. Total = **27 words (108 bytes)**.

#### Word-by-Word Layout

| Word(s) | Field |
|---|---|
| 1 | Header |
| 2 | Stream ID |
| 3–4 | Class Identifier |
| 5 | Integer-seconds Timestamp |
| 6–7 | Fractional-seconds Timestamp (picoseconds) |
| 8 | Context Indicator Field 0 (CIF 0) |
| ... | CIF 0 metadata fields (see below) |

#### Header (Word 1) — Bit-level

| Bits | Field | Required Value / Notes |
|---|---|---|
| 31–28 | Packet Type | `0x4` (Context with Stream ID) |
| 27 | Class Identifier present | `0x1` |
| 26–25 | Reserved | `0x0` |
| 24 | TSM | `0x1` (general timing for context changes) |
| 23–22 | TSI | UTC / GPS / POSIX (see TSI table) |
| 21–20 | TSF | `0x2` (picoseconds) |
| 19–16 | Sequence Number | Increments mod 16 per context packet |
| 15–0 | Packet Size | `27` (fixed) |

#### Stream ID (Word 2)

- Default `0`; any unsigned 32-bit value allowed.
- **Must match** the Stream ID of associated Signal Data packets.
- See VITA 49.2 §5.1.2.

#### Class Identifier (Words 3–4)

- **Padding Bits (bits 31–27):** `0` (padding not permitted)
- **Reserved Bits (bits 26–24):** `0` (per VITA 49.2 Rule 5.1.3-5)
- **OUI (bits 23–0):** `0x6A621E` (DIFI's IEEE-issued CID; canonical form `6A-62-1E`)
- **Information Class Code (bits 31–16 of word 4):** Defaults `0x0000`. May be any 16-bit value in RF-to-IP direction; **ignored in IP-to-RF**.
- **Packet Class Code (bits 15–0 of word 4):** Defaults `0x0000` (= "DIFI IQ Signal Context" → corrected: in this packet, class is `0x0001`). May be any 16-bit value RF-to-IP; ignored IP-to-RF.

#### Timestamps

- **Integer-seconds (Word 5):** Seconds since epoch for selected TSI source. Only UTC includes leap seconds. (VITA 49.2 §5.1.4–5.1.5.)
- **Fractional-seconds (Words 6–7):** Picoseconds past the integer seconds.

#### CIF 0 — Standard Signal Context Fields

The following **must** be included for RF-to-IP, and is the **minimum set** for IP-to-RF (additional fields in IP-to-RF are ignored). VITA 49.2 §9 has full details.

| Field | Description | RF-to-IP role | IP-to-RF role |
|---|---|---|---|
| **Reference Point** | Where in the system the samples refer to. Value `0x64`. | RF input | RF output |
| **Bandwidth** | Useable bandwidth of digitized signal, in 1 Hz increments (VITA 49.2 §9.5.1) | configured | configured |
| **IF Reference Frequency** | IF center frequency. Default `0` (zero-IF). (VITA 49.2 §9.5.5) | configured | configured |
| **RF Reference Frequency** | Center freq. of RF input port (RF-to-IP) or RF output port (IP-to-RF). RF-ref-freq is **status only** in IP-to-RF; the output center frequency is independently programmed (allows frequency translation). (§9.5.10) | actual RF | status only; programmed independently |
| **IF Band Offset** | Stream offset from IF center. Signed, 1 Hz resolution. Defaults to `0`. Stream bandwidth must stay within system bandwidth. RF-to-IP: stream offset. IP-to-RF: default stream offset (overridable). (§9.5.4) | stream offset | default; overridable |
| **Reference Level** | Power in **dBm** representing full-scale max-positive value. RF-to-IP: levels at the ADC analog reference point. IP-to-RF: levels at the DAC analog reference point. (§9.5.9, example §B.6) | ADC ref level | DAC ref level |
| **Gain/Attenuation** | Two stages, in dB. Stage 1 = analog-input gain pre-ADC + digital gain in equalizer post-ADC. Stage 2 = digital gain in post-ADC stream. In IP-to-RF, gain values are status (used for end-to-end path gain). (§9.5.3, example §B.7) | applied | status |
| **Sample Rate** | Sampling rate of samples in Signal Data packets. (§9.5.12) | configured | configured |
| **Timestamp Adjustment** | Adjustments for implementation delays, picoseconds. Defaults `0`. (§9.7.3.1) | as needed | as needed |
| **Timestamp Calibration Time** | Last time timestamp was known correct. Populated RF-to-IP for apps needing lock history. (§9.7.3.3) | populated | — |
| **State and Event Indicators** | Conveys lock states. **Bit 19 = calibrated time lock**, **Bit 17 = frequency reference lock**. Time refs: IRIG-B / IRIG-DC / 1PPS / NTP / GPS. Freq refs: 10 MHz / IRIG-B / IRIG-DC / 1PPS / GPS. Lock status updated ~1× per second. IP-to-RF uses these to decide if Programmed Delay mode is OK and whether end-to-end (Measured Delay) or Network Delay can be measured. **If RF-to-IP bit 19 (calibrated time) is not locked, Measured and Network Delays are forced to 0.** (§9.10.8) | populated | consumed |
| **Data Packet Payload Format** | Required to interpret samples. **Complex Cartesian (I/Q), link-efficient packing, signed fixed-point, no event/channel tags, sample sizes 4–16 bits, no sample-component repeats, no unused bits.** (§9.13.3) | populated | consumed |

---

### 2.2.3 Version Flow Signal Context Packet (Class `0x0004`)

Conveys **type and version** information and **precise time of day** for software apps creating an IP-to-RF flow (uplink) without an RF-to-IP flow (downlink). Created on the RF-to-IP side; used on the IP-to-RF side to **auto-select a compatible packet format** when possible. May optionally be used on IP-to-RF flows when applicable.

Total = **11 words (44 bytes)**. Uses the new VITA 49.2 CIF 1 indicator field for version metadata (§9.1).

#### Layout (TSI/SeqNum/Packet-Size/Stream-ID/Timestamps as in §2.2.2)

| Word(s) | Field |
|---|---|
| 1 | Header (packet size = 11) |
| 2 | Stream ID |
| 3–4 | Class Identifier |
| 5 | Integer-seconds Timestamp |
| 6–7 | Fractional-seconds Timestamp |
| 8 | CIF 0 |
| 9 | CIF 1 |
| 10 | V49 Spec Version |
| 11 | Version word |

#### Class Identifier (Words 3–4)

- **Padding Bits (31–27):** `0`
- **Reserved Bits (27–24):** `0` (per VITA 49.2 Rule 5.1.3-5)
- **OUI (23–0):** `0x6A621E`
- **Information Class Code (31–16 of word 4):** **MUST be `0x0001`** — cannot be changed. The IP-to-RF side uses this to auto-configure to a compatible mode.
- **Packet Class Code (15–0):** **MUST be `0x0004`**.

#### CIF 0 (Word 8)

Indicates which optional CIF 0 metadata fields are included AND if values changed since the last context packet.

- `0x80000002` → CIF 1 included **and** field changed
- `0x00000002` → CIF 1 included, no change
- These are the **only** allowed CIF 0 codes for the Version packet (only CIF 1 inclusion bit is set).

#### CIF 1 (Word 9)

- **`0x0000000C`** → only V49 Spec Version + Version field allowed. No other CIF 1 fields permitted.

#### V49 Spec Version (Word 10)

- **MUST = `0x4`** → indicates VITA 49.2.

#### Version Word (Word 11) — Bit Layout

| Bits | Field | Notes |
|---|---|---|
| 31–25 | Year | Year compiled, from 2000. (VITA 49.2 §9.10.4) |
| 24–16 | Day | Day-of-year compiled (Jan 1 = 1). |
| 15–10 | Revision | Distinguishes builds on same year/day. Normally `1`. |
| 9–6 | Type | User-defined device-type subfield (0..15). **MUST be `0x0`** (currently undefined). |
| 5–0 | ICD Version | `0` = DIFI v1.x. `1`–`31` reserved. |

---

## 2.3 Data Packets

| Data Flow | Data Packet | Class Code |
|---|---|---|
| Standard | Signal Data | `0x0000` |

### 2.3.1 Standard Flow Signal Data Packet (Class `0x0000`)

Same format for RF-to-IP and IP-to-RF.

#### Header — Bit-level

| Bits | Field | Required Value |
|---|---|---|
| 31–28 | Packet Type | `0x1` (Data with Stream ID) |
| 27 | Class ID present | `0x1` |
| 26–25 | Reserved | `0x0` |
| 24 | VITA 49.2 Spectrum/Time | `0x0` (= time data; spectrum data not supported by DIFI) — complies with VITA 49.2 Rule 6.3.1-2 |
| 23–22 | TSI | UTC / GPS / POSIX |
| 21–20 | TSF | `0x2` (picoseconds) |
| 19–16 | Sequence Number | mod 16 |
| 15–0 | Packet Size | 7 (header) + N (payload words) |

#### Packet Layout

| Word(s) | Field |
|---|---|
| 1 | Header |
| 2 | Stream ID |
| 3–4 | Class Identifier (OUI = `0x6A621E`, Information Class `0x0000`, Packet Class `0x0000`) |
| 5 | Integer-seconds Timestamp |
| 6–7 | Fractional-seconds Timestamp |
| 8 … 7+N | Signal Data Payload (N 32-bit words of packed I/Q samples) |

#### Sample Packing Rules

- **No sample padding allowed.** Every packet must contain an integer number of I/Q pairs.
- Each I/Q pair = `2 × sample-depth` bits.
- A whole number of complex samples must fit into a whole number of 32-bit units.
- Formal constraint:
  ```
  2 × <bits per sample> × <sample count granularity> = 32 × <32-bit unit granularity>
  ```
  All values must be whole numbers.

#### Sample-Count Granularity Table (Table 8 from spec)

For each I/Q sample bit-depth, the minimum number of complex samples per packet (samples must be a multiple of "sample count granularity"):

| Bits per sample | Sample count granularity | 32-bit unit granularity |
|---:|---:|---:|
| 4  | 4  | 1  |
| 5  | 16 | 5  |
| 6  | 8  | 3  |
| 7  | 16 | 7  |
| 8  | 2  | 1  |
| 9  | 16 | 9  |
| 10 | 8  | 5  |
| 11 | 16 | 11 |
| 12 | 4  | 3  |
| 13 | 16 | 13 |
| 14 | 8  | 7  |
| 15 | 16 | 15 |
| 16 | 1  | 1  |

**Worked examples (from spec):**
- 5-bit samples → 10-bit complex; 16 samples = 5 × 32 bits = 160 bits → multiples of 16 samples are legal.
- 6-bit samples → 12-bit complex; 8 samples = 3 × 32 bits = 96 bits → multiples of 8 samples are legal.
- 7-bit samples → 14-bit complex; 16 samples = 7 × 32 bits = 224 bits → multiples of 16 samples are legal.

---

## 3. Appendix — Class Definitions

DIFI defines the following classes per VITA 49.2 §5.1.3 conventions.

**Stream ID convention** (§3.1, repeated): even = RF-to-IP, odd = IP-to-RF, to disambiguate Reference Point direction.

---

### 3.1.1 Information Classes

#### 3.1.1.1 Information Class `0x0000` — DIFI basic dataplane-only configuration (Class Code 0)

| Component | Spec |
|---|---|
| Class Name / Code | "DIFI basic dataplane-only configuration" / `0x0000` |
| Purpose | "Convey digitized I and Q samples in either IP-to-RF or RF-to-IP direction, with all control and reference configuration communicated in advance or via non-VRT streams." |
| Packet Stream Names | 1. DIFI IQ Signal Data &nbsp; 2. DIFI IQ Signal Context |
| Packet Stream Purposes | 1. Convey IQ signal data &nbsp; 2. Convey data-stream context info |
| Packet Classes | 1. DIFI IQ Signal Data (§3.1.2) &nbsp; 2. DIFI IQ Signal Context (§3.1.2) |
| Packet Stream Details | 1. Packet size unrestricted, link-efficient packing, no zero padding, max 9000 bytes. Packet rate as needed. &nbsp; 2. Context packets sent on field change OR on user-set periodicity, whichever first. |
| Reference Point | `0x0064` (= 100). RF-to-IP → IFC RF input. IP-to-RF → IFC RF output. (See Recommendation 3.1.1.1-1) |
| Stream Associations | DIFI IQ Signal Data ↔ DIFI IQ Signal Context (paired) |

#### 3.1.1.2 Information Class `0x0001` — DIFI Version configuration (Class Code 1)

| Component | Spec |
|---|---|
| Class Name / Code | "DIFI basic dataplane-only configuration" / `0x0001` |
| Purpose | "Convey type/version info and precise time of day for software apps creating IP-to-RF data flow (uplink) and not using RF-to-IP (downlink)." |
| Packet Stream Names | 1. DIFI Version Flow Signal Context Packet |
| Packet Stream Purposes | 1. Convey type/version info &nbsp; 2. Convey time-of-day info |
| Packet Classes | 1. DIFI Version Flow Signal Context Packet |
| Packet Stream Details | 1. Fixed packet size = 11 words. &nbsp; 2. 0–100 packets/sec. |
| Reference Point | Not included — reference is the SID. |
| Stream Associations | None. |

---

### 3.1.2 Packet Classes

#### 3.1.2.1 Standard Flow Signal Data Packet — Class `0x0000`

| Section | Parameter | Selected Option | Comments |
|---|---|---|---|
| Header | Packet Type | Signal Data with Stream ID | Conveys digitized I/Q |
| Header | Packet Size | Variable, user-selected | No zero padding |
| Header | Stream Identifier | Yes | User-selected at runtime |
| Header | Class ID | Present | OUI `0x6A621E`, Packet Class `0x0000` |
| Header | Integer Timestamp | Present | UTC, POSIX, or GPS per header TSI |
| Header | Fractional Timestamp | Real-time, picoseconds | May be locked to external ref |
| Payload | Packing Method | Link Efficient | No zero padding; packet size chosen so payload fills integer 32-bit words |
| Payload | Data Item Size | Variable | I and Q each 4–16 bits → I/Q pair 8–32 bits |
| Payload | Item Packing Field Size | Variable, 2 × Data Item Size | — |
| Payload | Real/Complex | Complex Cartesian | — |
| Payload | Data Item Format | Signed fixed point | — |
| Payload | Sample/Channel repeating | N/A | No repeating |
| Payload | Repeat Count | 0 | — |
| Trailer | — | (Not Used) | — |

#### 3.1.2.2 Standard Flow Signal Context Packet — Class `0x0001`

Class Name: "DIFI IQ Signal Context"
Purpose: "Convey Context related to the DIFI IQ Data Packet Stream with which it is paired by Stream ID."

| Section | Parameter | Selected Option | Comments |
|---|---|---|---|
| Header | Packet Type | Context with Stream ID | Paired data stream context |
| Header | Packet Size | 27 words | — |
| Header | Stream Identifier | Yes | Matches paired Data Stream's SID |
| Header | Class ID | Present | OUI `0x6A621E`, Packet Class `0x0001` |
| Header | Integer Timestamp | Present | UTC/POSIX/GPS per header TSI |
| Header | Fractional Timestamp | Real-time, picoseconds | May be locked externally |
| Context | Context Field Change Indicator | Present | — |
| Context | Reference Point Identifier | Present | `0x0064` — IFC RF input (RF-to-IP) / IFC RF output (IP-to-RF) |
| Context | Bandwidth | Present | — |
| Context | IF Reference Frequency | Present | Default 0 for zero-IF |
| Context | RF Reference Frequency | Present | Two-word, VITA 49.2 format, **all bits right of radix point = 0** (no fractional Hz) |
| Context | IF Band Offset | Present | — |
| Context | Reference Level | Present | — |
| Context | Gain | Present | Two 16-bit words: IF gain + RF gain (VITA 49.2 §9.5.3) |
| Context | Over Range Count | **Not present** | — |
| Context | Sample Rate | Present | Two-word, VITA 49.2 format, **no fractional Hz** |
| Context | Timestamp Adjustment | Present | Defaults 0 if timestamp corrected to Reference Point time; otherwise difference between emission time and time-at-reference-point. (§9.7.3.1) |
| Context | Timestamp Calibration | Present | Most recent time when timestamp was known correct (synced to external source) |
| Context | State and Event Indicators | Present | Calibrated-time + freq-ref lock state (§9.10.8) |
| Context | Data Packet Payload Format | Present | Complex Cartesian I/Q only, link-efficient, no zero padding, signed fixed-point, no event/channel tags, sample size 4–16 bits (same for I and Q), no sample-component repeats |
| Context | Temperature | **Not present** | — |
| Context | Device ID | **Not present** | — |
| Context | Data Item Format | Signed fixed point | — |
| Trailer | — | (Not Used) | — |

#### 3.1.2.3 Version Flow Signal Context Packet — Class `0x0004`

Class Name: "DIFI Version Flow Signal Context"
Purpose: "Convey type/version information and precise time of day for software apps creating an IP-to-RF data flow (uplink) and not using an RF-to-IP data flow (downlink)."

| Section | Parameter | Selected Option | Comments |
|---|---|---|---|
| Header | Packet Type | Context with Stream ID | — |
| Header | Packet Size | 11 words | Fixed; all fields required, no others permitted |
| Header | Stream Identifier | Yes | Selected at runtime |
| Header | Class ID | Present | OUI `0x6A621E`, Packet Class `0x0004` |
| Header | Integer Timestamp | Present | UTC/POSIX/GPS per header TSI |
| Header | Fractional Timestamp | Real-time, picoseconds | May be locked externally |
| Context | CIF 0 Indicator | Present | `0x80000002` (change) or `0x00000002` (no change) — **only CIF 1 bit set** |
| Context | CIF 1 Indicator | Present | `0x0000000C` (V49 Spec Compliance + Version & Build Code). **No other fields permitted.** |
| Context | Reference Point Identifier | **Not Present** | Reference is SID |
| Context | Bandwidth | **Not Present** | — |
| Context | IF Reference Frequency | **Not Present** | — |
| Context | RF Reference Frequency | **Not Present** | — |
| Context | IF Band Offset | **Not Present** | — |
| Context | Reference Level | **Not Present** | — |
| Context | Gain | **Not Present** | — |
| Context | Over Range Count | **Not Present** | — |
| Context | Sample Rate | **Not Present** | — |
| Context | Timestamp Adjustment | **Not Present** | — |
| Context | Timestamp Calibration | **Not Present** | — |
| Context | State and Event Indicators | **Not Present** | — |
| Context | Data Packet Payload Format | **Not Present** | No associated data stream |
| Context | Temperature | **Not Present** | — |
| Context | Device ID | **Not Present** | — |
| Context | Data Item Format | N/A | — |
| Trailer | — | (Not Used) | — |

