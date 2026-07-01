import ipaddress
from metux.util import log
from os.path import normpath
import yaml

def clean_path(path):
    return normpath(path).replace('../', '')

class FT_Error(Exception):
    pass

class FT_ConfigError(FT_Error):
    pass

class FT_UnsupportedJail(FT_Error):
    pass

class FT_UnsupportedPkg(FT_Error):
    pass

class FT_UnsupportedTool(FT_Error):
    pass

class bimap(dict):
    def __init__(self, *args, **kwargs):
        super(bimap, self).__init__(*args, **kwargs)
        self.inverse = {}
        for key, value in self.items():
            self.inverse[value] = key

    def __delval(self, val):
        if val in self.inverse:
            oldkey = self.inverse[val]
            del self[oldkey]

    def __setitem__(self, key, value):
        del self[key]
        self.__delval(value)
        super(bimap, self).__setitem__(key, value)
        self.inverse[value] = key

    def __delitem__(self, key):
        if key in self:
            oldval = self[key]
            super(bimap, self).__delitem__(key)
            self.__delval(oldval)

    def update(self, d):
        for k,v in d.iteritems():
            self[k] = v

def load_bimap_yaml(fn):
    try:
        with open(fn) as f:
            return bimap(yaml.load(f))
    except Exception as e:
        pass
    return bimap()

def store_bimap_yaml(bd, fn):
    with open(fn, 'w') as outfile:
        yaml.dump(dict(bd), outfile, default_flow_style=False, indent=4)

class IpAddrMap:
    def __init__(self, fn, subnet, reserved = {}):
        self.my_ipmap_fn = fn
        self.my_subnet = subnet
        self.my_ipmap = load_bimap_yaml(self.my_ipmap_fn)
        self.my_ipmap.update(reserved)

    """fetch allocated ip or allocate a new one"""
    def get_ip(self, name):
        if name in self.my_ipmap:
            return self.my_ipmap[name]

        for ip in ipaddress.IPv4Network(unicode(self.my_subnet)):
            ips = str(ip)

            if ip.is_multicast or ip.is_reserved or ip.is_link_local:
                continue

            if ips in self.my_ipmap.inverse:
                continue

            self.my_ipmap[name] = ips
            store_bimap_yaml(self.my_ipmap, self.my_ipmap_fn)
            return ips

        raise Exception("failed to allocate a new ip address for: "+name)
