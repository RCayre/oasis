import struct

alert_messages_codes = {
  1 : "BTLEJACK",
  2 : "BTLEJUICE",
  3 : "GATTACKER",
  4 : "INJECTABLE",
  5 : "JAMMING",
  6 : "KNOB"
}

def parse_alert_message(message):
    alert_type = alert_messages_codes[message[0]]
    if alert_type == "BTLEJACK":
        return parse_alert_btlejack_message(message[1:])
    elif alert_type == "BTLEJUICE":
        return parse_alert_btlejuice_message(message[1:])
    elif alert_type == "GATTACKER":
        return parse_alert_gattacker_message(message[1:])
    elif alert_type == "INJECTABLE":
        return parse_alert_injectable_message(message[1:])
    elif alert_type == "JAMMING":
        return parse_alert_jammming_message(message[1:])
    elif alert_type == "KNOB":
        return parse_alert_knob_message(message[1:])
    else:
        return parse_alert_unknown_message(message[1:])

def parse_alert_btlejack_message(message):
    access_address,  = struct.unpack("I", message)
    return {"type":"BTLEJACK", "access_address":access_address}

def parse_alert_btlejuice_message(message):
    bd_address = ":".join(["{:02x}".format(i) for i in message])
    return {"type":"BTLEJUICE", "bd_address":access_address}

def parse_alert_gattacker_message(message):
    bd_address = ":".join(["{:02x}".format(i) for i in message])
    return {"type":"GATTACKER", "bd_address":access_address}

def parse_alert_injectable_message(message):
    access_address,  = struct.unpack("I", message)
    return {"type":"INJECTABLE", "access_address":access_address}

def parse_alert_jamming_message(message):
    channel_number,  = struct.unpack("I", message)
    return {"type":"JAMMING", "channel_number":channel_number}

def parse_alert_knob_message(message):
    entropy = message[0]
    return {"type":"KNOB", "entropy":entropy}

def parse_alert_unknown_message(message):
    entropy = message[0]
    return {"type":"UNKNOWN", "raw_data":message.hex()}

def format_alert_message(message):
    out = "ALERT => " + message["type"].lower() +" ("
    if "access_address" in message:
        out += "Access Address: {:08x}".format(message["access_address"])
    if "bd_address" in message:
        out += "BD Address: " + message["bd_address"]
    if "raw_data" in message:
        out += "Raw data: " + message["raw_data"]
    if "channel_number" in message:
        out += "Channel number: "+str(message["channel_number"])
    if "entropy" in message:
        out += "Entropy: "+str(message["entropy"])
    out += ")"
    return out
