from base import BasePkg
from os.path import basename
import subprocess
from metux.util import log

class AlpinePkg(BasePkg):

    sysroot_init_dirs = ['etc/apk/cache',
                         'etc/apk/keys',
                         'var/log',
                         'lib/apk/db']
    apk_cmd = 'apk'

    def __init__(self, param, jail):
        BasePkg.__init__(self, param, jail)
        self.my_repos_text = ''
        self.check_mandatory(['arch'])

    """[private] call the package manager"""
    def __call(self, cmd, args):
        return self.jail.call_cmd([self.apk_cmd, cmd, '--root='+self.jail.sysroot_fn('')] + args)

    """prepare the sysroot image"""
    def prepare(self):
        BasePkg.prepare(self)
        self.jail.sysroot_write_file('/etc/apk/arch', self['arch'])
        self.jail.sysroot_write_file('/etc/apk/world', '')

    """add repositories"""
    def add_repos(self, repos):
        if repos is None:
            return False

        # fixme: add sanity checks for downloaded image specs
        for x in repos['urls']:
            self.my_repos_text = self.my_repos_text + "%s\n" % x
        self.jail.sysroot_write_file('/etc/apk/repositories', self.my_repos_text)

        for x in repos['keys']:
            self.jail.sysroot_copy_file(x, '/etc/apk/keys/%s' % basename(x))

    """add/install packages"""
    def add_packages(self, pkgs):
        return self.__call('add', pkgs)

    def finish(self):
        return BasePkg.finish(self)
