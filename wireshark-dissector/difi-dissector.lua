-- Constants
CONTEXT_PKT = "Standard Flow Signal Context Packet"
VERSION_PKT = "Version Flow Signal Context Packet"
DATA_PKT    = "Standard Flow Signal Data Packet"
CMD_PKT     = "Command Packet"
EXT_CMD_PKT = "Extension Command Packet"

local tsi_codes = {
    [0] = "Not Allowed", -- (Some ICDs call this Not Specified)
    [1] = "UTC",
    [2] = "GPS",
    [3] = "POSIX"
}

local tsf_codes = {
    [0] = "Undefined",
    [1] = "Sample Count Time",
    [2] = "Real (pico secs) Time",
    [3] = "Free-Running Count Time"
}

local command_indicator_codes = {
    [0] = "Control",
    [4] = "Acknowledge"
}

-- Common Header fields
packet_type    = ProtoField.uint8 ("difi.packet_type", "Packet Type", base.HEX, nil)
tsi            = ProtoField.uint8 ("difi.tsi", "TSI", base.DEC, tsi_codes)
tsf            = ProtoField.uint8 ("difi.tsf", "TSF", base.DEC, tsf_codes)
seq_num        = ProtoField.uint8 ("difi.seq_num", "Seq Num", base.DEC)
packet_size    = ProtoField.uint16("difi.packet_size", "Packet Size (32-bit words)", base.DEC)
stream_id      = ProtoField.uint32("difi.stream_id", "Stream ID", base.DEC)
padding_bits   = ProtoField.uint8 ("difi.padding_bits", "Padding Bits", base.DEC)
oui            = ProtoField.uint24("difi.oui", "OUI/CID", base.HEX)
packet_class_code = ProtoField.uint16("difi.packet_class_code", "Packet Class Code", base.HEX)
information_class = ProtoField.uint16("difi.information_class", "Information Class Code", base.HEX)
int_timestamp  = ProtoField.uint32("difi.integer_timestamp", "Integer-Seconds Timestamp", base.DEC)
frac_timestamp = ProtoField.uint64("difi.fractional_timestamp", "Fractional-Seconds Timestamp (ps)", base.DEC)

-- Data Header fields
data     = ProtoField.bytes ("difi.data", "Payload")
data_len = ProtoField.uint64("difi.data_len", "Length", base.DEC)

-- Context Packet Header fields
ctxt_cif      = ProtoField.uint32("difi.ctxt_cif", "Context Indicator Field", base.HEX)
ref_point     = ProtoField.uint32("difi.ref_point", "Reference Point", base.HEX)
bandwidth     = ProtoField.uint64("difi.bandwidth", "Bandwidth (Hz)", base.DEC)
if_ref_freq   = ProtoField.uint64("difi.if_ref_freq", "IF Reference Frequency (Hz)", base.DEC)
rf_ref_freq   = ProtoField.uint64("difi.rf_ref_freq", "RF Reference Frequency (Hz)", base.DEC)
if_offset     = ProtoField.int64 ("difi.if_offset", "IF Band Offset (Hz)", base.DEC)
ref_level     = ProtoField.float ("difi.ref_level", "Reference Level (dB)", base.DEC)
scaling_level = ProtoField.float ("difi.scaling_level", "Scaling Level (dB)", base.DEC)
stage1_gain   = ProtoField.float ("difi.stage1_gain", "Stage 1 Attenuation/Gain (dB)", base.DEC)
stage2_gain   = ProtoField.float ("difi.stage2_gain", "Stage 2 Attenuation/Gain (dB)", base.DEC)
sample_rate   = ProtoField.uint64("difi.sample_rate", "Sample Rate (Hz)", base.DEC)
timestamp_adj = ProtoField.uint64("difi.time_adj", "Timestamp Adjustment (fs)", base.DEC)
time_cal      = ProtoField.uint32("difi.time_cal", "Timestamp Calibration Time", base.DEC)
se_indicator  = ProtoField.uint32("difi.se_indicator", "State and Event Indicators", base.HEX)
data_format   = ProtoField.uint64("difi.data_format", "Data Packet Payload Format", base.HEX)
bytes_per_sample = ProtoField.uint8("difi.bytes_per_sample", "Bytes Per Sample (I & Q pair)", base.DEC)

-- Version Header fields
ctxt_cif0     = ProtoField.uint32("difi.ctxt_cif0", "Context Indicator Field (CIF) 0", base.HEX)
ctxt_cif1     = ProtoField.uint32("difi.ctxt_cif1", "Context Indicator Field (CIF) 1", base.HEX)
v49spec       = ProtoField.uint32("difi.v49spec", "V49 Spec Version", base.HEX)
year          = ProtoField.uint32("difi.year","Year (Starting from 2000)", base.DEC, nil, 0xfe000000)
day           = ProtoField.uint32("difi.day","Day", base.DEC, nil, 0x01ff0000)
revision      = ProtoField.uint32("difi.revision","Revision", base.DEC, nil, 0x0000fc00)
user_type     = ProtoField.uint32("difi.user_type","Type (user-defined)", base.DEC, nil, 0x000003c0)
icd_version   = ProtoField.uint32("difi.icd_version","ICD Version", base.DEC, nil, 0x0000003f)

-- Command header fields
command_indicator = ProtoField.uint8 ("difi.command_indicator", "Control/Acknowledge Indicators", base.HEX, command_indicator_codes)
cam_field        = ProtoField.uint32("difi.cam_field", "CAM field", base.HEX)
message_id       = ProtoField.uint32("difi.message_id", "Message ID", base.HEX)
controllee_id    = ProtoField.uint32("difi.controllee_id", "Controllee ID", base.HEX)
controller_id    = ProtoField.uint32("difi.controller_id", "Controller ID", base.HEX)
ctrl_cif0        = ProtoField.uint32("difi.ctrl_cif0", "Control Indicator Field (CIF) 0", base.HEX)
ctrl_cif1        = ProtoField.uint32("difi.ctrl_cif1", "Control Indicator Field (CIF) 1", base.HEX)
buffer_size      = ProtoField.uint64("difi.buffer_size", "Buffer Size", base.DEC)
buffer_reserved  = ProtoField.uint16("difi.buffer_reserved","RESERVED", base.HEX)
buffer_level     = ProtoField.uint16("difi.buffer_level","Buffer Level", base.DEC, nil, 0xfff0)
buffer_overflow  = ProtoField.uint16("difi.buffer_overflow","Buffer Overflow", base.DEC, nil, 0x0008)
near_full        = ProtoField.uint16("difi.near_full","near_full", base.DEC, nil, 0x0004)
near_empty       = ProtoField.uint16("difi.near_empty","near_empty", base.DEC, nil, 0x0002)
buffer_underflow = ProtoField.uint16("difi.buffer_underflow","Buffer Underflow", base.DEC, nil, 0x0001)

