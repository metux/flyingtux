from os_service import X11, TempHomedir
from metux.util.log import info

os_services = {
    'x11': X11,
    'temp-homedir': TempHomedir
}

class E_UnknownOSService(Exception):
    def __init__(self, name, spec, runner):
        self.my_name = name
        self.my_spec = spec
        self.my_runner = runner
        Exception.__init__("Unknown OS service: "+name)

def get_os_service(name, spec, runner):
    if name not in os_services:
        raise E_UnknownOSService(name, spec, runner)
    return os_services[name](spec, runner)

def process_os_service(name, spec, runner):
    info("Processing OS service: "+name)
    return get_os_service(name, spec, runner).process()
