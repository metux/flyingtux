from metux.util import log
from metux.util.docker import Docker
from os.path import dirname
from metux.util.specobject import SpecObject

class ContainerDriverDocker(SpecObject):

    spec_mandatory = ['rootfs-image', 'command']

    def __init__(self, param):
        SpecObject.__init__(self, param)
        self.my_params = []
        self.my_docker = Docker()
        self.my_env = {}
        self.my_jail = None
        if 'name' in param:
            self.my_container_name = param['name']
        else:
            self.my_container_name = None
        self.add_params(param)

    def add_params(self, p):
        self.add_mounts(p.get('mounts'))
        self.add_env(p.get('env'))
        self.add_tempdirs(p.get('tempdirs'))
        self.add_opts(p.get('opts'))
        self.add_devices(p.get('devices'))

    def add_mount(self, m):
        if m is not None:
            if m['type'] == 'bind':
                self.add_bind_mount(m['source'], m['target'])
            else:
                raise FT_ConfigError("unsupported mount type: "+m['type'])

    def add_bind_mount(self, source, target):
        self.my_params.append('-v')
        self.my_params.append(source+':'+target)

    def add_mounts(self, mounts):
        if mounts is not None:
            for m in mounts:
                self.add_mount(m)

    def add_tempdir(self, t):
        if t is not None:
            self.my_params.append('--mount')
            self.my_params.append('type=tmpfs,destination=%s' % t)

    def add_tempdirs(self, dirs):
        if dirs is not None:
            for t in dirs:
                self.add_tempdir(t)

    def add_env(self, env):
        if env is not None:
            self.my_env.update(env)

    def add_opts(self, opts):
        if opts is not None:
            for o,v in opts.iteritems():
                if o == 'ipc':
                    self.my_params.append('--ipc')
                    self.my_params.append(v)
                elif o == 'user':
                    self.my_params.append('--user')
                    self.my_params.append(v)
                elif o == 'name' and v is not None:
                    self.my_container_name = v
                elif o == 'readonly':
                    if v:
                        self.my_params.append('--read-only')
                else:
                    raise FT_ConfigError("container opt %s (%s) not understood" % (o,v))

    def add_devices(self, devs):
        if devs is not None:
            for d in devs:
                self.my_params.append('--device')
                self.my_params.append(d)

    def add_network(self, net):
        self.my_params.append('--network')
        self.my_params.append(net)

    def add_ip(self, ipaddr):
        self.my_params.append('--ip=%s' % ipaddr)

    def run_foreground(self):
        log.info("docker jail running foreground")
        self.check_mandatory(self.spec_mandatory)
        self.my_docker.container_qrun(image      = self['rootfs-image'],
                                      cmdline    = self.get_cf_list('command'),
                                      extra_args = self.my_params,
                                      env        = self.my_env,
                                      name       = self.my_container_name)

    # FIXME: check for already running
    def run_detached(self):
        log.info("docker jail running detached")
        self.check_mandatory(self.spec_mandatory)
        id = self.my_docker.container_run_detached(
            image      = self['rootfs-image'],
            cmdline    = self.get_cf_list('command'),
            extra_args = self.my_params,
            env        = self.my_env,
            name       = self.my_container_name)
        log.info("new container ID: "+id)
        return id

    def create(self):
        log.info("creating container: %s" % self.my_container_name)
        self.my_jail = self.my_docker.container_create(
            image        = self['rootfs-image'],
            cmdline      = self.get_cf_list('command'),
            extra_args   = self.my_params,
            env          = self.my_env,
            name         = self.my_container_name,
            auto_destroy = False)
        log.info("new container ID: "+str(self.my_jail))

    def start(self):
        log.info("starting container: %s" % self.my_container_name)
        return self.my_jail.start()

    def join_network(self, netname):
        self.my_jail.join_network(netname)

    def destroy(self):
        self.my_docker.container_get(self.my_container_name).destroy()

    """execute inside running container"""
    def execute(self, args):
        return self.my_docker.container_get(self.my_container_name).execute(args)

    def check_running(self):
        return len(self.my_docker.container_running_id(self.my_container_name)) > 0

    def check_rootfs(self):
        return self.my_docker.image_check(self['rootfs-image'])

    def network_create(self, name, label=None, driver=None, internal=None, subnet=None, ip_range=None):
        return self.my_docker.network_create(
            name     = name,
            label    = label,
            driver   = driver,
            internal = internal,
            subnet   = subnet,
            ip_range = ip_range
        )

    def signal(self, sig):
        return self.my_docker.container_get(self.my_container_name).signal(sig)