-- DIFI 1.3 Extension Command packet fields
sink_time_cal_int_timestamp     = ProtoField.uint32("difi.sink_time_cal_integer_timestamp", "Sink Time Calibration Integer-Seconds", base.DEC)
sink_time_cal_frac_timestamp    = ProtoField.uint64("difi.sink_time_cal_fractional_timestamp", "Sink Time Calibration Fractional-Seconds", base.DEC)
control_int_timestamp           = ProtoField.uint32("difi.control_integer_timestamp", "Control Packet Integer-Seconds Timestamp", base.DEC)
control_frac_timestamp          = ProtoField.uint64("difi.control_fractional_timestamp", "Control Packet Fractional-Seconds Timestamp", base.DEC)
sink_reception_int_timestamp    = ProtoField.uint32("difi.sink_reception_integer_timestamp", "Sink Reception Integer-Seconds Timestamp", base.DEC)
sink_reception_frac_timestamp   = ProtoField.uint64("difi.sink_reception_fractional_timestamp", "Sink Reception Fractional-Seconds Timestamp", base.DEC)
capabilities_payload            = ProtoField.bytes ("difi.capabilities_payload", "Sink Capabilities Payload")
status_code_payload             = ProtoField.bytes ("difi.status_code_payload", "Status Code Payload")
extension_payload               = ProtoField.bytes ("difi.extension_payload", "Extension Command Payload")
extension_form                  = ProtoField.string("difi.extension_form", "Extension Command Form")
cif0_summary                    = ProtoField.string("difi.cif0.summary", "Decoded CIF0")
cif1_summary                    = ProtoField.string("difi.cif1.summary", "Decoded CIF1")
capability_format               = ProtoField.string("difi.capability_format", "Capability Response Format")
cap_supported_iccs              = ProtoField.string("difi.capability.supported_iccs", "Supported Information Classes")
cap_reference_point_count       = ProtoField.uint16("difi.capability.reference_point_count", "Reference Point Count", base.DEC)
cap_reference_point             = ProtoField.uint32("difi.capability.reference_point", "Reference Point", base.HEX)
cap_sample_rate_count           = ProtoField.uint16("difi.capability.sample_rate_count", "Sample Rate/Bandwidth Count", base.DEC)
cap_sample_rate_mode            = ProtoField.string("difi.capability.sample_rate_mode", "Sample Rate Range Mode")
cap_sample_rate_hz              = ProtoField.uint64("difi.capability.sample_rate_hz", "Sample Rate (Hz)", base.DEC)
cap_bandwidth_hz                = ProtoField.uint64("difi.capability.bandwidth_hz", "Maximum Bandwidth (Hz)", base.DEC)
cap_range_min_hz                = ProtoField.uint64("difi.capability.range_min_hz", "Range Minimum (Hz)", base.DEC)
cap_range_max_hz                = ProtoField.uint64("difi.capability.range_max_hz", "Range Maximum (Hz)", base.DEC)
cap_range_resolution_hz         = ProtoField.uint64("difi.capability.range_resolution_hz", "Range Resolution/Ratio", base.DEC)
cap_min_sr_bw_ratio             = ProtoField.uint32("difi.capability.min_sample_rate_bandwidth_ratio", "Min Sample Rate/Bandwidth Ratio (Q15)", base.DEC)
cap_if_frequency_count          = ProtoField.uint16("difi.capability.if_frequency_count", "IF Frequency Count", base.DEC)
cap_rf_frequency_count          = ProtoField.uint16("difi.capability.rf_frequency_count", "RF Frequency Count", base.DEC)
cap_if_offset_count             = ProtoField.uint16("difi.capability.if_offset_count", "IF Band Offset Count", base.DEC)
cap_if_frequency_hz             = ProtoField.uint64("difi.capability.if_frequency_hz", "IF Reference Frequency (Hz)", base.DEC)
cap_rf_frequency_hz             = ProtoField.uint64("difi.capability.rf_frequency_hz", "RF Reference Frequency (Hz)", base.DEC)
cap_if_offset_hz                = ProtoField.int64 ("difi.capability.if_offset_hz", "IF Band Offset (Hz)", base.DEC)
cap_if_offset_range_min_hz      = ProtoField.int64 ("difi.capability.if_offset_range_min_hz", "IF Band Offset Range Minimum (Hz)", base.DEC)
cap_if_offset_range_max_hz      = ProtoField.int64 ("difi.capability.if_offset_range_max_hz", "IF Band Offset Range Maximum (Hz)", base.DEC)
cap_if_offset_range_res_hz      = ProtoField.uint64("difi.capability.if_offset_range_resolution_hz", "IF Band Offset Range Resolution (Hz)", base.DEC)
cap_ref_level_min_db            = ProtoField.float ("difi.capability.ref_level_min_db", "Reference Level Minimum (dB)", base.DEC)
cap_ref_level_max_db            = ProtoField.float ("difi.capability.ref_level_max_db", "Reference Level Maximum (dB)", base.DEC)
cap_ref_level_resolution_db     = ProtoField.float ("difi.capability.ref_level_resolution_db", "Reference Level Resolution (dB)", base.DEC)
cap_sid_delay_fs                = ProtoField.uint64("difi.capability.sid_delay_fs", "Nominal SID to Reference Point Delay (fs)", base.DEC)
cap_bit_depth_indicator         = ProtoField.uint16("difi.capability.bit_depth_indicator", "Bit Depth Indicator", base.HEX)
cap_bit_depths                  = ProtoField.string("difi.capability.bit_depths", "Supported Bit Depths")
cap_max_streams                 = ProtoField.uint16("difi.capability.max_streams", "Maximum Simultaneous Streams", base.DEC)
cap_link_timeout_int            = ProtoField.uint32("difi.capability.link_active_timeout_integer", "Link Active Timeout Integer", base.DEC)
cap_link_timeout_frac           = ProtoField.uint64("difi.capability.link_active_timeout_fractional", "Link Active Timeout Fractional", base.DEC)
cap_context_timeout_int         = ProtoField.uint32("difi.capability.context_error_timeout_integer", "Context Error Timeout Integer", base.DEC)
cap_context_timeout_frac        = ProtoField.uint64("difi.capability.context_error_timeout_fractional", "Context Error Timeout Fractional", base.DEC)
status_packet_errors            = ProtoField.uint32("difi.status.packet_errors", "Packet Error Bits", base.HEX)
status_system_errors_warnings   = ProtoField.uint32("difi.status.system_errors_warnings", "System Errors and Warnings", base.HEX)
status_summary                  = ProtoField.string("difi.status.summary", "Decoded Status")
status_timeout_link_termination = ProtoField.bool("difi.status.timeout_link_termination", "Timeout/Link Termination", 32, nil, 0x00000010)
status_context_error_timeout    = ProtoField.bool("difi.status.context_error_timeout", "Context Error Timeout", 32, nil, 0x04000000)
status_link_termination         = ProtoField.bool("difi.status.link_termination", "Link Termination", 32, nil, 0x02000000)
status_sink_bw_exceeded         = ProtoField.bool("difi.status.sink_bandwidth_capacity_exceeded", "Sink Bandwidth Capacity Exceeded", 32, nil, 0x00000020)
status_stream_capacity_exceeded = ProtoField.bool("difi.status.stream_capacity_exceeded", "Stream Capacity Exceeded", 32, nil, 0x00000040)
status_frequency_conflict       = ProtoField.bool("difi.status.frequency_allocation_conflict", "Frequency Allocation Conflict", 32, nil, 0x00000080)
status_unsupported_bit_depth    = ProtoField.bool("difi.status.unsupported_bit_depth", "Unsupported Bit Depth", 32, nil, 0x00000100)
status_payload_config_error     = ProtoField.bool("difi.status.data_payload_config_error", "Data Payload Configuration Error", 32, nil, 0x00000200)
status_sample_rate_out_range    = ProtoField.bool("difi.status.sample_rate_out_of_range", "Sample Rate Out of Range", 32, nil, 0x00000400)
status_sample_rate_res_error    = ProtoField.bool("difi.status.sample_rate_resolution_error", "Sample Rate Resolution Error", 32, nil, 0x00000800)
status_ref_level_mismatch       = ProtoField.bool("difi.status.reference_level_mismatch", "Reference Level Mismatch", 32, nil, 0x00001000)
status_if_offset_too_large      = ProtoField.bool("difi.status.if_offset_too_large", "IF Offset Too Large", 32, nil, 0x00002000)
status_rf_freq_out_range        = ProtoField.bool("difi.status.rf_frequency_out_of_range", "RF Frequency Out of Range", 32, nil, 0x00004000)
status_rf_freq_res_error        = ProtoField.bool("difi.status.rf_frequency_resolution_error", "RF Frequency Resolution Error", 32, nil, 0x00008000)
status_if_freq_out_range        = ProtoField.bool("difi.status.if_frequency_out_of_range", "IF Frequency Out of Range", 32, nil, 0x00010000)
status_if_freq_res_error        = ProtoField.bool("difi.status.if_frequency_resolution_error", "IF Frequency Resolution Error", 32, nil, 0x00020000)
status_fractional_hz            = ProtoField.bool("difi.status.fractional_hz_specified", "Fractional Hz Specified", 32, nil, 0x00040000)
status_bw_too_large             = ProtoField.bool("difi.status.bandwidth_too_large_for_rate", "Bandwidth Too Large for Sample Rate", 32, nil, 0x00080000)
status_ref_point_unknown        = ProtoField.bool("difi.status.reference_point_not_recognized", "Reference Point Not Recognized", 32, nil, 0x00100000)
status_late_data                = ProtoField.bool("difi.status.late_data_packet", "Late Data Packet", 32, nil, 0x00200000)
status_late_context             = ProtoField.bool("difi.status.late_context_packet", "Late Context Packet", 32, nil, 0x00400000)
status_packet_class_undefined   = ProtoField.bool("difi.status.packet_class_not_defined", "Packet Class Not Defined", 32, nil, 0x00800000)
status_pcc_not_in_icc           = ProtoField.bool("difi.status.pcc_not_in_icc", "PCC Not in ICC", 32, nil, 0x01000000)
status_icc_not_defined          = ProtoField.bool("difi.status.icc_not_defined", "ICC Not Defined", 32, nil, 0x02000000)
status_pad_bit_count            = ProtoField.bool("difi.status.pad_bit_count_not_permitted", "Pad Bit Count Not Permitted", 32, nil, 0x04000000)
status_incorrect_packet_size    = ProtoField.bool("difi.status.incorrect_packet_size", "Incorrect Packet Size", 32, nil, 0x08000000)
status_wrong_tsf                = ProtoField.bool("difi.status.wrong_tsf", "Wrong TSF", 32, nil, 0x10000000)
status_wrong_tsi                = ProtoField.bool("difi.status.wrong_tsi", "Wrong TSI", 32, nil, 0x20000000)
status_wrong_tsm                = ProtoField.bool("difi.status.wrong_tsm", "Wrong TSM", 32, nil, 0x40000000)
status_wrong_packet_type        = ProtoField.bool("difi.status.wrong_packet_type", "Wrong Packet Type", 32, nil, 0x80000000)
status_buffer_overflow          = ProtoField.bool("difi.status.buffer_overflow_error", "Buffer Overflow", 32, nil, 0x10000000)
status_buffer_underflow         = ProtoField.bool("difi.status.buffer_underflow_error", "Buffer Underflow", 32, nil, 0x20000000)
status_time_lol                 = ProtoField.bool("difi.status.timebase_lol", "Timebase LOL", 32, nil, 0x40000000)
status_freq_lol                 = ProtoField.bool("difi.status.frequency_lol", "Frequency LOL", 32, nil, 0x80000000)

