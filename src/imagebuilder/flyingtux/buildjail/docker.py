from metux.util import log, fs
from metux.util.docker import Docker
from metux.util.specobject import SpecObject
from os.path import dirname
from os import remove, rmdir

class BuildJailDriverDocker(SpecObject):

    rootfs_tarball = '/sysroot.tar.bz2'
    build_sysroot  = '/sysroot'
    spec_mandatory = [ 'workdir', 'rootfs-image', 'conf' ]

    def post_init(self):
        self.check_mandatory(self.spec_mandatory)
        self.my_docker = Docker()

    def __temp_fn(self, fn):
        return "%s/sysroot/%s" % (self['workdir'], fn)

    def sysroot_fn(self, fn):
        return "%s/%s" % (self.build_sysroot, fn)

    def sysroot_create_dirs(self, dirs):
        self.my_container.mkdirs([self.sysroot_fn(x) for x in dirs])
        for x in dirs:
            fs.mkdir(self.__temp_fn(x))

    def sysroot_write_file(self, fn, text):
        local = self.__temp_fn(fn)
        remote = self.sysroot_fn(fn)
        open(local, 'w').write(text)
        self.my_container.cp_to(local, remote)
        self.my_container.chown('root:root', [remote])

    def sysroot_copy_file(self, src, dst, mode=None, owner=None):
        self.my_container.cp_to(src, self.sysroot_fn(dst), mode=mode, owner=owner)

    def sysroot_remove_recursive(self, dirs):
        return self.my_container.rm_recursive([self.sysroot_fn(x) for x in dirs])

    def sysroot_remove_dirs(self, dirs):
        return self.my_container.exec_catch(
            ['find'] +
            [self.sysroot_fn(x) for x in dirs] +
            ['-type', 'd', '-empty', '-exec', 'rmdir', '-p', '{}', ';'])

    def sysroot_symlink(self, name, target):
        self.sysroot_create_dirs([dirname(name), dirname(target)])
        self.my_container.execute(['ln', '-s', target, self.sysroot_fn(name)])

    def call_cmd(self, args):
        return self.my_container.execute(args)

    def prepare(self):
        self.my_container = self.my_docker.container_create(self['conf::image'], [self['conf::init']])
        self.my_container.start()

    def finish(self):
        target_tarball = self['workdir']+'/rootfs-temp.tar.bz2'
        target_dir     = dirname(target_tarball)

        self.my_container.execute(['tar','-cf', self.rootfs_tarball, '-C', self.build_sysroot, '.'])
        fs.mkdir(target_dir)
        self.my_container.cp_from(self.rootfs_tarball, target_tarball)
        self.my_container.destroy()
        self.my_docker.image_import(target_tarball, self['rootfs-image'])
