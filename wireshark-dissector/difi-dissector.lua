
local tsi_codes = {
    [0] = "Not Allowed",
    [1] = "UTC",
    [2] = "GPS",
    [3] = "POSIX"
}

-- Common Header fields
packet_type    = ProtoField.uint16("difi.packet_type", "Packet Type", base.HEX,NULL,0xf000)
tsi            = ProtoField.uint16("difi.tsi", "TSI", base.DEC, tsi_codes,0x00c0)
seq_num        = ProtoField.uint16("difi.seq_num", "Seq Num", base.DEC,NULL,0x000f)
packet_size    = ProtoField.uint16("difi.packet_size", "Packet Size", base.DEC)
stream_id      = ProtoField.uint32("difi.stream_id", "Stream ID", base.DEC)
padding_bits   = ProtoField.uint8("difi.padding_bits", "Padding Bits", base.DEC)
oui            = ProtoField.uint32("difi.oui", "OUI", base.HEX,NULL,0x00ffffff)
packet_class_code     = ProtoField.uint16("difi.packet_class_code", "Packet Class Code", base.HEX)
information_class      = ProtoField.uint16("difi.information_class", "Information Class Code", base.HEX)
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
cif0    = ProtoField.uint32("difi.cif0", "Context Indicator Field (CIF) 0", base.HEX)
cif1    = ProtoField.uint32("difi.cif1", "Context Indicator Field (CIF) 1", base.HEX)
v49spec = ProtoField.uint32("difi.v49spec", "V49 Spec Version", base.HEX)
info    = ProtoField.uint32("difi.info", "Year, Day, Revision, Type, ICD Version", base.HEX)

-- command header fields
cam_field        = ProtoField.uint32("difi.cam_field", "CAM field", base.HEX)
message_id       = ProtoField.uint32("difi.message_id", "Message ID", base.HEX)
controllee_id    = ProtoField.uint32("difi.controllee_id", "Controllee ID", base.DEC)
controller_id    = ProtoField.uint32("difi.controller_id", "Controller ID", base.DEC)
buffer_size      = ProtoField.uint64("difi.buffer_size", "Buffer Size", base.DEC)
buffer_reserved  = ProtoField.uint16("difi.buffer_reserved","RESERVED", base.HEX)
buffer_level     = ProtoField.uint16("difi.buffer_level","Buffer Level", base.DEC,NULL,0xfff0)
buffer_overflow  = ProtoField.uint16("difi.buffer_overflow","Buffer Overflow", base.DEC,NULL,0x0008)
near_full        = ProtoField.uint16("difi.near_full","near_full", base.DEC,NULL,0x0004)
near_empty       = ProtoField.uint16("difi.near_empty","near_empty", base.DEC,NULL,0x0002)
buffer_underflow = ProtoField.uint16("difi.buffer_underflow","Buffer Underflow", base.DEC,NULL,0x0001)

difi_protocol = Proto("DIFI", "DIFI Protocol")

-- Register all potential fields in the tree
difi_protocol.fields = {
    -- common
    packet_type, packet_size, seq_num, tsi, stream_id, padding_bits, oui, packet_class_code, information_class, int_timestamp, frac_timestamp,
    -- data
    data, data_len,
    -- context
    cif, ref_point, bandwidth, if_ref_freq, rf_ref_freq, if_offset, ref_level, gain, sample_rate,
    timestamp_adj, time_cal, se_indicator, data_format,
    -- version
    cif0, cif1, v49spec, info,
    -- command
    cam_field, message_id, controllee_id, controller_id, buffer_size, buffer_reserved, buffer_level, buffer_overflow, near_full, near_empty, buffer_underflow
}

-- Local functions

local function difi_common_dissector(buffer, tree)

    -- common header fields
    tree:add_packet_field(packet_type,buffer(0,2),ENC_BIG_ENDIAN)
    tree:add_packet_field(tsi,buffer(0,2),ENC_BIG_ENDIAN)
    tree:add_packet_field(seq_num,buffer(0,2),ENC_BIG_ENDIAN)
    tree:add(packet_size, buffer(2,2))
    tree:add(stream_id, buffer(4, 4))
    -- padding bits
    tree:add_packet_field(padding_bits, buffer(8,1),ENC_BIG_ENDIAN)
    tree:add_packet_field(oui, buffer(8,4),ENC_BIG_ENDIAN)
    tree:add(information_class,buffer(12,2))
    tree:add(packet_class_code,buffer(14,2))
    tree:add(int_timestamp,buffer(16,4))
    tree:add(frac_timestamp,buffer(20,8))
end

local function context_pkt_dissector(buffer, tree, name)

    if buffer:len() < 108 then return end

    local subtree = tree:add(difi_protocol, buffer(0, 108), "DIFI Protocol, " .. name)

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

local function data_pkt_dissector(buffer, tree, name)

    if buffer:len() < 28 then return end

    local length = buffer:len()
    local subtree = tree:add(difi_protocol, buffer(0, 27), "DIFI Protocol, " .. name)

    -- Header
    difi_common_dissector(buffer, subtree)

    -- Add the rest of the data fields
    local payload_len = length - 28
    local data_subtree = tree:add(difi_protocol, buffer(28, payload_len), "Data")
    data_subtree:add(data, buffer(28, payload_len))

