from metux.util.specobject import SpecObject
from metux.util.log import info
import container
from services import process_os_service
from os import environ

class Runner(SpecObject):
    def __init__(self, spec):
        SpecObject.__init__(self, spec)
        self.my_toolname = 'Runner'
        self.tempdirs = []

    def add_params(self, p, jail):
        if 'mounts' in p:
            jail.add_mounts(p['mounts'])
        if 'env' in p:
            jail.add_env(p['env'])
        if 'tempdirs' in p:
            jail.add_tempdirs(p['tempdirs'])

    def run(self):
        jail = container.get({
            'engine':  self['TARGET::runtime-jail::engine'],
            'command': self['IMAGE::command'],
            'tarball': self['ROOTFS-TARBALL'],
            'image':   self['DOCKER-IMAGE'],
        })

        platform = self['PLATFORM']
        for sname,sspec in self['IMAGE::os-services'].iteritems():
            self.add_params(process_os_service(sname, sspec, self), jail)

        jail.add_tempdirs(self['IMAGE::rootfs::tmpdirs'])
        jail.add_tempdirs(self['IMAGE::OSBASE::tmpdirs'])
        jail.run()

        return 0

    def info(self, text):
        info("Runner: %s" % text)
