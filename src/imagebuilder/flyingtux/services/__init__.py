import os_service
from metux.util.log import info
from ..util import FT_ConfigError
import x11, dev, userdir, webproxy

os_services = {
    'x11':            x11.X11,
    'temp-homedir':   os_service.TempHomedir,
    'user-documents': userdir.UserDocuments,
    'user-pictures':  userdir.UserPictures,
    'user-movies':    userdir.UserMovies,
    'user-downloads': userdir.UserDownloads,
    'dri':            dev.DriDevice,
    'service-dir':    os_service.ServiceDir,
    'data-volume':    os_service.DataVolume,
    'web':            webproxy.WebProxy,
}

class E_UnknownOSService(FT_ConfigError):
    def __init__(self, name, spec, runner):
        self.my_name = name
        self.my_spec = spec
        self.my_runner = runner
        Exception.__init__(self, "Unknown OS service: "+name)

def get_os_service(name, spec, runner):
    if name not in os_services:
        raise E_UnknownOSService(name, spec, runner)
    return os_services[name](spec, runner)

def process_os_service(name, spec, runner):
    return get_os_service(name, spec, runner).process()
