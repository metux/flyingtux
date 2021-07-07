from metux.util.specobject import SpecObject
from metux.util.log import info
from os import environ
from os_service import Base

"""
Access to X11 display.

2DO: add user-configured redirection to somewhere else, e.g.
a nested Xserver, so app has no access to X resources of other
applications.
"""
class X11(Base):
    permissions = {
        '__enabled__': { 'default': True },
        'shm':     { 'default': True, 'description': 'shared memory extension' },
    }

    settings = {
        'x11-display': {
            'default':     '${ENV::DISPLAY}',
            'type':        'string',
            'description': 'number of the X11 display to attach to',
        },
        'x11-socketdir': {
            'default':     '/tmp/.X11-unix',
            'type':        'host-path',
            'description': 'directory of X11 sockets',
        },
    }

    def compute(self):
        import re

        display = self.get_setting('x11-display')

        disp = re.search('^:([0-9]+)(\.[0-9]+|)$', display).group(1)
        sockname = self.get_path_setting('x11-socketdir')+'/X'+disp

        self.info("display: "+str(display))
        self.add_env('DISPLAY', display)
        self.bind_file_direct(sockname)

        if self.is_permitted('shm'):
            self.info("host shm: enabled")
            self.set_container_opt('ipc', 'host')
        else:
            self.info("host shm: disabled")
