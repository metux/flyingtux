from metux.util import log
from metux.util.fs import mkdir
import subprocess
from user import JailDriverUser
from docker import JailDriverDocker

jail_drivers = {
    'user': JailDriverUser,
    'docker': JailDriverDocker
}

def get(param):
    if param['engine'] in jail_drivers:
        return jail_drivers[param['engine']](param)

    raise Exception("unknown jail type "+param['engine'])
