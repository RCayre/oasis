import struct


def get_gap_role(gap_role):
    role = "UNKNOWN"
    if gap_role == 0:
        role = "ADVERTISER"
    elif gap_role == 1:
        role = "PERIPHERAL"
    elif gap_role == 2:
        role = "SCANNER"
    elif gap_role == 3:
        role = "CENTRAL"
    else:
        role = "UNKNOWN"
    return role

def parse_monitor_message(message):
    try:
        if message[0] == 0:
            return parse_time_monitor_message(message)
        elif message[0] == 1:
            return parse_scan_rx_monitor_message(message)
        elif message[0] == 2:
            return parse_conn_init_monitor_message(message)
        elif message[0] == 3:
            return parse_conn_rx_monitor_message(message)
    except struct.error:
        return None
    return None

def parse_time_monitor_message(message):
    timestamp,address6, address5, address4, address3, address2, address1, gap_role = struct.unpack("IBBBBBBB",message[1:])
    address = ":".join(["{:02x}".format(i) for i in [address1,address2,address3,address4,address5,address6]])
    return {"type":"TIME", "timestamp":timestamp, "address": address, "gap_role":get_gap_role(gap_role)}

def parse_scan_rx_monitor_message(message):
    timestamp, valid, channel, rssi = struct.unpack("IHHH", message[1:11])
    packet = message[11:]
    return {"type":"SCAN_RX","timestamp" :timestamp, "valid":valid, "channel":channel, "rssi":rssi, "packet":bytes(packet)}

def parse_conn_init_monitor_message(message):
    access_address, crc_init, hop_interval = struct.unpack("IIH",message[1:11])
    channel_map =  message[11:][::-1]
    access_address = hex(access_address)
    crc_init = hex(crc_init)
    return {"type":"CONN_INIT","access_address" :access_address, "crc_init":crc_init, "hop_interval":hop_interval, "channel_map":bytes(channel_map)}

def parse_conn_rx_monitor_message(message):
    timestamp, valid, channel, rssi = struct.unpack("IHHH", message[1:11])
    packet = message[11:]
    return {"type":"CONN_RX","timestamp" :timestamp, "valid":valid, "channel":channel, "rssi":rssi, "packet":bytes(packet)}


def format_monitor_message(message):
    out = "MONITORING => " + message["type"].lower() +" ("
    for k,v in message.items():
        if k != "type":
            out += k
            out += ": "
            if isinstance(v,bytes):
                out += v.hex()
            elif isinstance(v,int):
                out += str(v)
            elif isinstance(v,str):
                out += v
            out += ", "
    out = out[:-2]+")"
    return out
