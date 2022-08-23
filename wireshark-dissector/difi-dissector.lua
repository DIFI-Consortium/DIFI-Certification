-- Constants

CONTEXT_PKT = "Standard Flow Signal Context Packet"
VERSION_PKT = "Version Flow Signal Context Packet"
DATA_PKT    = "Standard Flow Signal Data Packet"

local tsi_codes = {
    [0] = "Not Allowed",
    [1] = "UTC",
    [2] = "GPS",
    [3] = "POSIX"
}

-- Common Header fields
packet_size    = ProtoField.uint16("difi.packet_size", "Packet Size", base.DEC)
seq_num        = ProtoField.uint8("difi.seq_num", "Seq Num", base.DEC)
tsi            = ProtoField.uint8("difi.tsi", "TSI", base.DEC, tsi_codes)
stream_id      = ProtoField.uint32("difi.stream_id", "Stream ID", base.DEC)
oui            = ProtoField.uint32("difi.oui", "OUI", base.HEX)
class_code     = ProtoField.uint16("difi.class_code", "Packet Class Code", base.HEX)
info_code      = ProtoField.uint16("difi.info_code", "Information Class Code", base.HEX)
int_timestamp  = ProtoField.uint32("difi.integer_timestamp", "Integer-Seconds Timestamp", base.DEC)
frac_timestamp = ProtoField.uint64("difi.fractional_timestamp", "Fractional-Seconds Timestamp", base.DEC)

-- Data Header fields
data = ProtoField.bytes("difi.data", "Payload")
data_len = ProtoField.uint64("difi.data_len", "Length", base.DEC)

-- Context Packet Header fields
cif           = ProtoField.uint32("difi.cif", "Context Indicator Field", base.HEX)
ref_point     = ProtoField.uint32("difi.ref_point", "Reference Point", base.HEX)
bandwidth     = ProtoField.uint64("difi.bandwidth", "Bandwidth", base.DEC)
if_ref_freq   = ProtoField.uint64("difi.if_ref_freq", "IF Reference Frequency", base.DEC)
rf_ref_freq   = ProtoField.uint64("difi.rf_ref_freq", "RF Reference Frequency", base.DEC)
if_offset     = ProtoField.int64("difi.if_offset", "IF Band Offset", base.DEC)
ref_level     = ProtoField.uint32("difi.ref_level", "Reference Level", base.DEC)
gain          = ProtoField.int32("difi.gain", "Attenuation/Gain", base.DEC)
sample_rate   = ProtoField.uint64("difi.sample_rate", "Sample Rate", base.DEC)
timestamp_adj = ProtoField.uint64("difi.time_adj", "Timestamp Adjustment", base.DEC)
time_cal      = ProtoField.uint32("difi.time_cal", "Timestamp Calibration Time", base.DEC)
se_indicator  = ProtoField.uint32("difi.se_indicator", "State and Event Indicators", base.DEC)
data_format   = ProtoField.uint64("difi.data_format", "Data Packet Payload Format", base.DEC)

-- Version Header fields
cif0    = ProtoField.uint32("difi.cif0", "Context Indicator Field 0", base.HEX)
cif1    = ProtoField.uint32("difi.cif1", "Context Indicator Field 1", base.HEX)
v49spec = ProtoField.uint32("difi.v49spec", "V49 Spec Version", base.HEX)
info    = ProtoField.uint32("difi.info", "Year, Day, Revision, Type, ICD Version", base.HEX)


difi_protocol = Proto("DIFI", "DIFI Protocol")

-- Register all potential fields in the tree
difi_protocol.fields = {
    -- common
    packet_size, seq_num, tsi, stream_id, oui, class_code, info_code, int_timestamp, frac_timestamp,
    -- data
    data, data_len,
    -- context
    cif, ref_point, bandwidth, if_ref_freq, rf_ref_freq, if_offset, ref_level, gain, sample_rate,
    timestamp_adj, time_cal, se_indicator, data_format,
    -- version
    cif0, cif1, v49spec, info
}

-- Local functions

local function get_packet_type(ptype)
    local packet_type = "Unknown"

    if ptype == 0x4 then packet_type = CONTEXT_PKT
    elseif ptype == 0x5 then packet_type = VERSION_PKT
    elseif ptype == 0x1 then packet_type = DATA_PKT end

    return packet_type
end

