from metux.util import log
from metux.util.fs import mkdir

class BasePkg:
    def __init__(self, param):
        self.my_param = param

        for x in ['sysroot', 'osbase', 'arch', 'confdir']:
            if x not in param:
                raise Exception("missing %s param" % x)

    def img_prefixed(self, fn):
        return "%s/%s" % (self.get_sysroot(), fn)

    def img_create_dirs(self, dirs):
        for x in dirs:
            mkdir(self.img_prefixed(x))

    def img_write_file(self, fn, text):
        open(self.img_prefixed(fn), 'w').write(text)

    def img_copy_file(self, src, dst):
        return self.img_write_file(dst, open(src,mode='r').read())

    def img_copy_cf_file(self, src, dst):
        return self.img_copy_file('%s/%s' % (self.my_param['confdir'], src), dst)

    def get_sysroot(self):
        return self.my_param['sysroot']
