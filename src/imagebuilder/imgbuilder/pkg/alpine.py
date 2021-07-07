from base import BasePkg
from os.path import basename
import subprocess
from metux.util import log

class AlpinePkg(BasePkg):
    def __init__(self, param, jail):
        BasePkg.__init__(self, param, jail)
        self.my_repos_text = ''
        self.apk_cmd = 'apk'
        self.check_mandatory(['arch'])

    """[private] call the package manager"""
    def __call(self, cmd, args):
        self.jail.call_cmd([self.apk_cmd, cmd, ('--root=%s' % self.jail['pkg-sysroot'])] + args)
        return True

    """prepare the sysroot image"""
    def prepare(self):
        BasePkg.prepare(self)
        self.img_create_dirs(['etc/apk/cache',
                              'etc/apk/keys',
                              'var/log',
                              'lib/apk/db'])
        self.img_write_file('/etc/apk/arch', self['arch'])
        self.img_write_file('/etc/apk/world', '')

    """add repositories"""
    def add_repos(self, repos):
        if repos is None:
            return False

        # fixme: add sanity checks for downloaded image specs
        for x in repos['urls']:
            self.my_repos_text = self.my_repos_text + "%s\n" % x
        self.img_write_file('/etc/apk/repositories', self.my_repos_text)

        for x in repos['keys']:
            self.img_copy_file(x, '/etc/apk/keys/%s' % basename(x))

    """add/install packages"""
    def add_packages(self, pkgs):
        return self.__call('add', pkgs)

    def finish(self):
        return BasePkg.finish(self)
