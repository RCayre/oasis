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
    if len(message) != 1+4*3:
      return None
    else:
      message_type = timestamps_message_codes[message[0]]
      start, callbacks, end = struct.unpack("III", message[1:])
      return {"type":message_type, "start":start, "end":end, "callbacks":callbacks}

def format_timestamps_message(message):
    ed = message["end"] - message["start"]
    md = message["end"] - message["callbacks"]
    out = "TIMING => " + message["type"].lower() +" (start: {}, callbacks: {}, end: {}, event_duration: {}, module_duration: {})".format(message["start"], message["callbacks"], message["end"],ed, md)
    return out
