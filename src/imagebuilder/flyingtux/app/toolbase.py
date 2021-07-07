from metux.util.specobject import SpecObject
from metux.util import log
from ..util import FT_UnsupportedTool

class ToolBase(SpecObject):
    def __init__(self, spec, name = None):
        SpecObject.__init__(self, spec)
        if name is None:
            self.my_toolname = self.__class__.__name__
        else:
            self.my_toolname = name

    def info(self, text):
        log.info(self.my_toolname+': '+text)

    def abort(self, text):
        raise FT_UnsupportedTool(self.my_toolname+': '+text)