local function difi_common_dissector(buffer, tree)

    -- common header fields
    local word0 = buffer(0, 4):uint()
    local word3 = buffer(12, 4):uint()
    tree:add(packet_size, bit.band(word0, 0xffff))
    tree:add(seq_num, bit.rshift(bit.band(word0, 0xf0000), 16))
    tree:add(tsi, bit.rshift(bit.band(word0, 0xC00000), 22))
    tree:add(stream_id, buffer(4, 4):uint())
    tree:add(oui, buffer(8, 4):uint())
    tree:add(class_code, bit.band(word3, 0xffff))
    tree:add(info_code, bit.rshift(word3, 16))
    tree:add(int_timestamp, buffer(16, 4):uint())
    tree:add(frac_timestamp, buffer(20, 8):uint64())
end

local function context_pkt_dissector(buffer, tree)

    if buffer:len() < 108 then return end

    local subtree = tree:add(difi_protocol, buffer(0, 108), "DIFI Protocol, " .. CONTEXT_PKT)

    -- Header
    difi_common_dissector(buffer, subtree)

    -- Additional header fiels
    subtree:add(cif, buffer(28, 4):uint())
    subtree:add(ref_point, buffer(32, 4):uint())
    subtree:add(bandwidth, buffer(36, 8):uint64())
    subtree:add(if_ref_freq, buffer(44, 8):uint64())
    subtree:add(rf_ref_freq, buffer(52, 8):uint64())
    subtree:add(if_offset, buffer(60, 8):int64())
    subtree:add(ref_level, buffer(68, 4):uint())
    subtree:add(gain, buffer(72, 4):int())
    subtree:add(sample_rate, buffer(76, 8):uint64())
    subtree:add(timestamp_adj, buffer(84, 8):uint64())
    subtree:add(time_cal, buffer(92, 4):uint())
    subtree:add(se_indicator, buffer(96, 4):uint())
    subtree:add(data_format, buffer(100, 8):uint64())
end

local function data_pkt_dissector(buffer, tree)

    if buffer:len() < 28 then return end

    local length = buffer:len()
    local subtree = tree:add(difi_protocol, buffer(0, 27), "DIFI Protocol, " .. DATA_PKT)

    -- Header
    difi_common_dissector(buffer, subtree)

    -- Add the rest of the data fields
    local payload_len = length - 28
    local data_subtree = tree:add(difi_protocol, buffer(28, payload_len), "Data")
    data_subtree:add(data, buffer(28, payload_len))

end

local function version_pkt_dissector(buffer, tree)

    if buffer:len() < 44 then return end

    local subtree = tree:add(difi_protocol, buffer(0, 44), "DIFI Protocol, " .. VERSION_PKT)

    -- Header
    difi_common_dissector(buffer, subtree)

    -- rest of the version header fields
    subtree:add(cif0, buffer(28, 4):uint())
    subtree:add(cif1, buffer(32, 4):uint())
    subtree:add(v49spec, buffer(36, 4):uint())
    subtree:add(info, buffer(40, 4):uint())

end

local function heuristic_checker(buffer, pinfo, tree)
    -- guard for length, header for data packet is at least 7 32-bit words
    if buffer:len() < 28 then return false end

    local potential_oui = buffer(8, 4):uint()
    if potential_oui ~= 0x7C386C then return false end

    local word0 = buffer(0,4):uint()
    local potential_packet_type = bit.rshift(bit.band(word0,0xf0000000), 28)
    local packet_type = get_packet_type(potential_packet_type)

    if packet_type ~= "Unknown"
    then
        difi_protocol.dissector(buffer, pinfo, tree)
        return true
    else return false end
end

function difi_protocol.dissector(buffer, pinfo, tree)

    local word0 = buffer(0,4):uint()
    local potential_packet_type = bit.rshift(bit.band(word0,0xf0000000), 28)
    local packet_type = get_packet_type(potential_packet_type)

    if packet_type == CONTEXT_PKT then
        context_pkt_dissector(buffer, tree)
    elseif packet_type == VERSION_PKT then
        version_pkt_dissector(buffer, tree)
    elseif packet_type == DATA_PKT then

        data_pkt_dissector(buffer, tree)
    end

    pinfo.cols.protocol = difi_protocol.name
end

difi_protocol:register_heuristic("udp", heuristic_checker)