difi_protocol = Proto("DIFI", "DIFI Protocol")

-- Register all fields
difi_protocol.fields = {
    -- common
    packet_type, packet_size, seq_num, tsi, tsf, stream_id, padding_bits, oui,
    packet_class_code, information_class, int_timestamp, frac_timestamp,
    -- data
    data, data_len,
    -- context
    ctxt_cif, ref_point, bandwidth, if_ref_freq, rf_ref_freq, if_offset, ref_level, scaling_level,
    stage1_gain, stage2_gain, sample_rate, timestamp_adj, time_cal, se_indicator, data_format, bytes_per_sample,
    -- version
    ctxt_cif0, ctxt_cif1, v49spec, year, day, revision, user_type, icd_version,
    -- command
    command_indicator, cam_field, message_id, controllee_id, controller_id, ctrl_cif0, ctrl_cif1,
    buffer_size, buffer_reserved, buffer_level, buffer_overflow, near_full, near_empty, buffer_underflow,
    -- DIFI 1.3 extension command
    sink_time_cal_int_timestamp, sink_time_cal_frac_timestamp,
    control_int_timestamp, control_frac_timestamp,
    sink_reception_int_timestamp, sink_reception_frac_timestamp,
    capabilities_payload, status_code_payload, extension_payload,
    extension_form, cif0_summary, cif1_summary,
    capability_format, cap_supported_iccs, cap_reference_point_count,
    cap_reference_point, cap_sample_rate_count, cap_sample_rate_mode,
    cap_sample_rate_hz, cap_bandwidth_hz, cap_range_min_hz, cap_range_max_hz,
    cap_range_resolution_hz, cap_min_sr_bw_ratio, cap_if_frequency_count,
    cap_rf_frequency_count, cap_if_offset_count, cap_if_frequency_hz,
    cap_rf_frequency_hz, cap_if_offset_hz, cap_if_offset_range_min_hz,
    cap_if_offset_range_max_hz, cap_if_offset_range_res_hz, cap_ref_level_min_db,
    cap_ref_level_max_db, cap_ref_level_resolution_db, cap_sid_delay_fs,
    cap_bit_depth_indicator, cap_bit_depths, cap_max_streams, cap_link_timeout_int,
    cap_link_timeout_frac, cap_context_timeout_int, cap_context_timeout_frac,
    status_packet_errors, status_system_errors_warnings, status_summary,
    status_timeout_link_termination, status_context_error_timeout,
    status_link_termination, status_sink_bw_exceeded, status_stream_capacity_exceeded,
    status_frequency_conflict, status_unsupported_bit_depth,
    status_payload_config_error, status_sample_rate_out_range,
    status_sample_rate_res_error, status_ref_level_mismatch,
    status_if_offset_too_large, status_rf_freq_out_range, status_rf_freq_res_error,
    status_if_freq_out_range, status_if_freq_res_error, status_fractional_hz,
    status_bw_too_large, status_ref_point_unknown, status_late_data,
    status_late_context, status_packet_class_undefined, status_pcc_not_in_icc,
    status_icc_not_defined, status_pad_bit_count, status_incorrect_packet_size,
    status_wrong_tsf, status_wrong_tsi, status_wrong_tsm, status_wrong_packet_type,
    status_buffer_overflow, status_buffer_underflow, status_time_lol, status_freq_lol
}

