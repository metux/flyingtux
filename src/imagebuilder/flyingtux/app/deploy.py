from metux.util.log import info
from ..container import get as container_get
from ..services import process_os_service
from toolbase import ToolBase
from metux.util.fs import mkdir
from ..spec.deploy import DeploySpec
from os.path import isfile, dirname
import yaml

class Deploy(ToolBase):
    def __init__(self, spec):
        ToolBase.__init__(self, spec, 'Deploy')
        self.tempdirs = []
        self.default_set('APP_DEPLOY_DIR', '${TARGET::deploy-app-dir}/${IMAGE::NAME}')
        self.my_deploy_spec_file = self['TARGET::deploy-app-dir']+'/'+self['IMAGE::NAME']+'/info.yml'

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
# 2do:
# + check for image built
# + check for deployment descriptor -- load it or generate it
# + check for unmet permissions etc
        self.load_deploy()


    def load_deploy(self):
        dirname(self.my_deploy_spec_file)

        self.my_deploy_spec = DeploySpec({})
        if isfile(self.my_deploy_spec_file):
            self.info("already deployed: "+self.my_deploy_spec_file)
            self.my_deploy_spec.load_spec(deploy_app_yml)
        else:
            self.info("creating new deploy spec")
            self.my_deploy_spec['image'] = DeploySpec({})

        with open(self.my_deploy_spec_file, 'w') as outfile:
#            yaml.dump(self, outfile, default_flow_style=False, indent='    ')
            yaml.dump(self, outfile, indent=4)

        self.info("deploying "+self['IMAGE::NAME'])
        return 0
