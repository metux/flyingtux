from alpine import AlpinePkg
from ..util import FT_UnsupportedPkg

drivers = {
    'apk': AlpinePkg
}

def get(drv, param, jail):
    if drv in drivers:
        return drivers[drv](param, jail)
    raise FT_UnsupportedPkg("unsupported pkg driver: %s" % drv)