-- Helpers ----------------------------------------------------

-- All frequency and sample rate fields are 64-bit 2's complement with radix point right of bit 20.
local function get_int_freq(word64)
    return word64:rshift(20)
end

-- Convert 16-bit signed fixed-point with radix at bit 7 into dB float.
local function get_dB(word16)
    local db_val = 0.0
    if (bit.band(word16,0x8000) == 0x8000) then
        local temp = (bit.bxor(word16, 0xffff)) + 1
        db_val = -temp/0x80
    else
        db_val = word16/0x80
    end
    return db_val
end

local function get_bytes_per_sample(data_format_word64)
    local upper_32_bits = data_format_word64:rshift(32)
    local w26 = upper_32_bits:tonumber()
    local complex_type = bit.rshift(bit.band(w26, 0x0000C000), 14)
    local packing_method = bit.rshift(bit.band(w26, 0x00002000), 13)

    if complex_type == 1 and packing_method == 1 then
        local bit_depth = bit.rshift(bit.band(w26, 0x03F00000), 20) + 1
        return bit_depth / 4
    end

    local bits_per_iq = bit.band(w26, 0x3F) + 1
    return (bits_per_iq * 2) / 8
end

local function get_dB_q8(word16)
    local db_val = 0.0
    if (bit.band(word16,0x8000) == 0x8000) then
        local temp = (bit.bxor(word16, 0xffff)) + 1
        db_val = -temp/0x100
    else
        db_val = word16/0x100
    end
    return db_val
end

local function add_note(tree, text)
    tree:add(text)
end

local function icc_list_string(count, first, second_word, third_word)
    local values = {}
    if count > 0 then table.insert(values, string.format("0x%04X", first)) end
    if count > 1 then table.insert(values, string.format("0x%04X", bit.rshift(second_word, 16))) end
    if count > 2 then table.insert(values, string.format("0x%04X", bit.band(second_word, 0xffff))) end
    if count > 3 then table.insert(values, string.format("0x%04X", bit.rshift(third_word, 16))) end
    if count > 4 then table.insert(values, string.format("0x%04X", bit.band(third_word, 0xffff))) end
    return table.concat(values, ", ")
end

local function bit_depths_string(indicator)
    local values = {}
    for depth = 4, 16 do
        local bit_index = depth - 4
        if bit.band(indicator, bit.lshift(1, bit_index)) ~= 0 then
            table.insert(values, tostring(depth))
        end
    end
    if #values == 0 then return "none advertised" end
    return table.concat(values, ", ")
end

local function add_difi13_cif_summary(tree, buffer, packet_class_int, packet_len, cif0, is_short_form)
    local sections = "Capability sections: information classes, reference points, sample rate/bandwidth, IF/RF frequency, IF offset, reference level, SID delay, bit depth/streams, buffer size, link/context timeouts"
    local cif0_text = nil
    local cif1_text = nil

    if packet_class_int == 0x0007 then
        if is_short_form then
            cif0_text = string.format("CIF0 0x%08X: Short-form query: latency/timing exchange; optional sink time calibration may follow", cif0)
        else
            cif0_text = string.format("CIF0 0x%08X: Long-form query: requests sink DIFI 1.3 capability sections; CIF1 present", cif0)
            cif1_text = "CIF1 present: long-form sink capability query selector"
        end
    elseif packet_class_int == 0x0008 then
        if is_short_form then
            cif0_text = string.format("CIF0 0x%08X: Short-form response: echoed query time and sink reception time", cif0)
        else
            cif0_text = string.format("CIF0 0x%08X: Long-form response: advertises sink DIFI 1.3 capabilities; %s", cif0, sections)
            cif1_text = "CIF1 present: long-form sink capability response selector"
        end
    elseif packet_class_int == 0x0009 then
        cif0_text = string.format("CIF0 0x%08X: Status report: status-code payload follows", cif0)
    else
        cif0_text = string.format("CIF0 0x%08X", cif0)
    end

    if cif0_text ~= nil then
        tree:add(cif0_summary, buffer(44,4), cif0_text)
    end

    if cif1_text ~= nil and packet_len >= 52 then
        local cif1 = buffer(48,4):uint()
        tree:add(cif1_summary, buffer(48,4), string.format("CIF1 0x%08X: %s", cif1, cif1_text))
    end
end

local function add_u64_freq(tree, field, buffer, offset, label)
    if buffer:len() >= offset + 8 then
        local hz = get_int_freq(buffer(offset, 8):uint64())
        local item = tree:add(field, buffer(offset, 8), hz)
        if label ~= nil then item:append_text(" (" .. label .. ")") end
        return hz
    end
    return nil
end

local function add_i64_freq(tree, field, buffer, offset, label)
    if buffer:len() >= offset + 8 then
        local hz = get_int_freq(buffer(offset, 8):int64())
        local item = tree:add(field, buffer(offset, 8), hz)
        if label ~= nil then item:append_text(" (" .. label .. ")") end
        return hz
    end
    return nil
end

