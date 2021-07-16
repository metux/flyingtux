from basespec import BaseSpec
from metux.util.specobject import SpecObject
from ..util import clean_path

class OSBaseSpec(BaseSpec):
    def get_component(self, name):
        return self['components::%s' % name]

    def get_repos(self):
        k = self['DATADIR']+'/keys/'
        return {
            'keys': [k+clean_path(x) for x in self.get_cf_list('repos::keys')],
            'urls': self.get_cf_list('repos::urls'),
        }
