from oasis.utils.dissectors import alert, monitor, timing

message_types = {
    0xF0 : {"type":"MONITOR", "parser":monitor.parse_monitor_message, "formatter": monitor.format_monitor_message},
    0xF1 : {"type":"ALERT", "parser":alert.parse_alert_message, "formatter": alert.format_alert_message},
    0xF2 : {"type":"TIMING", "parser":timing.parse_timestamps_message, "formatter": timing.format_timestamps_message},
}

def parse_log_message(message, formatting=True):
    try:
        msg = message_types[message[0]]["parser"](message[1:])
        if msg is not None:
            if formatting:
                return message_types[message[0]]["formatter"](msg)
            else:
                return msg
    except:
        return  "LOG => " + message.hex()
