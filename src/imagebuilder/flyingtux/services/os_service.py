from metux.util.specobject import SpecObject
from metux.util.log import info
from metux.util.fs import mkdir
from os import environ
from os.path import basename

"""
Notes:

* compute() is only called if at least one of the permissions is granted
  also for automatically applying statically given attributes
* should use decorators for registering services
"""
class Base(SpecObject):

    permissions = {
        '__enabled__': { 'default': True },
    }
    temp_dirs = []
    settings = {}

    def __init__(self, spec, runner):
        SpecObject.__init__(self, spec)
        self.my_runner = runner
        self.my_srv_env = {}
        self.my_srv_mounts = []
        self.my_tempdirs = []
        self.my_opts = {}
        self.my_devices = []
        self.default_set('TARGET', self.my_runner)
        self.default_set('ENV', environ)

    def compute(self):
        pass

    def get_app_name(self):
        return self.my_runner['image']

    def process(self):
        self.add_tempdirs(self.temp_dirs)
        if self.is_permitted('__enabled__'):
            self.info("enabled")
            self.compute()
        else:
            self.info("disabled")
        return {
            'mounts':   self.my_srv_mounts,
            'env':      self.my_srv_env,
            'tempdirs': self.my_tempdirs,
            'opts':     self.my_opts,
            'devices':  self.my_devices,
        }

    def bind_file_direct(self, fn):
        self.my_srv_mounts.append({ 'type': 'bind', 'source': fn, 'target': fn })

    def bind_dir(self, source, target):
        self.my_srv_mounts.append({
             'type':    'bind',
             'source':  source,
             'target':  target,
        })

    def bind_user_dir(self, src, dst):
        """2DO: honour xdg settings on host side"""
        self.my_srv_mounts.append({
             'type':    'bind',
             'source':  environ['HOME']+'/'+src,
             'target':  '/home/app/'+dst
        })

    def is_permitted(self, perm_name):
        if perm_name in self['permissions']:
            return self['permissions'][perm_name]
        return self.permissions[perm_name]['default']

    def add_env(self, name, val):
        self.my_srv_env[name] = val

    def add_tempdirs(self, dirs):
        self.my_tempdirs.extend(dirs)

    def add_device(self, name):
        self.my_devices.append(name)

    def set_container_opt(self, opt, val):
        self.my_opts[opt] = val

    def info(self, msg):
        info("os-service %s: %s" % (self.__class__.__name__, msg))

    def prepare_conf(self):
        pass

    def get_conf(self):
        self.prepare_conf()

        for perm_name, perm_def in self.permissions.iteritems():
            keyname = 'permissions::'+perm_name
            if self[keyname] is None:
                self[keyname] = perm_def['default']

        for sname, sval in self.settings.iteritems():
            keyname = 'settings::'+sname
            if self[keyname] is None:
                self[keyname] = sval['default']

        self['initialized'] = True
        return dict(self.get_spec())

    def get_setting(self, name):      return self['settings::'+name]
    def get_path_setting(self, name): return self.get_setting(name)
    def get_app_volume_dir(self):     return self.my_runner['APP-VOLUME-DIR']
    def get_app_service_dir(self):    return self.my_runner['APP-SERVICE-DIR']

"""
Give the container a temporary writable home directory
This is generally safe to have, most apps will want it,
and really doesn't need to be user-configurable at all.
"""
class TempHomedir(Base):
    temp_dirs = [ '/root', '/home/app', '/tmp' ]

class SysTempDir(Base):
    temp_dirs = ['/tmp', '/var/tmp']

class ServiceDir(Base):
    def compute(self):
        self.bind_dir(self.get_app_service_dir()+'/import/', '/service/import')
        self.bind_dir(self.get_app_service_dir()+'/export/', '/service/export')

class DataVolume(Base):
    def compute(self):
        datadir = self.get_app_volume_dir()
        for v in self.get_cf_list('volumes'):
            volume_dir = datadir+'/'+basename(v['name'])
            mkdir(volume_dir)
            self.bind_dir(volume_dir, v['mountpoint'])
