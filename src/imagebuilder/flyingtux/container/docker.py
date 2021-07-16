from metux.util.fs import mkdir
from metux.util import log
from metux.util.docker import Docker
from os.path import dirname
from metux.util.specobject import SpecObject

class ContainerDriverDocker(SpecObject):
    def __init__(self, param):
        SpecObject.__init__(self, param)
        self.my_params = ['--read-only']
        self.my_docker = Docker()
        self.my_env = {}

    def add_mounts(self, mounts):
        if mounts is not None:
            for m in mounts:
                if m['type'] == 'bind':
                    self.my_params.append('-v')
                    self.my_params.append(m['source']+':'+m['target'])
                else:
                    raise Exception("unsupported mount type: "+m['type'])

    def add_tempdirs(self, dirs):
        if dirs is not None:
            for t in dirs:
                self.my_params.append('--mount')
                self.my_params.append('type=tmpfs,destination=%s' % t)

    def add_env(self, env):
        if env is not None:
            self.my_env.update(env)

    def run(self):
        log.info("docker jail running")
        self.check_mandatory(['tarball', 'image', 'command'])
        self.my_docker.container_qrun(image      = self['image'],
                                      cmdline    = [self['command']],
                                      extra_args = self.my_params,
                                      env        = self.my_env)
