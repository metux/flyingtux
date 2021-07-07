from metux.util.log import info
from ..container import get as container_get
from ..services import process_os_service
from toolbase import ToolBase
from os import environ

"""Runner is initialized with an deploy spec"""
class Runner(ToolBase):

    def run(self):
        self['ENV'] = environ
        self.my_jail = container_get({
            'engine':       self['engine'],
            'command':      self['command'],
            'rootfs-image': self['rootfs-image'],
            'tempdirs':     self['tmpdirs'],
        })

        if not self.my_jail.check_rootfs():
            self.info("missing image: %s" % self['image'])
            self['TARGET'].get_builder(self['image']).run()

        for sname,sspec in self['os-services'].iteritems():
            self.my_jail.add_params(process_os_service(sname, sspec, self))

        self.my_jail.add_opts({
            'user': self['user'],
            'name': self['name'],
        })

        return self.my_jail.run()
