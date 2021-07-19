from metux.util.specobject import SpecObject
from metux.util.log import info
from ..pkg import get as pkg_get
from ..buildjail import get as buildjail_get
from toolbase import ToolBase

# 2do: * fetch arch from target
#      * check what else can be fetched from target
class Builder(ToolBase):
    def __init__(self, spec):
        ToolBase.__init__(self, spec, 'Builder')

    """[private]"""
    def __do_single_os_component(self, name, component):
        pkg = component['packages']
        if pkg is not None:
            self.info("osbase component %s: installing packages: %s" % (name,str(pkg)))
            self.my_pkg.add_packages(pkg)

        selector = component['selector']
        if selector is not None:
            choice = component['choice::'+selector]
            if choice is None:
                self.info("osbase component %s: cant find choice %s - using default" % (name, selector))
                choice = component['default']

            if choice is not None:
                pkg = choice['packages']
                if pkg is not None:
                    self.info("osbase component %s choice: installing packages: %s" % (name,str(pkg)))
                    self.my_pkg.add_packages(pkg)
            else:
                self.info("osbase component %s has no default choice" % name)

    """[private]"""
    def __do_os_components(self):
        for name in self.get_cf_list('IMAGE::rootfs::os-components'):
            component = self['IMAGE::OSBASE'].get_component(name)
            self.info("processing component: "+name)
            if component is None:
                self.abort("missing os component %s needed by image" % name)
            self.__do_single_os_component(name, component)

    def init_jail(self):
        # fixme: can't use default_set(), since lambdadict defaults aren't
        # automatically imported when creating SpecObject from a lambdadict
        jailconf = self['IMAGE::OSBASE::build-jail']
        jailconf['target-docker-image'] = self['DOCKER-IMAGE']
        jailconf['target-tarball']      = self['ROOTFS-TARBALL']
        jailconf['workdir']             = self['BUILD-SYSROOT']

        self.my_jail = buildjail_get(jailconf)

    def init_pkg(self):
        self.my_pkg = pkg_get(
            self['IMAGE::OSBASE::engine'],
            {
                'arch':    self['ARCH'],
            },
            self.my_jail
        )

    def build_image(self):

        self.init_jail()
        self.init_pkg()

        self.info("preparing image")
        self.my_pkg.prepare()

        self.info("adding repos")
        self.my_pkg.add_repos(self['IMAGE'].get_repos())

        self.info("adding os components")
        self.__do_os_components()

        self.info("installing application packages")
        self.my_pkg.add_packages(self['IMAGE::rootfs::packages'])

        self.info("cleaning up")
        self.my_jail.img_remove_recursive(self['IMAGE'].get_purged_files())
        self.my_jail.img_remove_dirs(self['IMAGE'].get_empty_dirs())

        self.info("finishing image")
        self.my_pkg.finish()

        self.info("image build done")
        return 0

    def run(self):
        return self.build_image()
