from metux.util.specobject import SpecObject
from metux.util.lambdadict import LambdaDict
from metux.util import log
from spec import obj_types
from app import Builder, Deploy, Runner
from os import getcwd, environ
from os.path import expanduser

class Target(SpecObject):
    def post_init(self):
        self['ENV'] = LambdaDict(environ) # fixme: do we still need that explicit wrapping ?
        self.default_addlist({
            'USER::uid':  lambda: str(getuid()),
            'USER::gid':  lambda: str(getgid()),
            'USER::home': lambda: expanduser('~'),
            'USER::cwd':  lambda: getcwd(),
        })
        self._objcache = {}

    def load_object(self, type, name, param = {}):
        datadir = self['configdir']+'/'+type+'/'+name
        cf = datadir+'/info.yml'

        if cf in self._objcache:
            log.info("cached object: "+cf)
            return self._objcache[cf]

        obj = obj_types[type](param)
        obj.load_spec(cf)
        obj['DATADIR'] = datadir
        obj['NAME'] = name

        if type == 'image':
            obj['OSBASE'] = self.load_object('osbase', obj['rootfs::osbase'])

        self._objcache[cf] = obj
        return obj

    def compute_arch(self, obj):
        arch = obj['arch']
        platform_arch = obj['PLATFORM'].get_arch_list()
        osbase_arch = obj['IMAGE::OSBASE'].get_arch_list()

        if arch is None:
            for pf_arch in platform_arch:
                if pf_arch in osbase_arch:
                    obj.default_set('ARCH', pf_arch)
                    obj.info("auto-selected arch: %s" % pf_arch)
                    return
            raise FT_ConfigError("failed finding matching arch for platform and osbase")
        else:
            if arch not in platform_arch:
                raise FT_ConfigError("requested arch %s not supported by platform" % arch)
            if arch not in osbase_arch:
                raise FT_ConfigError("requested arch %s not supported by osbase" % arch)

            obj.info("forced arch: %s" % arch)
            obj.default_set('ARCH', arch)

    def get_tool(self, tool, img_name):
        obj = tool({
            'IMAGE':        self.load_object('image', img_name),
            'PLATFORM':     self.load_object('platform', self['platform']),
            'TARGET':       self,
            'ROOTFS-IMAGE': 'flyingtux-${IMAGE::NAME}-${ARCH}:${IMAGE::version}',
        })

        self.compute_arch(obj)

        return obj

    def get_builder(self, img_name):
        obj = self.get_tool(Builder, img_name)
        obj['BUILD-TEMP'] = self['build-temp']+'/${IMAGE::NAME}-${IMAGE::version}.${ARCH}'
        return obj

    def get_deploy(self, img_name):
        return self.get_tool(Deploy, img_name)

    def get_runner(self, img_name):
        obj = Runner({})
        obj.load_spec(self['deploy-app-dir']+'/'+img_name+'/info.yml')
        obj['TARGET'] = self
        obj['APP-BASE-DIR'] = self['app-base-dir']+'/'+img_name
        obj['APP-VOLUME-DIR'] = '${APP-BASE-DIR}/volumes'
        obj['APP-SERVICE-DIR'] = '${APP-BASE-DIR}/services'
        return obj

def get(conffile):
    obj = Target({})
    obj.load_spec(conffile)
    return obj