end

local function version_pkt_dissector(buffer, tree)

    if buffer:len() < 44 then return end

    local subtree = tree:add(difi_protocol, buffer(0, 44), "DIFI Protocol, " .. "Version Flow Signal Context Packet")

    -- Header
    difi_common_dissector(buffer, subtree)

    -- rest of the version header fields
    subtree:add(cif0, buffer(28, 4):uint())
    subtree:add(cif1, buffer(32, 4):uint())
    subtree:add(v49spec, buffer(36, 4):uint())
    subtree:add(info, buffer(40, 4):uint())

end

local function control_pkt_dissector(buffer, tree, name)
    if buffer:len() < 84 then return end

    local subtree = tree:add(difi_protocol, buffer(0, 84), "DIFI Protocol, " .. name)

    -- Header
    difi_common_dissector(buffer, subtree)

    subtree:add_packet_field(cam_field, buffer(28, 4),ENC_BIG_ENDIAN)
    subtree:add_packet_field(message_id, buffer(32, 4),ENC_BIG_ENDIAN)
    subtree:add_packet_field(controllee_id, buffer(36, 4),ENC_BIG_ENDIAN)
    subtree:add_packet_field(cif0,buffer(23,4),ENC_BIG_ENDIAN)
    subtree:add_packet_field(cif1,buffer(36,4),ENC_BIG_ENDIAN)
    subtree:add_packet_field(controller_id, buffer(40, 4),ENC_BIG_ENDIAN)
    subtree:add_packet_field(ref_point, buffer(52, 4),ENC_BIG_ENDIAN)
    subtree:add_packet_field(sample_rate, buffer(56, 8),ENC_BIG_ENDIAN)
    subtree:add_packet_field(timestamp_adj, buffer(64, 8),ENC_BIG_ENDIAN)
    subtree:add_packet_field(buffer_size, buffer(72, 8),ENC_BIG_ENDIAN)
    subtree:add_packet_field(buffer_reserved, buffer(80,2),ENC_BIG_ENDIAN)
    subtree:add_packet_field(buffer_level, buffer(82,2),ENC_BIG_ENDIAN)
    subtree:add_packet_field(buffer_overflow, buffer(82,2),ENC_BIG_ENDIAN)
    subtree:add_packet_field(near_full, buffer(82,2),ENC_BIG_ENDIAN)
    subtree:add_packet_field(near_empty, buffer(82,2),ENC_BIG_ENDIAN)
    subtree:add_packet_field(buffer_underflow, buffer(82,2),ENC_BIG_ENDIAN)
end

local function heuristic_checker(buffer, pinfo, tree)
    -- guard for length, header for data packet is at least 7 32-bit words
    if buffer:len() < 28 then return false end

    -- TODO: the OUI / CID is 24 bits not 4 bytes. Since pad bit count is no longer fixed at 0 this is no longer valid
    local potential_oui = buffer(9, 3):uint()
    if (potential_oui ~= 0x7C386C and potential_oui ~= 0x6A621E) then return false end

    local word0 = buffer(0,4):uint()
    local packet_type_int = bit.rshift(bit.band(word0,0xf0000000), 28)

    local valid_ptype = false
    if packet_type == 4 or packet_type == 5 or packet_type == 1 or packet_type == 6 then
        valid_ptype = true
    end
    valid_ptype = true
    if valid_ptype then
        difi_protocol.dissector(buffer, pinfo, tree)
        return true
    else
        return false
    end
end

function difi_protocol.dissector(buffer, pinfo, tree)

    local word0 = buffer(0,4):uint()
    local word3 = buffer(12,4):uint()
    local packet_type_int = bit.rshift(bit.band(word0,0xf0000000), 28)
    local packet_class_int = bit.rshift(bit.band(word3,0x0000ffff), 0)

    local packet_type_int = bit.rshift(bit.band(word0,0xf0000000), 28)
    name = "unknown type=" .. packet_type_int .. " , class=" .. packet_class_int
    if packet_type_int == 0x4 then
        if packet_class_int == 1 then name = "Standard Flow Signal Context Packet" end
        if packet_class_int == 3 then name = "Sample Count Context Packet" end
        context_pkt_dissector(buffer, tree, name)
    elseif packet_type_int == 0x5 then
        name = "Version Flow Signal Context Packet"
        version_pkt_dissector(buffer, tree, name)
    elseif packet_type_int == 0x1 then
        if packet_class_int == 0 then name = "Standard Flow Signal Data Packet" end
        if packet_class_int == 2 then name = "Sample Count Data Packet" end
        data_pkt_dissector(buffer, tree, name)
    elseif packet_type_int == 0x6 then
        if packet_class_int == 6 then name = "Real Time Command Packet" end
        if packet_class_int == 5 then name = "Sample Count Command Packet" end
        control_pkt_dissector(buffer, tree, name)
    end

    pinfo.cols.protocol = difi_protocol.name
end

difi_protocol:register_heuristic("udp", heuristic_checker)
