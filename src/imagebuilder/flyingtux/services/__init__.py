from os_service import X11, TempHomedir
from metux.util.log import info

os_services = {
    'x11': X11,
    'temp-homedir': TempHomedir
}

def get_os_service(name, spec, runner):
    if name not in os_services:
        raise Exception("unknown os service: "+name)
    return os_services[name](spec, runner)

def process_os_service(name, spec, runner):
    info("Processing OS service: "+name)
    return get_os_service(name, spec, runner).process()
