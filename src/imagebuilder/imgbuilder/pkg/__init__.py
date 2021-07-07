from alpine import AlpinePkg

drivers = {
    'apk': AlpinePkg
}

def get(drv, param):
    if drv in drivers:
        return drivers[drv](param)
    raise(Exception("unsupported pkg driver: %s" % drv))
