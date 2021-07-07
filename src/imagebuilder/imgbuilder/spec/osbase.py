from basespec import BaseSpec
from metux.util.specobject import SpecObject

class OSBaseSpec(BaseSpec):

    def get_component(self, name):
        return self.get_subdict('components::%s' % name)
