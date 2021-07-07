import user, docker
from ..util import FT_UnsupportedJail

jail_drivers = {
    'docker': docker.BuildJailDriverDocker
}

def get(param):
    if param['engine'] in jail_drivers:
        return jail_drivers[param['engine']](param)

    raise FT_UnsupportedJail("unknown build jail type "+str(param['engine']))
