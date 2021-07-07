from metux.util.specobject import SpecObject
from metux.util import log
from os import getcwd
import spec
import pkg

class Builder(SpecObject):
    def __init__(self, spec):
        SpecObject.__init__(self, spec)

        self.default_addlist({
            'confdir': getcwd()+"/cf"
        })

        self.my_platform = self.loadobj('platform', spec['platform'])
        self.my_image    = self.loadobj('image',    spec['image'])
        self.my_osbase   = self.loadobj('osbase',   self.my_image['osbase'])

        for a in [self.my_platform, self.my_image, self.my_osbase]:
            a.default_set('PLATFORM', self.my_platform)
            a.default_set('IMAGE', self.my_image)
            a.default_set('OSBASE', self.my_osbase)

        self.compute_arch()

        self.my_pkg = pkg.get(self.my_osbase['engine'], {
            'sysroot': self['workdir']+"/images/"+self.my_image['NAME'],
            'osbase':  self.my_osbase,
            'arch':    self['ARCH'],
            'confdir': self['confdir']
        })

    def loadobj(self, type, name):
        obj = spec.loadobj(self['confdir'], type, name)
        obj.default_set('BUILDER', self)
        self.default_set(type.upper(), obj)
        return obj

    """check whether selected arch is supported"""
    def compute_arch(self):
        arch = self['arch']
        if arch is None:
            for pf_arch in self.my_platform.get_arch_list():
                if self.my_osbase.have_arch(pf_arch):
                    self.default_set('ARCH', pf_arch)
                    log.info("Builder: auto-selected arch: %s" % pf_arch)
                    return
            raise Exception("failed finding matching arch for platform and osbase")
        else:
            if not self.my_platform.have_arch(arch):
                raise Exception("requested arch %s not supported by platform" % arch)
            if not self.my_osbase.have_arch(arch):
                raise Exception("requested arch %s not supported by osbase" % arch)

            log.info("Builder: forced arch: %s" % arch)
            self.default_set('ARCH', arch)

    def do_single_os_component(self, name, component):
        selector = component['selector']
        ch = component['choice::'+selector]
        if ch is None:
            log.info("osbase component %s: cant find selector %s - using default" % (name, selector))
            ch = component['default']

        if ch is None:
            log.info("osbase component %s has no default behaviour" % name)
            return False

        pkg = ch['packages']
        if pkg is not None:
            log.info("osbase component %s: installing packages" % name)
            self.my_pkg.add_packages(pkg)

    def do_os_components(self):
        for name in self.my_image['os-components']:
            comp = self.my_osbase.get_component(name)
            if comp is None:
                raise Exception("missing os component %s needed by image" % name)
            self.do_single_os_component(name, comp)

    def run(self):
        self.my_pkg.prepare_image()
        self.my_pkg.add_repos(self.my_osbase['repos'])
        self.my_pkg.add_repos(self.my_image['repos'])
        self.do_os_components()

def get(param = None):
    return Builder(param)
