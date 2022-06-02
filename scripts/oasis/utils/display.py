import time,threading

class Style:
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

"━"
def waiting(message):
    animation = [
        "          ",
        "━         ",
        "━━        ",
        "━━━       ",
        "━━━━      ",
        "━━━━━     ",
        "━━━━━━    ",
        "━━━━━━━   ",
        "━━━━━━━━  ",
        "━━━━━━━━━ ",
        "━━━━━━━━━━",
        " ━━━━━━━━━",
        "  ━━━━━━━━",
        "   ━━━━━━━",
        "    ━━━━━━",
        "     ━━━━━",
        "      ━━━━",
        "       ━━━",
        "        ━━",
        "         ━",
    ]
    waiting.i += 1
    print(animation[waiting.i % len(animation)]+" "+message+(" "*(len(waiting.last_message)-len(message)) if len(message) < len(waiting.last_message) else ""), end='\r')
    waiting.last_message = message

waiting.i = 0
waiting.last_message = ""

def waiting_thread(message):
    waiting_thread.current_message = message
    while waiting_thread.enabled:
        waiting(waiting_thread.current_message)
        time.sleep(0.1)
    print(waiting_thread.final_message+"           "+(" "*(len(waiting_thread.final_message)-len(waiting_thread.current_message)) if len(waiting_thread.final_message) < len(waiting_thread.current_message) else ""))

waiting_thread.enabled = True
waiting_thread.final_message = ""

def start_waiting(message=""):
    waiting_thread.enabled = True
    threading.Thread(target=waiting_thread, args=(message,)).start()

def update_waiting_message(message):
    waiting_thread.current_message = message

def stop_waiting(message):
    waiting_thread.final_message = message
    waiting_thread.enabled = False


def print_info(msg="",end="\n",start=""):
    print(start,"\U0001F535",msg,end=end)

def print_warning(msg="",end="\n",start=""):
    print(start,"\U0001F7E0",msg,end=end)

def print_success(msg="",end="\n",start=""):
    print(start,"\U0001F7E2",msg,end=end)

def print_error(msg="",end="\n",start=""):
    print(start,"\U0001F534",msg,end=end)

def print_msg(msg="",end="\n", start="", type="info"):
    if type == "info":
        print_info(msg,end,start)
    elif type == "error":
        print_error(msg,end,start)
    elif type == "warning":
        print_warning(msg,end,start)
    elif type == "success":
        print_success(msg,end,start)
