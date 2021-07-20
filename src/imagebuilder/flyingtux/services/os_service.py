from metux.util.specobject import SpecObject
from metux.util.log import info

class Base(SpecObject):
    def __init__(self, spec, runner):
        SpecObject.__init__(self, spec)
        self.my_runner = runner

    def process(self):
        raise Exeption("not implemented")

class X11(Base):
    def process(self):
        display = self.my_runner['TARGET::ENV::DISPLAY']
        info("x11 display: "+str(display))
        return {
            'env' :   { 'DISPLAY': display },
            'mounts': [
                { 'type': 'bind', 'source': '/tmp/.X11-unix', 'target': '/tmp/.X11-unix' }
            ]
        }

class TempHomedir(Base):
    def process(self):
        return {
            'tempdirs': [ '/root', '/home/app' ]
        }
