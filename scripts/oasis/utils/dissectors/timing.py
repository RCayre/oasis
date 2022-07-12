import struct

timestamps_message_codes = {
  0 : "SCAN_EVENT",
  1 : "TIME_EVENT",
  2 : "CONN_TX_EVENT",
  3 : "CONN_RX_EVENT",
  4 : "CONN_INIT_EVENT",
  5 : "CONN_DELETE_EVENT"
}
def parse_timestamps_message(message):
    if len(message) != 1+4*2:
      return None
    else:
      message_type = timestamps_message_codes[message[0]]
      event_delay, modules_delay = struct.unpack("II", message[1:])
      return {"type":message_type, "event_delay":event_delay, "modules_delay":modules_delay}

def format_timestamps_message(message):
    out = "TIMING => " + message["type"].lower() +" (event_duration: {}, module_duration: {})".format(message["event_delay"], message["modules_delay"])
    return out
