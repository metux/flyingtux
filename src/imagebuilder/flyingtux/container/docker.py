from metux.util import log
from metux.util.docker import Docker
from os.path import dirname
from metux.util.specobject import SpecObject

class ContainerDriverDocker(SpecObject):

    spec_mandatory = ['rootfs-image', 'command']

    def __init__(self, param):
        SpecObject.__init__(self, param)
        self.my_params = ['--read-only']
        self.my_docker = Docker()
        self.my_env = {}
        self.my_container_name = None
        self.add_params(param)

    def add_params(self, p):
        self.add_mounts(p.get('mounts'))
        self.add_env(p.get('env'))
        self.add_tempdirs(p.get('tempdirs'))
        self.add_opts(p.get('opts'))
        self.add_devices(p.get('devices'))

    def add_mounts(self, mounts):
        if mounts is not None:
            for m in mounts:
                if m['type'] == 'bind':
                    self.my_params.append('-v')
                    self.my_params.append(m['source']+':'+m['target'])
                else:
                    raise FT_ConfigError("unsupported mount type: "+m['type'])

    def add_tempdirs(self, dirs):
        if dirs is not None:
            for t in dirs:
                self.my_params.append('--mount')
                self.my_params.append('type=tmpfs,destination=%s' % t)

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
                    self.my_params.append('--name')
                    self.my_params.append(v)
                else:
                    raise FT_ConfigError("container opt %s (%s) not understood" % (o,v))

    def add_devices(self, devs):
        if devs is not None:
            for d in devs:
                self.my_params.append('--device')
                self.my_params.append(d)

    def run(self):
        log.info("docker jail running")
        self.check_mandatory(self.spec_mandatory)
        self.my_docker.container_qrun(image      = self['rootfs-image'],
                                      cmdline    = self.get_cf_list('command'),
                                      extra_args = self.my_params,
                                      env        = self.my_env)

    def check_rootfs(self):
        return self.my_docker.image_check(self['rootfs-image'])
