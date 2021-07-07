from metux.util.specobject import SpecObject
from metux.util.lambdadict import LambdaDict
from spec import obj_types
from builder import Builder
from runner import Runner
from os import getcwd, environ

class Target(SpecObject):
    def load_spec(self, spec):
        SpecObject.load_spec(self, spec)
        self['ENV'] = LambdaDict(environ)

    def load_object(self, type, name, param = {}):
        datadir = self['configdir']+'/'+type+'/'+name
        cf = datadir+'/info.yml'
        obj = obj_types[type](param)
        obj.load_spec(cf)
        obj['DATADIR'] = datadir
        obj['CONFFILE'] = cf
        obj['NAME'] = name
        return obj

    def load_osbase(self, name):
        return self.load_object('osbase', name)

    def load_image(self, name):
        image = self.load_object('image', name)
        image['OSBASE'] = self.load_osbase(image['rootfs::osbase'])
        return image

    def inject_conf(self, obj):
        # overwrite instead of defaults in order to protect from malicious configs
        obj['ROOTFS-TARBALL'] = self['image-dir']+'/${IMAGE::NAME}-${IMAGE::version}.${ARCH}.tar.bz2'
        obj['DOCKER-IMAGE']   = 'flyingtux-${IMAGE::NAME}-${ARCH}:${IMAGE::version}'
        obj['BUILD-SYSROOT']  = self['sysroot-dir']+'/${IMAGE::NAME}-${IMAGE::version}'

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
            raise Exception("failed finding matching arch for platform and osbase")
        else:
            if arch not in platform_arch:
                raise Exception("requested arch %s not supported by platform" % arch)
            if arch not in osbase_arch:
                raise Exception("requested arch %s not supported by osbase" % arch)

            obj.info("forced arch: %s" % arch)
            obj.default_set('ARCH', arch)

    def get_builder(self, img_name):
        obj = Builder({
            'workdir':  getcwd()+'/tmp',
            'IMAGE':    self.load_image(img_name),
            'PLATFORM': self.load_object('platform', self['platform']),
            'TARGET':   self
        }, self)

        self.inject_conf(obj)
        self.compute_arch(obj)

        return obj

    def get_runner(self, img_name):
        obj = Runner({
            'workdir':  getcwd()+'/tmp',
            'IMAGE':    self.load_image(img_name),
            'PLATFORM': self.load_object('platform', self['platform']),
            'TARGET':   self
        })

        self.inject_conf(obj)
        self.compute_arch(obj)

        return obj

def get(conffile):
    obj = Target({})
    obj.load_spec(conffile)
    obj['CONFIG_FILE'] = conffile
    return obj
