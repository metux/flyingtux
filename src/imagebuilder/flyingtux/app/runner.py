from metux.util.log import info
from ..container import get as container_get
from ..services import process_os_service
from toolbase import ToolBase
from os import environ
from os.path import basename
from metux.util.fs import mkdir

class ServiceContainer:
    def __init__(self, engine, name, image, network = None, bridge = None, ip = None):
        self.my_name = name
        self.my_bridge = bridge
        self.my_network = network
        self.my_ip = ip
        self.my_jail = container_get({
            'engine':       engine,
            'name':         name,
            'rootfs-image': image,
        })

    def reload(self):
        if self.my_jail.check_running():
            self.my_jail.signal('HUP')
        else:
            self.startup()

    def startup(self):
        if self.my_ip is not None:
            self.my_jail.add_ip(self.my_param['ip'])
        if self.my_network is not None:
            self.my_jail.add_network(self.my_param['network'])
        self.my_jail.destroy()
        self.my_jail.create()
        if self.my_bridge is not None:
            self.my_jail.join_network(self.my_param['bridge'])
        return self.my_jail.start()

class WebProxyContainer(ServiceContainer):
    def __init__(self, param):
        self.my_param = param
        ServiceContainer.__init__(self,
            engine  = param['jail-engine'],
            name    = param['name'],
            image   = param['image'],
            bridge  = param['bridge'],
            network = param['network'],
            ip      = param['ip'],
        )
        self.my_jail.add_bind_mount(param['conf-source'], param['conf-target'])

    def startup2(self):
        self.my_jail.add_ip(self.my_param['ip'])
        self.my_jail.add_network(self.my_param['network'])
        self.my_jail.destroy()
        self.my_jail.create()
        self.my_jail.join_network(self.my_param['bridge'])
        self.my_jail.start()

    def get_url(self):
        return "%s:%s" % (self.my_param['ip'], self.my_param['port'])

"""Runner is initialized with an deploy spec"""
class Runner(ToolBase):

    def mount_volume(self, vol):
        if 'tempdir' in vol:
            self.my_jail.add_tempdir(vol['tempdir'])
        elif 'datadir' in vol:
            if 'name' not in vol:
                raise Exception("data volume needs a name: "+vol['datadir'])
            d = self.get_data_vol_dir(vol['name'])
            mkdir(d)
            self.my_jail.add_bind_mount(d, vol['datadir'])
        elif 'cachedir' in vol:
            if 'name' not in vol:
                raise Exception("data volume needs a name: "+vol['cachedir'])
            d = self.get_cache_vol_dir(vol['name'])
            mkdir(d)
            self.my_jail.add_bind_mount(d, vol['cachedir'])
        elif 'nullfile' in vol:
            self.my_jail.add_bind_mount('/dev/null', vol['nullfile'])
        else:
            raise Exception("unknown volume type: "+str(vol))

    def get_data_vol_dir(self, volname):
        return self.my_app_volume_dir+'/'+basename(volname)

    def get_cache_vol_dir(self, volname):
        return self.my_app_cache_dir+'/'+basename(volname)

    def init_jail(self):
        self['ENV'] = environ
        self.my_jail = container_get({
            'engine':       self['engine'],
            'command':      self['command'],
            'rootfs-image': self['rootfs-image'],
            'tempdirs':     self['tmpdirs'],
        })
        self.my_app_volume_dir = self['APP-VOLUME-DIR']
        self.my_app_cache_dir  = self['APP-CACHE-DIR']
        self.my_target = self['TARGET']
        self.ip_address = self.my_target.get_app_ipaddr(self['image'])

        for v in self.get_cf_list('volumes'):
            self.mount_volume(v)

        for sname,sspec in self['os-services'].iteritems():
            self.my_jail.add_params(process_os_service(sname, sspec, self))

        self.my_jail.add_opts({
            'user': self['user'],
            'name': self['name'],
            'readonly': True,
        })

        self.my_jail.add_network(self.my_target['jail-network::name'])
        self.my_jail.add_ip(self.ip_address)

    def configure(self):
        self.init_jail()

    def run(self, args):
        print("runner args: "+str(args))
        self.init_jail()
        self.my_target.start_network()
        if self.my_jail.check_running():
            self.info("container already running")
        else:
            self.info("container not running yet")
            if not self.my_jail.check_rootfs():
                self.info("missing image: %s" % self['image'])
                self.my_target.get_builder(self['image']).run()
#            self.my_jail.run_detached()
            self.my_jail.run_foreground()

    def execute(self, args):
        self.init_jail()
        if not self.my_jail.check_running():
            self.run()
        return self.my_jail.execute(args)

    def start_web_proxy(self):
        t = self.my_target
        p = t['web-proxy']
        p.update({
            'jail-engine': t['jail-engine'],
            'network':     t['jail-network::name'],
            'bridge':      t['jail-network::bridge'],
        })
        self.my_web_proxy = WebProxyContainer(p)
        self.my_web_proxy.reload()
        return self.my_web_proxy.get_url()
