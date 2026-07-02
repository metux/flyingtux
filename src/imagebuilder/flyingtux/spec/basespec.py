# SPDX-License-Identifier: AGPL-3.0-or-later
from metux.util.specobject import SpecObject

class BaseSpec(SpecObject):
    def have_arch(self, arch):
        for a in self['arch']:
            if a == arch:
                return True
        return False

    def get_arch_list(self):
        return self['arch']
