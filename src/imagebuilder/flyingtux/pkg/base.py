from metux.util import log
from metux.util.fs import mkdir
from metux.util.specobject import SpecObject

class BasePkg(SpecObject):
    def __init__(self, param, jail):
        SpecObject.__init__(self, param)
        self.my_param = param
        self.jail = jail

    def img_create_dirs(self, dirs):
        return self.jail.img_create_dirs(dirs)

    def img_write_file(self, fn, text):
        return self.jail.img_write_file(fn, text)

    def img_copy_file(self, src, dst):
        return self.jail.img_copy_file(src, dst)

    def prepare(self):
        self.jail.prepare()

    def finish(self):
        self.jail.finish()
