from base import BasePkg
from os.path import basename
import subprocess

class AlpinePkg(BasePkg):

    def __init__(self, param):
        BasePkg.__init__(self, param)
        self.my_repos_text = ''
        self.apk_cmd = 'apk'

    def prepare_image(self):
        print("preparig os image ...")
        print(self.get_sysroot())

        # initial dirs / files
        self.img_create_dirs(['etc/apk/cache',
                              'etc/apk/keys',
                              'var/log',
                              'lib/apk/db'])
        self.img_write_file('/etc/apk/arch', self.my_param['arch'])
        self.img_write_file('/etc/apk/world', '')

    def add_repos(self, repos):
        if repos is None:
            return False

        # fixme: add sanity checks for downloaded image specs
        for x in repos['urls']:
#            self.my_repos_text = self.my_repos_text + "@%s %s\n" % (x, repos['urls'][x])
            self.my_repos_text = self.my_repos_text + "%s\n" % repos['urls'][x]
        self.img_write_file('/etc/apk/repositories', self.my_repos_text)

        for x in repos['key-files']:
            self.img_copy_cf_file(x, '/etc/apk/keys/%s' % basename(x))

    def call(self, cmd, args):
        cmdline = [self.apk_cmd, cmd, '--root=%s' % self.get_sysroot()] + args
        stdout, stderr = subprocess.Popen(cmdline).communicate()
        stdout, stderr

    def add_packages(self, pkgs):
        return self.call('add', pkgs)
