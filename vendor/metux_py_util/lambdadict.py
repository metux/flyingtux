from inspect import isfunction
from collections import Mapping
from metux.util.log import info

class LambdaDictFilter:
    def filter_get_res(self, ld, key, val):
        return val

class LambdaDict(dict):
    def __init__(self, d = None, dflt = None, filter = None):
        self.filter = filter
        self.load_dict(d)
        if dflt is None:
            dflt = {}
        self.defaults = dict(dflt)

    def load_dict(self, d):
        if d is not None:
            for k,v in d.iteritems():
                if isinstance(v, Mapping):
                    dict.__setitem__(self, k, LambdaDict(v, None, self.filter))
                else:
                    dict.__setitem__(self, k, v)

    def __getitem_raw__(self, key):
        if dict.has_key(self, key):
            return dict.__getitem__(self, key)

        if key in self.defaults:
            return self.defaults[key]

        return None

    def __getitem__(self, key):
        if type(key)==tuple or type(key)==list:

            # fetch item from dict
            item = self.__getitem_raw__(key[0])

            # process potential callable
            if callable(item):
                item = item()

            # apply filter
            if self.filter is not None:
                item = self.filter.filter_get_res(self, key[0], item)

            # break out of end of keys or None
            if len(key) == 1 or item is None:
                return item

            # ask our child dict
            return item[key[1:]]

        return self.__getitem__(key.split('::'))

    def has_key(self, key):
        if dict.has_key(self, key):
            return True

        if (self.defaults.has_key(key)):
            return True

        return False

    def __mksub(self, key):
        if dict.has_key(self, key):
            sub = dict.__getitem__(self, key)
            if not isinstance(sub, Mapping):
                raise Exeption("attemted to add default for a sub-dict defined as scalar")
            return sub

        sub = LambdaDict(None, None, self.filter)
        dict.__setitem__(self, key, sub)
        return sub

    """set a default value, which is returned when key not found"""
    def default_set(self, key, value):
        if type(key)==tuple or type(key)==list:
            k0 = key[0]
            if len(key) == 1:
                self.defaults[k0] = value
            else:
                self.__mksub(k0).default_set(key[1:], value)
        else:
            self.default_set(key.split('::'), value)

    """remove a default value"""
    def default_del(self, key):
        self.defaults.pop(key, None)

    """add a list of default values"""
    def default_addlist(self, attrs):
        if attrs is not None:
            for key, value in attrs.iteritems():
                self.default_set(key, value)

    """add item to the dict (not default)"""
    def __setitem__(self, key, value):
        if type(key)==tuple or type(key)==list:

            if len(key) == 1: # final leaf
                dict.__setitem__(self, key[0], value)
                return

            if dict.has_key(self, key[0]):
                sub = dict.__getitem__(self, key[0])
                if not isinstance(sub, dict):
                    raise Exception("cant add elements to non-dict")
            else:
                sub = LambdaDict({}, None, self.filter)
                dict.__setitem__(self, key[0], sub)

            return sub.__setitem__(key[1:], val)

        return self.__setitem__(key.split('::'), value)
