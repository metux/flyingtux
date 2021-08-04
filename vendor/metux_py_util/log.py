from sys import stderr
from datetime import datetime

color_normal = "\033[0;32;39m"
color_yellow = "\033[1;32;33m"
color_green  = "\033[1;32;40m"
color_cyan   = "\033[1;32;36m"
color_red    = "\033[1;32;91m"

last_time = datetime.now()

def _wr(prefix, color, text):
    global last_time
    now = datetime.now()
    diff = now - last_time
    diff = diff.microseconds
    stderr.write("%s%5s%s [%8s] %s\n" % (color, prefix, color_normal, diff, text))
    last_time = now

def info(text):
    _wr("INFO:", color_green, text)

def warn(text):
    _wr("WARN:", color_yellow, text)

def err(text):
    _wr("ERR:", color_red, text)

def debug(text):
    _wr("DBG:", color_cyan, text)
