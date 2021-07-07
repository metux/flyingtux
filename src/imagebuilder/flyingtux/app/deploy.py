from ..services import process_os_service, get_os_service
from ..spec.deploy import DeploySpec, DeploySpec_representer
from metux.util.fs import mkdir
from os.path import isfile, dirname
from toolbase import ToolBase
import yaml

class Deploy(ToolBase):

    def post_init(self):
        self.my_deploy_spec_file = self['TARGET::deploy-app-dir']+'/'+self['IMAGE::NAME']+'/info.yml'

    def run(self):
        self.create_deploy()

    def create_deploy(self):
        image = self['IMAGE']
        self.info("deploying "+image['NAME'])
        mkdir(dirname(self.my_deploy_spec_file))

        # FIXME: autogenerate missing image on (re)deploy
        # FIXME: support transparent redeploy (eg. platform/arch changes)

        self.my_deploy_spec = DeploySpec({})
        d = self.my_deploy_spec
        if isfile(self.my_deploy_spec_file):
            self.info("already deployed: "+self.my_deploy_spec_file)
            self.my_deploy_spec.load_spec(self.my_deploy_spec_file)
        else:
            self.info("creating new deployment: "+self.my_deploy_spec_file)

        # write / update deployment descriptor
        d['image']         = image['NAME']
        d['name']          = 'flyingtux-app-'+image['NAME']+'_'+image['version']
        d['version']       = image['version']
        d['os-services']   = image['os-services']
        d['arch']          = self['ARCH']
        d['platform']      = self['PLATFORM::NAME']
        d['engine']        = self['TARGET::jail-engine']
        d['command']       = image['command']
        d['rootfs-image']  = self['ROOTFS-IMAGE']
        d['tmpdirs']       = (image.get_cf_list('rootfs::tmpdirs')
                            + image.get_cf_list('IMAGE::OSBASE::tmpdirs'))
        d['user']          = image['user']

        for sname,sspec in image['os-services'].iteritems():
            d['os-services::'+sname] = get_os_service(sname, sspec, self).get_conf()

        with open(self.my_deploy_spec_file, 'w') as outfile:
            yaml.dump(self.my_deploy_spec, outfile, default_flow_style=False, indent=4)

        return 0
