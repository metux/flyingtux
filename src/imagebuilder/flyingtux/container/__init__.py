from metux.util import log
import subprocess
from docker import ContainerDriverDocker
from ..util import FT_UnsupportedJail

"""
This module contains the runtime container implementations - this is used
for running an application from an existing image that previously had been
built in a build jail.

For now we only support docker, but smaller runtimes like runc will be
implemented later. Docker is a good start for the initial implementation
and also well suited for running on classic GNU/Linux systems (e.g.
desktop/notebook, servers, etc), but still requires too much resources
for small mobile devices like smartphones, infotainment, etc.

When the fundamental mechanisms and infrastructure is settled, it's time
to optimize for the small device / embedded world, while collecting more
practical experience on larger machines and ironing out bugs.
"""

jail_drivers = {
    'docker': ContainerDriverDocker
}

def get(param):
    if param['engine'] in jail_drivers:
        return jail_drivers[param['engine']](param)

    raise FT_UnsupportedJail("unknown container type "+param['engine'])
