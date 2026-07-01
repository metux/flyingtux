from subprocess import Popen, PIPE, check_output
from os import environ
import atexit

class DockerContainer:
    def __init__(self, docker, id, auto_destroy = True):
        self.my_docker = docker
        self.my_id = id
        self.my_auto_destroy = auto_destroy
        atexit.register(self.__atexit)

    def _call_stdout(self, cmd, args = []):
        return self.my_docker._call_stdout([cmd, self.my_id]+args)

    def _call_direct(self, cmd, args = []):
        return self.my_docker._call_direct([cmd, self.my_id]+args)

    def start(self):
        return self._call_stdout('start')

    def stop(self):
        return self._call_catch('stop')

    def remove(self):
        return self._call_catch('rm')

    def destroy(self):
        return self.my_docker._call_catch(['rm', '-f', self.my_id])

    def execute(self, args):
        return self._call_direct('exec', args)

    def exec_stdout(self, args):
        return self.my_docker._call_stdout(['exec', self.my_id]+args)

    def exec_catch(self, args):
        return self.my_docker._call_catch(['exec', self.my_id]+args)

    def mkdirs(self, dirs):
        return self.execute(['mkdir', '-p']+dirs)

    def cp_to(self, src, dest, owner=None, mode=None):
        ret = self.my_docker._call_direct(['cp', src, self.my_id+':'+dest])
        if owner is not None:
            self.chown(owner, [dest])
        if mode is not None:
            self.chmod(mode, [dest])
        return ret

    def cp_from(self, src, dest):
        return self.my_docker._call_direct(['cp', self.my_id+':'+src, dest])

    def chown(self, owner, files):
        return self.my_docker._call_direct(['exec', self.my_id, 'chown', owner]+files)

    def chmod(self, mode, files):
        return self.my_docker._call_direct(['exec', self.my_id, 'chmod', mode]+files)

    def rm_recursive(self, dirs):
        return self.my_docker._call_direct(['exec', self.my_id, 'rm', '-Rf']+dirs)

    def __atexit(self):
        if self.my_auto_destroy:
            self.destroy()

    def signal(self, sig):
        return self.my_docker._call_stdout(['kill', '-s', sig, self.my_id])

    def set_auto_destroy(self, a):
        self.my_auto_destroy = a

    def join_network(self, netname):
        self.my_docker.network_connect(netname, self.my_id)

    def start(self, args = []):
        self._call_direct('start', args)

class Docker:
    def __init__(self):
        if 'DOCKER' in environ:
            self.cmd = environ['DOCKER']
        else:
            self.cmd = 'docker'

    def _call_stdout(self, args):
        return check_output([self.cmd]+args)

    def _call_direct(self, args):
        process = Popen([self.cmd]+args)
        stdout, stderr = process.communicate()
        return process.wait()

    def _call_catch(self, args):
        process = Popen([self.cmd]+args, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        exit_code = process.wait()
        return exit_code, stdout, stderr

    def container_create(self, image, args):
        return DockerContainer(self, self._call_stdout(['create', image]+args).strip(), False)

    def container_get(self, name, auto_destroy = False):
        return DockerContainer(self, name, auto_destroy)

    def container_qrun(self, image, cmdline, name=None, extra_args=[], env={}):
        if image is None:
            raise Exception("image cant be none")

        if name is not None:
            extra_args.append('--name')
            extra_args.append(name)

        env_param = []
        for n,v in env.iteritems():
            env_param.append('-e')
            env_param.append(n+'='+v)

        x = ['run', '-ti', '--rm']+ env_param + extra_args + [image] + cmdline
        return self._call_direct(x)

    def container_run_detached(self, image, cmdline, name=None, extra_args=[], env={}):
        if image is None:
            raise Exception("image cant be none")

        if name is not None:
            extra_args.append('--name')
            extra_args.append(name)

        env_param = []
        for n,v in env.iteritems():
            env_param.append('-e')
            env_param.append(n+'='+v)

        x = ['run', '-ti', '-d', '--rm']+ env_param + extra_args + [image] + cmdline
        return self._call_stdout(x)

    def container_create(self, image, cmdline, name=None, extra_args=[], env={}, auto_destroy = False):
        if image is None:
            raise Exception("image cant be none")

        if name is not None:
            extra_args.append('--name')
            extra_args.append(name)

        env_param = []
        for n,v in env.iteritems():
            env_param.append('-e')
            env_param.append(n+'='+v)

        x = ['create']+ env_param + extra_args + [image] + cmdline
        id = self._call_stdout(x).strip()
        return self.container_get(id, auto_destroy)

    def container_running_id(self, name):
        return self._call_stdout(['container', 'ls', '-q', '-f', 'name='+name]).strip()

    def image_import(self, filename, name):
        return self._call_stdout(['image', 'import', filename, name])

    def network_connect(self, netname, container_id):
        return self._call_direct(['network', 'connect', netname, container_id])

    def image_check(self, name):
        exit_code, stdout, stderr = self._call_catch(['inspect', '--type=image', name])
        return exit_code == 0

    def network_create(self, name = None, label = None, driver = None, internal = None, subnet = None, ip_range = None):
        args = ['network', 'create']
        if 'name' is None:
            raise Exception("need network name")
        if label is not None:
            args.append('--label')
            args.append(label)
        if driver is not None:
            args.append('--driver')
            args.append(driver)
        if internal is not None and internal:
            args.append('--internal')
        if ip_range is not None:
            args.append('--ip-range='+ip_range)
        if subnet is not None:
            args.append('--subnet='+subnet)
        args.append(name)
        return self._call_stdout(args)
