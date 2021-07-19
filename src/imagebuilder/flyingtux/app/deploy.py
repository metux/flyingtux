from metux.util.log import info
from ..container import get as container_get
from ..services import process_os_service
from toolbase import ToolBase

class Deploy(ToolBase):
    def __init__(self, spec):
        ToolBase.__init__(self, spec, 'Deploy')
        self.tempdirs = []

    def add_params(self, p, jail):
        if 'mounts' in p:
            jail.add_mounts(p['mounts'])
        if 'env' in p:
            jail.add_env(p['env'])
        if 'tempdirs' in p:
            jail.add_tempdirs(p['tempdirs'])

    def run(self):
#        jail = container_get({
#            'engine':  self['TARGET::runtime-jail::engine'],
#            'command': self['IMAGE::command'],
#            'tarball': self['ROOTFS-TARBALL'],
#            'image':   self['DOCKER-IMAGE'],
#        })
#
#        platform = self['PLATFORM']
#        for sname,sspec in self['IMAGE::os-services'].iteritems():
#            self.add_params(process_os_service(sname, sspec, self), jail)
#
#        jail.add_tempdirs(self['IMAGE::rootfs::tmpdirs'])
#        jail.add_tempdirs(self['IMAGE::OSBASE::tmpdirs'])
#        jail.run()
#
        info("application: "+text)
        return 0