local function decode_discrete_capabilities(buffer, tree, packet_len)
    if packet_len < 88 then return end

    local w14 = buffer(52,4):uint()
    local num_ic = bit.rshift(w14, 16)
    local first_ic = bit.band(w14, 0xffff)
    local w15 = packet_len >= 60 and buffer(56,4):uint() or 0
    local w16 = packet_len >= 64 and buffer(60,4):uint() or 0
    tree:add(cap_supported_iccs, buffer(52, math.min(packet_len - 52, 12)),
             icc_list_string(num_ic, first_ic, w15, w16))

    if packet_len >= 68 then
        local count = bit.band(buffer(64,4):uint(), 0xffff)
        tree:add(cap_reference_point_count, buffer(64,4), count)
        for i = 0, math.min(count, 4) - 1 do
            local off = 68 + i * 4
            if packet_len >= off + 4 then tree:add(cap_reference_point, buffer(off,4)) end
        end
    end

    local w22 = buffer(84,4):uint()
    local count = bit.band(w22, 0x7fff)
    tree:add(cap_sample_rate_count, buffer(84,4), count)
    for i = 0, math.min(count, 3) - 1 do
        add_u64_freq(tree, cap_sample_rate_hz, buffer, 88 + i * 8, "sample rate #" .. (i + 1))
        add_u64_freq(tree, cap_bandwidth_hz, buffer, 112 + i * 8, "max bandwidth #" .. (i + 1))
    end

    if packet_len >= 140 then
        local if_count = bit.band(buffer(136,4):uint(), 0x7fff)
        tree:add(cap_if_frequency_count, buffer(136,4), if_count)
        for i = 0, math.min(if_count, 3) - 1 do
            add_u64_freq(tree, cap_if_frequency_hz, buffer, 140 + i * 8, "IF #" .. (i + 1))
        end
    end

    if packet_len >= 168 then
        local rf_count = bit.band(buffer(164,4):uint(), 0x7fff)
        tree:add(cap_rf_frequency_count, buffer(164,4), rf_count)
        for i = 0, math.min(rf_count, 3) - 1 do
            add_u64_freq(tree, cap_rf_frequency_hz, buffer, 168 + i * 8, "RF #" .. (i + 1))
        end
    end

    if packet_len >= 196 then
        local offset_count = bit.band(buffer(192,4):uint(), 0x7fff)
        tree:add(cap_if_offset_count, buffer(192,4), offset_count)
        for i = 0, math.min(offset_count, 3) - 1 do
            add_i64_freq(tree, cap_if_offset_hz, buffer, 196 + i * 8, "IF offset #" .. (i + 1))
        end
    end

    if packet_len >= 228 then
        local ref_word = buffer(220,4):uint()
        local res_word = buffer(224,4):uint()
        tree:add(cap_ref_level_min_db, buffer(220,2), get_dB_q8(bit.rshift(ref_word, 16)))
        tree:add(cap_ref_level_max_db, buffer(222,2), get_dB_q8(bit.band(ref_word, 0xffff)))
        tree:add(cap_ref_level_resolution_db, buffer(224,2), get_dB_q8(bit.rshift(res_word, 16)))
    end

    if packet_len >= 236 then tree:add(cap_sid_delay_fs, buffer(228,8)) end
    if packet_len >= 240 then
        local w60 = buffer(236,4):uint()
        local depth_indicator = bit.rshift(bit.band(w60, 0xfff80000), 19)
        tree:add(cap_bit_depth_indicator, buffer(236,4), depth_indicator)
        tree:add(cap_bit_depths, buffer(236,4), bit_depths_string(depth_indicator))
        tree:add(cap_max_streams, buffer(238,2), bit.band(w60, 0xffff))
    end
    if packet_len >= 248 then tree:add(buffer_size, buffer(240,8)) end
    if packet_len >= 268 then
        tree:add(cap_link_timeout_int, buffer(256,4))
        tree:add(cap_link_timeout_frac, buffer(260,8))
    end
    if packet_len >= 280 then
        tree:add(cap_context_timeout_int, buffer(268,4))
        tree:add(cap_context_timeout_frac, buffer(272,8))
    end
end

local function add_range_tuple(tree, buffer, offset, title)
    if buffer:len() < offset + 24 then return offset end
    local range_tree = tree:add(difi_protocol, buffer(offset, 24), title)
    add_u64_freq(range_tree, cap_range_min_hz, buffer, offset, "minimum")
    add_u64_freq(range_tree, cap_range_max_hz, buffer, offset + 8, "maximum")
    add_u64_freq(range_tree, cap_range_resolution_hz, buffer, offset + 16, "resolution")
    return offset + 24
end

local function add_signed_if_offset_range_tuple(tree, buffer, offset, title)
    if buffer:len() < offset + 24 then return offset end
    local range_tree = tree:add(difi_protocol, buffer(offset, 24), title)
    local min_hz = get_int_freq(buffer(offset, 8):int64())
    local max_hz = get_int_freq(buffer(offset + 8, 8):int64())
    local res_hz = get_int_freq(buffer(offset + 16, 8):uint64())
    range_tree:add(cap_if_offset_range_min_hz, buffer(offset, 8), min_hz)
    range_tree:add(cap_if_offset_range_max_hz, buffer(offset + 8, 8), max_hz)
    range_tree:add(cap_if_offset_range_res_hz, buffer(offset + 16, 8), res_hz)
    return offset + 24
end

local function decode_frequency_section(buffer, tree, offset, count_field, value_field, range_name, packet_len)
    if packet_len < offset + 4 then return offset end
    local word = buffer(offset,4):uint()
    local is_discrete = bit.band(word, 0x8000) ~= 0
    local count = bit.band(word, 0x7fff)
    tree:add(count_field, buffer(offset,4), count):append_text(is_discrete and " (discrete)" or " (ranges)")
    offset = offset + 4
    if is_discrete then
        for i = 0, count - 1 do
            if packet_len >= offset + 8 then
                add_u64_freq(tree, value_field, buffer, offset, "#" .. (i + 1))
                offset = offset + 8
            end
        end
    else
        for i = 0, count - 1 do
            if packet_len >= offset + 24 then
                offset = add_range_tuple(tree, buffer, offset, range_name .. " range #" .. (i + 1))
            end
        end
    end
    return offset
end

local function decode_if_offset_section(buffer, tree, offset, packet_len)
    if packet_len < offset + 4 then return offset end
    local word = buffer(offset,4):uint()
    local is_discrete = bit.band(word, 0x8000) ~= 0
    local count = bit.band(word, 0x7fff)
    tree:add(cap_if_offset_count, buffer(offset,4), count):append_text(is_discrete and " (discrete)" or " (single range)")
    offset = offset + 4
    if is_discrete then
        for i = 0, count - 1 do
            if packet_len >= offset + 8 then
                add_i64_freq(tree, cap_if_offset_hz, buffer, offset, "#" .. (i + 1))
                offset = offset + 8
            end
        end
    else
        offset = add_signed_if_offset_range_tuple(tree, buffer, offset, "IF band offset range")
    end
    return offset
end

