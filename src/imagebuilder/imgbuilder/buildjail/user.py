from metux.util.fs import mkdir
import subprocess

class JailDriverUser:
    def __init__(self, param):
        self.my_param = param
        if 'sysroot-tempdir' not in param:
            raise Exception("missing sysroot-tempdir parameter")

    def img_prefixed(self, fn):
        return "%s/%s" % (self.get_sysroot(), fn)

    def img_create_dirs(self, dirs):
        for x in dirs:
            mkdir(self.img_prefixed(x))

    def img_write_file(self, fn, text):
        return open(self.img_prefixed(fn), 'w').write(text)

    def img_copy_file(self, src, dst):
        return self.img_write_file(dst, open(src,mode='r').read())

    def get_sysroot(self):
        return self.my_param['sysroot-tempdir']

    def call_cmd(self, args):
        stdout, stderr = subprocess.Popen(args).communicate()
        stdout, stderr
