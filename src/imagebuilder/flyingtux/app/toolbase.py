from metux.util.specobject import SpecObject
from metux.util import log

class ToolBase(SpecObject):
    def __init__(self, spec, name):
        SpecObject.__init__(self, spec)
        self.my_toolname = name

    def info(self, text):
        log.info(self.my_toolname+': '+text)

    def abort(self, text):
        raise Exception(self.my_toolname+': '+text)