local function decode_range_capabilities(buffer, tree, packet_len)
    if packet_len < 116 then return end

    local w14 = buffer(52,4):uint()
    local num_ic = bit.rshift(w14, 16)
    local first_ic = bit.band(w14, 0xffff)
    local w15 = packet_len >= 60 and buffer(56,4):uint() or 0
    local w16 = packet_len >= 64 and buffer(60,4):uint() or 0
    tree:add(cap_supported_iccs, buffer(52, math.min(packet_len - 52, 12)),
             icc_list_string(num_ic, first_ic, w15, w16))

    if packet_len >= 68 then
        local count = bit.band(buffer(64,4):uint(), 0xffff)
        tree:add(cap_reference_point_count, buffer(64,4), count)
        for i = 0, math.min(count, 4) - 1 do
            local off = 68 + i * 4
            if packet_len >= off + 4 then tree:add(cap_reference_point, buffer(off,4)) end
        end
    end

    local mode = bit.band(buffer(84,4):uint(), 0x1)
    tree:add(cap_sample_rate_mode, buffer(84,4),
             mode == 1 and "fixed ratio between rates" or "fixed resolution")
    add_range_tuple(tree, buffer, 88, "Sample rate range")
    tree:add(cap_min_sr_bw_ratio, buffer(112,4))

    local offset = 116
    offset = decode_frequency_section(buffer, tree, offset, cap_if_frequency_count,
                                      cap_if_frequency_hz, "IF frequency", packet_len)
    offset = decode_frequency_section(buffer, tree, offset, cap_rf_frequency_count,
                                      cap_rf_frequency_hz, "RF frequency", packet_len)
    offset = decode_if_offset_section(buffer, tree, offset, packet_len)

    if packet_len >= offset + 4 then
        local ref_word = buffer(offset,4):uint()
        tree:add(cap_ref_level_min_db, buffer(offset,2), get_dB_q8(bit.rshift(ref_word, 16)))
        tree:add(cap_ref_level_max_db, buffer(offset + 2,2), get_dB_q8(bit.band(ref_word, 0xffff)))
        offset = offset + 4
    end
    if packet_len >= offset + 4 then
        local res_word = buffer(offset,4):uint()
        tree:add(cap_ref_level_resolution_db, buffer(offset,2), get_dB_q8(bit.rshift(res_word, 16)))
        offset = offset + 4
    end
    if packet_len >= offset + 8 then tree:add(cap_sid_delay_fs, buffer(offset,8)); offset = offset + 8 end
    if packet_len >= offset + 4 then
        local w = buffer(offset,4):uint()
        local depth_indicator = bit.rshift(bit.band(w, 0xfff80000), 19)
        tree:add(cap_bit_depth_indicator, buffer(offset,4), depth_indicator)
        tree:add(cap_bit_depths, buffer(offset,4), bit_depths_string(depth_indicator))
        tree:add(cap_max_streams, buffer(offset + 2,2), bit.band(w, 0xffff))
        offset = offset + 4
    end
    if packet_len >= offset + 8 then tree:add(buffer_size, buffer(offset,8)); offset = offset + 8 end
    if packet_len >= offset + 8 then add_note(tree, "Nearly Late Threshold: " .. tostring(buffer(offset,8):int64())); offset = offset + 8 end
    if packet_len >= offset + 12 then
        tree:add(cap_link_timeout_int, buffer(offset,4))
        tree:add(cap_link_timeout_frac, buffer(offset + 4,8))
        offset = offset + 12
    end
    if packet_len >= offset + 12 then
        tree:add(cap_context_timeout_int, buffer(offset,4))
        tree:add(cap_context_timeout_frac, buffer(offset + 4,8))
    end
end

