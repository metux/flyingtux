from ..services import process_os_service, get_os_service
from ..spec.deploy import DeploySpec, DeploySpec_representer
from ..naming import app_container_name
from metux.util.fs import mkdir
from os.path import isfile, dirname
from os import chmod
from toolbase import ToolBase
import yaml

class Deploy(ToolBase):

    def post_init(self):
        self.my_deploy_spec_file = self['TARGET::deploy-app-dir']+'/'+self['IMAGE::NAME']+'/info.yml'

    def run(self):
        self.create_deploy()
        self.create_script()

    def create_script(self):
        scriptdir = self['TARGET::workdir']+'/bin'
        name      = self['IMAGE::NAME']
        codebase  = self['TARGET::CODEBASE']
        scriptname = scriptdir+'/'+name
        mkdir(scriptdir)

        with open(scriptname, "w") as f:
            f.write('#!/usr/bin/python\n')
            f.write('import sys\n')
            f.write('sys.path.append("'+codebase+'")\n')
            f.write('from flyingtux.cmd import run_app\n')
            f.write('run_app()\n')
        chmod(scriptname, 0755)

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
        d['name']          = app_container_name(appname=image['NAME'],
                                                version=image['version'])
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
        d['volumes']       = image['volumes']

        for sname,sspec in image['os-services'].iteritems():
            d['os-services::'+sname] = get_os_service(sname, sspec, self).get_conf()

        with open(self.my_deploy_spec_file, 'w') as outfile:
            yaml.dump(self.my_deploy_spec, outfile, default_flow_style=False, indent=4)

        return 0
