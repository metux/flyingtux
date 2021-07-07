from metux.util.specobject import SpecObject

class BasePkg(SpecObject):
    sysroot_init_dirs = []

    def __init__(self, param, jail):
        SpecObject.__init__(self, param)
        self.my_param = param
        self.jail = jail

    def prepare(self):
        self.jail.prepare()
        self.jail.sysroot_create_dirs(self.sysroot_init_dirs)

    def finish(self):
        self.jail.finish()
