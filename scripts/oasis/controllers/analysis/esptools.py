import struct, hashlib

ESP32_MAPPING = {
    "ROM0" : [(0x40000000, 0x4005FFFF)],
    "ROM1" : [(0x3FF90000, 0x3FF9FFFF)],
    "SRAM0": [(0x40070000, 0x4009FFFF)],
    "SRAM1": [(0x3FFE0000, 0x3FFFFFFF), (0x400A0000, 0x400BFFFF)],
    "SRAM2": [(0x3FFAE000, 0x3FFDFFFF)],
    "RTC_FAST":[(0x3ff80000, 0x3ff81fff), (0x400c0000, 0x400c1fff)],
    "RTC_SLOW":[(0x50000000, 0x50001fff)],
    "EXT_FLASH":[(0x3f400000, 0x3f7fffff), (0x400c2000, 0x40bfffff)],
    "EXT_RAM":[(0x3f800000, 0x3fbfffff)],
}

def espChecksum(data,init):
    state = init
    for i in data:
        state ^= i
    return state

def imageToInternal(input_image_file):
    header = None
    raw_firmware = None
    with open(input_image_file,"rb") as f:
        data = f.read()
        raw_firmware = data
        header = data[:8+16]
        entryPoint = struct.unpack("I", data[4:8])[0]
        number_of_segments = data[1]
        current_segment = 8+16 # header size
        segments = []
        for i in range(number_of_segments):
            segment_header = data[current_segment:current_segment+8]
            segment_address, segment_length = struct.unpack("<II",segment_header)
            segment_data = data[current_segment+8:current_segment+8+segment_length]
            label = "UNKNOWN"
            for memory_label, zones in ESP32_MAPPING.items():
                for zone in zones:
                    if segment_address >= zone[0] and segment_address <= zone[1]:
                        label = memory_label
            segments.append({"address":segment_address, "length":segment_length, "data":segment_data, "label":label})
            current_segment+=(8+segment_length)

        while data[current_segment] == 0:
            current_segment+=1
        checksum = data[current_segment]
        hash_sha256 = data[current_segment+1:]

        return header, raw_firmware, segments, entryPoint

def internalToImage(header,segments, entryPoint):
    new_header = bytes([header[0], len(segments)]) + header[2:4] + struct.pack("I", entryPoint) + header[8:]
    data_zone = b""
    checksum = 0xef
    for segment in segments:
        data_zone += struct.pack("<II", segment["address"],segment["length"])
        data_zone += segment["data"]
        checksum = espChecksum(segment["data"], checksum)
    output = new_header + data_zone + b"\x00"
    while len(output) % 16 != 0:
        output += b"\x00"
    output = output[:-1] + bytes([checksum])
    hash_sha256 = hashlib.sha256(output).digest()
    output += hash_sha256

    return output

def readInImage(segments, address, length):
    for segment in segments:
        if address >= segment["address"] and address <= segment["address"] + segment["length"]:
            offset = address-segment["address"]
            return segment["data"][offset:offset+length]
    return None


def writeInImage(segments, address, data):
    found = False
    for i in range(len(segments)):
        if address >= segments[i]["address"] and address <= segments[i]["address"] + segments[i]["length"]:
            found = True
            offset = address-segments[i]["address"]
            segments[i]["data"] = segments[i]["data"][:offset] + data + segments[i]["data"][offset+len(data):]
            segments[i]["length"] = len(segments[i]["data"])
    if not found:
        segments.append({"address":address, "length":len(data), "data":data})
    return segments
