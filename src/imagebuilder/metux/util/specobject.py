import yaml
from os import getuid, getcwd, getgid
from os.path import expanduser
from metux.util.log import info
from metux.util.lambdadict import LambdaDict
from string import Template
import re

class SubstTemplate(Template):
    idpattern = r"[_a-zA-Z][_a-zA-Z0-9/\.\-\:]*"
    match_re = re.compile(r'^\$\{([_a-zA-Z][_a-zA-Z0-9/\.\-\:]*)\}$')

class SpecError(Exception):

    def __init__(self, msg):
        self.msg = msg
        Exception.__init__(self, "[spec error] "+msg)

    def get_message(self):
        return self.msg

class SpecObject(object):

    """[private]"""
    def __init__(self, spec):
        self.set_spec(spec)

    """retrieve a config element by path"""
    def get_cf_raw(self, p, dflt = None):
        res = self._my_spec[p]
        if res is None:
            return dflt
        else:
            return res

    """retrieve a config element as list"""
    def get_cf_list(self, p, dflt = []):
        return self.get_cf(p, dflt)

    """retrieve a config element by path and substitute variables"""
    def get_cf(self, p, dflt = None):
        walk = self._my_spec
        for pwalk in p.split('::'):
            walk = self.cf_substvar(walk[pwalk])
            if walk is None:
                return dflt
        return walk

    """retrieve a config element as dict"""
    def get_cf_dict(self, p):
        r = self.get_cf(p)
        if p is None:
            return LambdaDict({})
        return r

    """retrieve a config element as bool"""
    def get_cf_bool(self, p, dflt = False):
        r = self.get_cf(p, dflt)
        if r is None:
            return dflt
        if r:
            return True
        return False

    """container get method"""
    def __getitem__(self, p):
        return self.get_cf(p)

    """container has_key method"""
    def has_key(self, p):
        return self._my_spec.has_key(p)

    """set spec object"""
    def set_spec(self, s):
        self._my_spec = LambdaDict(s)
        self.default_addlist({
            'user.uid':  lambda: str(getuid()),
            'user.gid':  lambda: str(getgid()),
            'user.home': lambda: expanduser('~'),
            'user.cwd':  lambda: getcwd(),
        })

    """get spec object"""
    def get_spec(self, s):
        return self._my_spec

    """def load spec from yaml"""
    def load_spec(self, fn):
        with open(fn) as f:
            # use safe_load instead load
            self.set_spec(yaml.safe_load(f))
            info("loaded config: "+fn)

    """add a default value, which will be used if key is not present"""
    def default_set(self, key, val):
        self._my_spec.default_set(key, val)

    """add a list of default values"""
    def default_addlist(self, attrs):
        self._my_spec.default_addlist(attrs)

    """[private] variable substitution"""
    def cf_substvar(self, var):
        if (var is None) or (isinstance(var,bool)) or (isinstance(var, (long, int))):
            return var

        if isinstance(var, basestring) or (isinstance(var, str)):
            if var.lower() in ['true', '1', 't', 'y', 'yes']:
                return True

            if var.lower() in ['false', '0', 'f', 'n', 'no']:
                return False

            res = SubstTemplate.match_re.match(var.strip())
            if res is not None:
                return self.get_cf(res.group(1))

            new = SubstTemplate(var).substitute(self._my_spec)
            if new == var:
                return var

            return self.cf_substvar(new)

        return var

    """create a proxy that accesses sub dicts with path prefix"""
    def get_subdict(self, prefix):
        return SpecObjectProxy(self, prefix)

"""[private]"""
class SpecObjectProxy(object):

    """[private]"""
    def __init__(self, parent, root):
        self.my_parent = parent
        self.my_root = root + '::'

    def __getitem__(self, p):
        p = self.my_root+p
        return self.my_parent.__getitem__(p)

    def has_key(self, p):
        return self.my_parent.has_key(self.my_root+p)