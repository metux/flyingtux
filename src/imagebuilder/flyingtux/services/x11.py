# SPDX-License-Identifier: AGPL-3.0-or-later
from .os_service import Base
from metux.util.fs import mkdir
from metux.util.log import warn
from os.path import dirname
from subprocess import Popen, PIPE, check_output
from os import environ, urandom, chmod
import re

"""
Access to X11 display.

2DO: add user-configured redirection to somewhere else, e.g.
a nested Xserver, so app has no access to X resources of other
applications.

X-NAMESPACE (see setup_namespace() below) confines the app to its own
namespace instead of getting the full, unrestricted display. Requires an
XLibre server with X-NAMESPACE support (merged in xserver-master as of
2026-07-03, PR #3103) started with "-namespace <config>" granting
management rights.

Falls back to full display access if X-NAMESPACE is unavailable (server
too old, not built with namespace support, or lacking management
privileges). A visible warning is printed on the console in this case.
"""
class X11(Base):
    permissions = {
        '__enabled__': { 'default': True },
        'shm':       { 'default': True, 'description': 'shared memory extension' },
        'namespace': { 'default': True, 'description': 'confine the app to its own X-NAMESPACE, if the display supports it and we are allowed to manage it (falls back to full access otherwise)' },
    }

    settings = {
        'x11-display': {
            'default':     '${ENV::DISPLAY}',
            'type':        'string',
            'description': 'number of the X11 display to attach to',
        },
        'x11-socketdir': {
            'default':     '/tmp/.X11-unix',
            'type':        'host-path',
            'description': 'directory of X11 sockets',
        },
        'x11-namespace-bin': {
            'default':     'xnamespace',
            'type':        'string',
            'description': 'path/name of the xnamespace CLI tool (github.com/X11Libre/go-x11proto) used to probe/manage the X-NAMESPACE extension',
        },
        'x11-namespace-caps': {
            'default':     'mouse,keyboard,shape,input',
            'type':        'string',
            'description': 'comma-separated X-NAMESPACE capabilities granted to the app namespace (never include admin/all here)',
        },
    }

    def compute(self):
        import re

        display = self.get_setting('x11-display')

        disp = re.search('^:([0-9]+)(\.[0-9]+|)$', display).group(1)
        sockname = self.get_path_setting('x11-socketdir')+'/X'+disp

        self.info("display: "+str(display))
        self.add_env('DISPLAY', display)
        self.bind_file_direct(sockname)

        if self.is_permitted('shm'):
            self.info("host shm: enabled")
            self.set_container_opt('ipc', 'host')
        else:
            self.info("host shm: disabled")

        if self.is_permitted('namespace'):
            self.setup_namespace(display)
        else:
            self.info("X-NAMESPACE isolation: disabled by config")

    def run_xnamespace(self, display, args):
        xnbin = self.get_setting('x11-namespace-bin')
        env = dict(environ)
        env['DISPLAY'] = display
        try:
            p = Popen([xnbin, '-s']+args, stdout=PIPE, stderr=PIPE, env=env)
        except OSError as e:
            return 127, '', str(e)
        stdout, stderr = p.communicate()
        return p.wait(), stdout.decode().strip(), stderr.decode().strip()

    """probe whether we're allowed to see/manage X-NAMESPACE on this display at all"""
    def probe_namespace(self, display):
        rc, out, err = self.run_xnamespace(display, ['version'])
        if rc != 0:
            self.info("X-NAMESPACE probe failed on "+display+": "+(err or "unknown error"))
            return False
        self.info("X-NAMESPACE present, version "+out)
        return True

    def setup_namespace(self, display):
        if not self.probe_namespace(display):
            warn("=" * 60)
            warn("X-NAMESPACE ISOLATION UNAVAILABLE")
            warn("App '"+self.get_app_name()+"' will have FULL access to the display")
            warn("No per-app isolation - all X11 resources are shared")
            warn("Start server with '-namespace <config>' to enable isolation")
            warn("=" * 60)
            return

        name = 'app-'+self.get_app_name()
        caps = [c for c in self.get_setting('x11-namespace-caps').split(',') if c]

        rc, out, err = self.run_xnamespace(display, ['create', name]+caps+['transient'])
        if rc != 0:
            warn("X-NAMESPACE create "+name+" failed (may already exist): "+(err or "unknown error"))
            warn("Falling back to full display access - no isolation")
            return

        token = urandom(16).hex()
        rc, out, err = self.run_xnamespace(display, ['addtoken', name, 'MIT-MAGIC-COOKIE-1', token])
        if rc != 0:
            warn("X-NAMESPACE addtoken for "+name+" failed: "+(err or "unknown error"))
            warn("Falling back to full display access - no isolation")
            return

        xauth_file = self.write_xauth(display, token)
        self.add_env('XAUTHORITY', '/etc/x11-app.xauth')
        self.bind_dir(xauth_file, '/etc/x11-app.xauth')
        self.info("X-NAMESPACE: confined to namespace '"+name+"' (caps: "+','.join(caps)+")")

    def write_xauth(self, display, token):
        fn = self.my_runner['TARGET::dynconf-dir']+'/xauth/'+self.get_app_name()+'.xauth'
        mkdir(dirname(fn))
        p = Popen(['xauth', '-f', fn, 'add', display, 'MIT-MAGIC-COOKIE-1', token], stdout=PIPE, stderr=PIPE)
        p.communicate()

        # xauth just wrote a FamilyLocal entry keyed to *our* hostname. The
        # container that reads this file has a different hostname, so a
        # FamilyLocal lookup from inside it never matches and the client
        # falls back to no auth data at all - silently defeating the whole
        # point of this per-app cookie. Rewrite the family as FamilyWild
        # (matches from any host) using the standard xauth nlist/nmerge trick.
        nlist = check_output(['xauth', '-f', fn, 'nlist', display])
        wild = re.sub(rb'^[0-9a-f]{4}', b'ffff', nlist)
        p2 = Popen(['xauth', '-f', fn, 'nmerge', '-'], stdin=PIPE)
        p2.communicate(wild)

        chmod(fn, 0o644)
        return fn