local function decode_status_report(buffer, tree, packet_len)
    if packet_len < 56 then return end
    local word1 = buffer(48,4):uint()
    local word2 = buffer(52,4):uint()
    local status_tree = tree:add(difi_protocol, buffer(48, math.min(packet_len - 48, 8)), "Decoded Status Bits")
    status_tree:add(status_packet_errors, buffer(48,4))
    status_tree:add_packet_field(status_timeout_link_termination, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_sink_bw_exceeded, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_stream_capacity_exceeded, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_frequency_conflict, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_unsupported_bit_depth, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_payload_config_error, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_sample_rate_out_range, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_sample_rate_res_error, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_ref_level_mismatch, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_if_offset_too_large, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_rf_freq_out_range, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_rf_freq_res_error, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_if_freq_out_range, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_if_freq_res_error, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_fractional_hz, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_bw_too_large, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_ref_point_unknown, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_late_data, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_late_context, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_packet_class_undefined, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_pcc_not_in_icc, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_icc_not_defined, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_pad_bit_count, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_incorrect_packet_size, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_wrong_tsf, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_wrong_tsi, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_wrong_tsm, buffer(48,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_wrong_packet_type, buffer(48,4), ENC_BIG_ENDIAN)

    status_tree:add(status_system_errors_warnings, buffer(52,4))
    status_tree:add_packet_field(status_link_termination, buffer(52,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_context_error_timeout, buffer(52,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_buffer_overflow, buffer(52,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_buffer_underflow, buffer(52,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_time_lol, buffer(52,4), ENC_BIG_ENDIAN)
    status_tree:add_packet_field(status_freq_lol, buffer(52,4), ENC_BIG_ENDIAN)

    local decoded = {}
    local function add_if(mask, word, name)
        if bit.band(word, mask) ~= 0 then table.insert(decoded, name) end
    end
    add_if(0x00000010, word1, "Timeout/Link Termination")
    add_if(0x00000020, word1, "Sink BW Capacity Exceeded")
    add_if(0x00000040, word1, "Stream Capacity Exceeded")
    add_if(0x00000080, word1, "Frequency Allocation Conflict")
    add_if(0x00000100, word1, "Unsupported Bit Depth")
    add_if(0x00000200, word1, "Data Payload Config Error")
    add_if(0x00000400, word1, "Sample Rate Out of Range")
    add_if(0x00000800, word1, "Sample Rate Resolution Error")
    add_if(0x00001000, word1, "Reference Level Mismatch")
    add_if(0x00002000, word1, "IF Offset Too Large")
    add_if(0x00004000, word1, "RF Frequency Out of Range")
    add_if(0x00008000, word1, "RF Frequency Resolution Error")
    add_if(0x00010000, word1, "IF Frequency Out of Range")
    add_if(0x00020000, word1, "IF Frequency Resolution Error")
    add_if(0x00040000, word1, "Fractional Hz Specified")
    add_if(0x00080000, word1, "Bandwidth Too Large for Sample Rate")
    add_if(0x00100000, word1, "Reference Point Not Recognized")
    add_if(0x00200000, word1, "Late Data Packet")
    add_if(0x00400000, word1, "Late Context Packet")
    add_if(0x02000000, word2, "Link Termination")
    add_if(0x04000000, word2, "Context Error Timeout")
    add_if(0x10000000, word2, "Buffer Overflow")
    add_if(0x20000000, word2, "Buffer Underflow")
    add_if(0x40000000, word2, "Timebase LOL")
    add_if(0x80000000, word2, "Frequency LOL")
    if #decoded == 0 then
        tree:add(status_summary, buffer(48, math.min(packet_len - 48, 8)), "No errors/warnings set")
    else
        tree:add(status_summary, buffer(48, math.min(packet_len - 48, 8)), table.concat(decoded, ", "))
    end
end

-- Common header
local function difi_common_dissector(buffer, tree)
    local word0 = buffer(0, 4):uint()
    local word3 = buffer(12, 4):uint()

    tree:add(packet_type,  bit.rshift(bit.band(word0, 0xF0000000), 28))
    tree:add(packet_size,  bit.band(word0, 0xffff))
    tree:add(seq_num,      bit.rshift(bit.band(word0, 0x000F0000), 16))
    tree:add(tsi,          bit.rshift(bit.band(word0, 0x00C00000), 22))
    tree:add(tsf,          bit.rshift(bit.band(word0, 0x00300000), 20))
    tree:add(stream_id,    buffer(4, 4):uint())

    -- padding bits (byte 8) + OUI/CID (bytes 9..11)
    tree:add(padding_bits, buffer(8,1):uint())
    tree:add(oui,          buffer(9,3):uint())

    tree:add_packet_field(information_class, buffer(12, 2), ENC_BIG_ENDIAN)
    tree:add_packet_field(packet_class_code, buffer(14, 2), ENC_BIG_ENDIAN)
    tree:add(int_timestamp,  buffer(16, 4):uint())
    tree:add(frac_timestamp, buffer(20, 8):uint64())
end

-- Packet dissectors ------------------------------------------

local function context_pkt_dissector(buffer, tree, name)
    if buffer:len() < 108 then return end

    local subtree = tree:add(difi_protocol, buffer(0, 108), "DIFI Protocol, " .. name)

    -- Header
    difi_common_dissector(buffer, subtree)

    -- Additional header fields
    subtree:add(ctxt_cif,  buffer(28, 4):uint())
    subtree:add(ref_point, buffer(32, 4):uint())

    -- 64-bit fixed-point -> integer Hz via shift
    local bw_int       = get_int_freq(buffer(36, 8):uint64())
    local if_ref_int   = get_int_freq(buffer(44, 8):uint64())
    local rf_ref_int   = get_int_freq(buffer(52, 8):uint64())
    local if_offset_i  = get_int_freq(buffer(60, 8):int64())
    subtree:add(bandwidth,   bw_int)
    subtree:add(if_ref_freq, if_ref_int)
    subtree:add(rf_ref_freq, rf_ref_int)
    subtree:add(if_offset,   if_offset_i)

    -- Levels/Gains (two 16-bit fixed-point values in each 32-bit word)
    local level_word = buffer(68,4):int()
    local ref_level_word16     = bit.band(level_word, 0xFFFF)
    local scaling_level_word16 = bit.rshift(bit.band(level_word, 0xFFFF0000), 16)
    subtree:add(ref_level,     get_dB(ref_level_word16))
    subtree:add(scaling_level, get_dB(scaling_level_word16))

    local gain_word = buffer(72,4):int()
    local stage1_gain_word16 = bit.band(gain_word, 0xFFFF)
    local stage2_gain_word16 = bit.rshift(bit.band(gain_word, 0xFFFF0000), 16)
    subtree:add(stage1_gain, get_dB(stage1_gain_word16))
    subtree:add(stage2_gain, get_dB(stage2_gain_word16))

    local sample_rate_int = get_int_freq(buffer(76,8):uint64())
    subtree:add(sample_rate, sample_rate_int)

    subtree:add(timestamp_adj, buffer(84, 8):uint64())
    subtree:add(time_cal,      buffer(92, 4):uint())
    subtree:add(se_indicator,  buffer(96, 4):uint())
    local data_format_word64 = buffer(100, 8):uint64()
    subtree:add(data_format, data_format_word64)
    subtree:add(bytes_per_sample, get_bytes_per_sample(data_format_word64))
end

local function data_pkt_dissector(buffer, tree, name)
    if buffer:len() < 28 then return end

    local length  = buffer:len()
    local subtree = tree:add(difi_protocol, buffer(0, 28), "DIFI Protocol, " .. name)

    -- Header
    difi_common_dissector(buffer, subtree)

    -- Payload
    local payload_len   = length - 28
    if payload_len > 0 then
        local data_subtree = subtree:add(difi_protocol, buffer(28, payload_len), "Data")
        data_subtree:add(data, buffer(28, payload_len))
    end
end

local function version_pkt_dissector(buffer, tree, name)
    if buffer:len() < 44 then return end

    local subtree = tree:add(difi_protocol, buffer(0, 44), "DIFI Protocol, " .. name)

    -- Header
    difi_common_dissector(buffer, subtree)

    -- Version fields
    subtree:add(ctxt_cif0, buffer(28, 4):uint())
    subtree:add(ctxt_cif1, buffer(32, 4):uint())
    subtree:add(v49spec,   buffer(36, 4):uint())

    -- Packed bitfields in the last 32-bit word
    subtree:add_packet_field(year,      buffer(40,4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(day,       buffer(40,4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(revision,  buffer(40,4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(user_type, buffer(40,4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(icd_version, buffer(40,4), ENC_BIG_ENDIAN)
end

local function control_pkt_dissector(buffer, tree, name)
    if buffer:len() < 84 then return end

    local subtree = tree:add(difi_protocol, buffer(0, 84), "DIFI Protocol, " .. name)

    -- Header
    difi_common_dissector(buffer, subtree)

    subtree:add_packet_field(cam_field,     buffer(28, 4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(message_id,    buffer(32, 4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(controllee_id, buffer(36, 4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(controller_id, buffer(40, 4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(ctrl_cif0,     buffer(44, 4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(ctrl_cif1,     buffer(48, 4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(ref_point,     buffer(52, 4), ENC_BIG_ENDIAN)

    local sample_rate_int = get_int_freq(buffer(56,8):uint64())
    subtree:add(sample_rate, sample_rate_int)

    subtree:add_packet_field(timestamp_adj,   buffer(64, 8), ENC_BIG_ENDIAN)
    subtree:add_packet_field(buffer_size,     buffer(72, 8), ENC_BIG_ENDIAN)
    subtree:add_packet_field(buffer_reserved, buffer(80, 2), ENC_BIG_ENDIAN)
    subtree:add_packet_field(buffer_level,    buffer(82, 2), ENC_BIG_ENDIAN)
    subtree:add_packet_field(buffer_overflow, buffer(82, 2), ENC_BIG_ENDIAN)
    subtree:add_packet_field(near_full,       buffer(82, 2), ENC_BIG_ENDIAN)
    subtree:add_packet_field(near_empty,      buffer(82, 2), ENC_BIG_ENDIAN)
    subtree:add_packet_field(buffer_underflow,buffer(82, 2), ENC_BIG_ENDIAN)
end

local function extension_command_pkt_dissector(buffer, tree, name)
    -- DIFI 1.3 Extension Command packets all include the 7-word prologue plus
    -- CAM, Message ID, Controllee ID, Controller ID, and CIF0 (12 words total).
    -- Packet classes 0x0007, 0x0008, and 0x0009 then interpret the remaining
    -- words differently.
    if buffer:len() < 48 then return end

    local word0 = buffer(0,4):uint()
    local word3 = buffer(12,4):uint()
    local packet_class_int = bit.band(word3, 0x0000ffff)
    local size_words = bit.band(word0, 0xffff)
    local size_bytes = size_words * 4
    local packet_len = buffer:len()
    if size_words > 0 and size_bytes < packet_len then
        packet_len = size_bytes
    end

    local subtree = tree:add(difi_protocol, buffer(0, packet_len), "DIFI Protocol, " .. name)

    difi_common_dissector(buffer, subtree)

    subtree:add(command_indicator, bit.rshift(bit.band(word0, 0x07000000), 24))
    subtree:add_packet_field(cam_field,     buffer(28, 4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(message_id,    buffer(32, 4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(controllee_id, buffer(36, 4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(controller_id, buffer(40, 4), ENC_BIG_ENDIAN)
    subtree:add_packet_field(ctrl_cif0,     buffer(44, 4), ENC_BIG_ENDIAN)

    local cif0 = buffer(44, 4):uint()
    local is_short_form = bit.band(cif0, 0x80000000) ~= 0
    add_difi13_cif_summary(subtree, buffer, packet_class_int, packet_len, cif0, is_short_form)

    if packet_class_int == 0x0007 then
        -- Sink Capability Query Control.
        -- Short form: CIF0 bit 31 set, optional Sink Time Calibration words.
        -- Long form: CIF0 bit 31 clear, CIF1 follows.
        if is_short_form then
            subtree:add(extension_form, buffer(44,4), "Sink Capability Query: Short form")
            if packet_len >= 60 then
                subtree:add_packet_field(sink_time_cal_int_timestamp,  buffer(48, 4), ENC_BIG_ENDIAN)
                subtree:add_packet_field(sink_time_cal_frac_timestamp, buffer(52, 8), ENC_BIG_ENDIAN)
            end
        else
            subtree:add(extension_form, buffer(44,4), "Sink Capability Query: Long form")
            if packet_len >= 52 then
                subtree:add_packet_field(ctrl_cif1, buffer(48, 4), ENC_BIG_ENDIAN)
            end
        end

    elseif packet_class_int == 0x0008 then
        -- Sink Capability Response Acknowledge.
        -- Short form carries echoed query timestamps and sink reception time.
        -- Long form carries a variable capabilities payload after CIF1.
        if is_short_form then
            subtree:add(extension_form, buffer(44,4), "Sink Capability Response: Short form")
            if packet_len >= 72 then
                subtree:add_packet_field(control_int_timestamp,         buffer(48, 4), ENC_BIG_ENDIAN)
                subtree:add_packet_field(control_frac_timestamp,        buffer(52, 8), ENC_BIG_ENDIAN)
                subtree:add_packet_field(sink_reception_int_timestamp,  buffer(60, 4), ENC_BIG_ENDIAN)
                subtree:add_packet_field(sink_reception_frac_timestamp, buffer(64, 8), ENC_BIG_ENDIAN)
            end
        else
            subtree:add(extension_form, buffer(44,4), "Sink Capability Response: Long form")
            if packet_len >= 52 then
                subtree:add_packet_field(ctrl_cif1, buffer(48, 4), ENC_BIG_ENDIAN)
            end
            if packet_len > 52 then
                local cap_tree = subtree:add(capabilities_payload, buffer(52, packet_len - 52))
                if packet_len >= 88 then
                    local w22 = buffer(84,4):uint()
                    if bit.band(w22, 0x8000) ~= 0 then
                        cap_tree:add(capability_format, buffer(84,4), "Long form, discrete values")
                        decode_discrete_capabilities(buffer, cap_tree, packet_len)
                    else
                        cap_tree:add(capability_format, buffer(84,4), "Long form, ranges")
                        decode_range_capabilities(buffer, cap_tree, packet_len)
                    end
                end
            end
        end

    elseif packet_class_int == 0x0009 then
        -- Status Report Control. CIF0 is all zero per DIFI 1.3; remaining
        -- words are the status-code payload plus optional quantitative fields.
        if packet_len > 48 then
            subtree:add(status_code_payload, buffer(48, packet_len - 48))
            decode_status_report(buffer, subtree, packet_len)
        end

    elseif packet_len > 48 then
        subtree:add(extension_payload, buffer(48, packet_len - 48))
    end
end

-- Heuristic --------------------------------------------------

local function heuristic_checker(buffer, pinfo, tree)
    -- guard for minimal header: 7 * 32-bit words = 28 bytes
    if buffer:len() < 28 then return false end

    -- OUI/CID is 24 bits at bytes 9..11 (pad at byte 8)
    local potential_oui = buffer(9, 3):uint()
    if (potential_oui ~= 0x7C386C and potential_oui ~= 0x6A621E) then
        return false
    end

    local word0 = buffer(0,4):uint()
    local packet_type_int = bit.rshift(bit.band(word0,0xf0000000), 28)
    local valid_ptype = (packet_type_int == 4 or packet_type_int == 5 or packet_type_int == 1 or packet_type_int == 6 or packet_type_int == 7)
    if not valid_ptype then return false end

    if packet_type_int == 7 then
        local packet_class_int = bit.band(buffer(12,4):uint(), 0x0000ffff)
        local valid_extension_class = (packet_class_int == 7 or packet_class_int == 8 or packet_class_int == 9)
        if not valid_extension_class then return false end
    end

    -- Optional: basic size sanity check (packet_size is in 32-bit words)
    local size_words = bit.band(word0, 0xffff)
    local size_bytes = size_words * 4
    if size_words > 0 and buffer:len() < size_bytes then
        return false
    end

    -- Looks like DIFI—hand over to the dissector
    difi_protocol.dissector(buffer, pinfo, tree)
    return true
end

-- Main dissector --------------------------------------------

function difi_protocol.dissector(buffer, pinfo, tree)
    if buffer:len() < 28 then return end

    local word0 = buffer(0,4):uint()
    local word3 = buffer(12,4):uint()
    local packet_type_int  = bit.rshift(bit.band(word0,0xf0000000), 28)
    local packet_class_int = bit.band(word3, 0x0000ffff)

    -- Optional: enforce size sanity here as well
    local size_words = bit.band(word0, 0xffff)
    local size_bytes = size_words * 4
    if size_words > 0 and buffer:len() < size_bytes then
        return
    end

    local name = "unknown type=" .. packet_type_int .. " , class=" .. packet_class_int

    if packet_type_int == 0x4 then
        if packet_class_int == 0 or packet_class_int == 1 then name = "Standard Flow Signal Context Packet" end
        if packet_class_int == 3 then name = "Sample Count Context Packet" end
        if packet_class_int == 4 then
            name = "Version Flow Signal Context Packet"
            version_pkt_dissector(buffer, tree, name)
        else
            context_pkt_dissector(buffer, tree, name)
        end

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

    elseif packet_type_int == 0x7 then
        if packet_class_int == 7 then name = "Sink Capability Query Control Packet" end
        if packet_class_int == 8 then name = "Sink Capability Response Acknowledge Packet" end
        if packet_class_int == 9 then name = "Status Report Control Packet" end
        extension_command_pkt_dissector(buffer, tree, name)
    end

    pinfo.cols.protocol = difi_protocol.name
    pinfo.cols.info = name
end

-- Register heuristic on UDP
difi_protocol:register_heuristic("udp", heuristic_checker)
