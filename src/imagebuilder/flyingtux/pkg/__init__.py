from alpine import AlpinePkg

drivers = {
    'apk': AlpinePkg
}

def get(drv, param, jail):
    if drv in drivers:
        return drivers[drv](param, jail)
    raise(Exception("unsupported pkg driver: %s" % drv))
