from metux.util.log import info
from ..pkg import get as pkg_get
from ..buildjail import get as buildjail_get
from toolbase import ToolBase
from shutil import rmtree

class Builder(ToolBase):

    """[private]"""
    def __do_single_os_component(self, name, component):
        self.__do_os_components(component['depends'])

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
    def __do_os_components(self, components):
        if components is None:
            return

        for name in components:
            component = self['IMAGE::OSBASE'].get_component(name)
            self.info("processing component: "+name)
            if component is None:
                self.abort("missing os component %s needed by image" % name)
            self.__do_single_os_component(name, component)

    def post_init(self):
        self['BUILD-TEMP'] = '${TARGET::build-temp}/${IMAGE::NAME}-${IMAGE::version}.${ARCH}'

    def run(self):

        platform = self['PLATFORM']
        image    = self['IMAGE']
        osbase   = image['OSBASE']

        # need to make a few object fixups
        image['PLATFORM']  = platform
        osbase['PLATFORM'] = platform

        self.info("initializing build jail")

        build_temp = self['BUILD-TEMP']
        try:
            rmtree(build_temp)
        except:
            pass

        jail_engine = self['TARGET::jail-engine']
        self.my_jail = buildjail_get({
            'rootfs-image': self['ROOTFS-IMAGE'],
            'workdir':      build_temp,
            'engine':       jail_engine,
            'conf':         osbase['build-jail::'+jail_engine],
        })

        self.my_pkg = pkg_get(osbase['engine'], { 'arch': self['ARCH'], }, self.my_jail)

        self.info("preparing image")
        self.my_pkg.prepare()

        self.info("adding repos")
        self.my_pkg.add_repos(image.get_repos())

        self.info("copying base files")
        for ent in osbase['rootfs::copy-files']:
            self.my_jail.sysroot_copy_file(ent['source'], ent['dest'], mode=ent['mode'], owner=ent['owner'])

        self.my_jail.sysroot_create_dirs(
            osbase.get_cf_list('rootfs::create-dirs') +
            image.get_cf_list('rootfs::create-dirs'))

        for ent in image.get_cf_list('rootfs::create-links'):
            self.my_jail.sysroot_symlink(name=ent['name'], target=ent['target'])

        self.info("adding os components")
        self.__do_os_components(image['rootfs::os-components'])

        self.info("installing application packages")
        self.my_pkg.add_packages(image['rootfs::packages'])

        self.info("cleaning up")
        self.my_jail.sysroot_remove_recursive(image.get_purged_files())
        self.my_jail.sysroot_remove_dirs(image.get_empty_dirs())

        self.info("finishing image")
        self.my_pkg.finish()

        self.info("cleaning working directory: "+self['BUILD-TEMP'])
        rmtree(build_temp)

        self.info("image build done")
        return 0
