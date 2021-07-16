from metux.util.fs import mkdir
from metux.util import log
from metux.util.docker import Docker
from os.path import dirname
from metux.util.specobject import SpecObject

class JailDriverDocker(SpecObject):
    def __init__(self, param):
        SpecObject.__init__(self, param)

        self.default_addlist({
            'pkg-sysroot':    '/sysroot',
            'rootfs-tarball': '/sysroot.tar.bz2',
        })

        self.check_mandatory(['workdir',
                              'target-tarball',
                              'target-docker-image',
                              'rootfs-tarball',
                              'pkg-sysroot',
                              'build-image',
                              'build-init'])

        self.my_docker = Docker()

    def sysroot_fn(self, fn):
        return "%s/%s" % (self['pkg-sysroot'], fn)

    def temp_fn(self, fn):
        return "%s/%s" % (self['workdir'], fn)

    def img_create_dirs(self, dirs):
        self.my_container.mkdirs([self.sysroot_fn(x) for x in dirs])
        for x in dirs:
            mkdir(self.temp_fn(x))

    def img_write_file(self, fn, text):
        local = self.temp_fn(fn)
        remote = self.sysroot_fn(fn)
        open(local, 'w').write(text)
        self.my_container.cp_to(local, remote)
        self.my_container.chown('root:root', [remote])

    def img_copy_file(self, src, dst):
        self.my_container.cp_to(src, self.sysroot_fn(dst))

    def img_remove_recursive(self, dirs):
        return self.my_container.rm_recursive([self.sysroot_fn(x) for x in dirs])

    def img_remove_dirs(self, dirs):
        self.my_container.exec_catch(
            ['find'] +
            [self.sysroot_fn(x) for x in dirs] +
            ['-type', 'd', '-empty', '-exec', 'rmdir', '-p', '{}', ';'])

    def call_cmd(self, args):
        return self.my_container.execute(args)

    def prepare(self):
        self.my_container = self.my_docker.container_create(self['build-image'], [self['build-init']])
        self.my_container.start()

    def do_compress(self):
        self.my_container.execute(['tar', '-cjf', self['rootfs-tarball'], '-C', self['pkg-sysroot'], '.'])
        mkdir(dirname(self['target-tarball']))
        self.my_container.cp_from(self['rootfs-tarball'], self['target-tarball'])

    def finish(self):
        self.do_compress()
        self.my_container.destroy()
        self.my_docker.image_import(self['target-tarball'], self['target-docker-image'])
