# SPDX-License-Identifier: AGPL-3.0-or-later
from os_service import Base
from metux.util.fs import mkdir
from os.path import dirname
from subprocess import Popen, PIPE
from os import environ, urandom, chmod

"""
Access to X11 display.

2DO: add user-configured redirection to somewhere else, e.g.
a nested Xserver, so app has no access to X resources of other
applications.

X-NAMESPACE (see setup_namespace() below) is a first step towards that:
where available, the app's connection is confined to its own namespace
instead of getting the full, unrestricted display. It's best-effort and
optional on purpose - the extension is still DRAFT/experimental, requires
an XLibre server built with it *and* started with a "-namespace <config>"
granting our own connection management rights (plain QueryExtension
already reports the extension as absent to any client without that
privilege - there's no way to tell "not built in" apart from "built in but
we're not privileged", and both cases must fall back the same way).

Confirmed root cause (2026-07-01/02, mpbt-workspace DASHBOARD.md): stock
xserver-master's Xext/namespace/ only wires the ACE enforcement hooks, it
never registers X-NAMESPACE as a queryable/dispatchable protocol extension
- that missing wire-protocol registration lives on xserver PR #3103
(branch draft/xns-proto), not yet merged. Built from that branch, the
extension works end-to-end: 'xnamespace -s version'/'-s list' succeed and
go-x11proto's run-xnamespace-test.sh passes 40/40 (both byte orders). So
today this falls back to the plain bind-mount below on every server except
one built from draft/xns-proto; it starts paying off as soon as #3103 (or
an equivalent) merges upstream.
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
        return p.wait(), stdout.strip(), stderr.strip()

    """probe whether we're allowed to see/manage X-NAMESPACE on this display at all"""
    def probe_namespace(self, display):
        rc, out, err = self.run_xnamespace(display, ['version'])
        if rc != 0:
            self.info("X-NAMESPACE unavailable on "+display+": "+(err or "unknown error"))
            return False
        self.info("X-NAMESPACE present, version "+out)
        return True

    def setup_namespace(self, display):
        if not self.probe_namespace(display):
            return

        name = 'app-'+self.get_app_name()
        caps = [c for c in self.get_setting('x11-namespace-caps').split(',') if c]

        rc, out, err = self.run_xnamespace(display, ['create', name]+caps+['transient'])
        if rc != 0:
            self.info("X-NAMESPACE create "+name+" failed (may already exist): "+(err or "unknown error"))

        token = urandom(16).encode('hex')
        rc, out, err = self.run_xnamespace(display, ['addtoken', name, 'MIT-MAGIC-COOKIE-1', token])
        if rc != 0:
            self.info("X-NAMESPACE addtoken for "+name+" failed, falling back to full access: "+(err or "unknown error"))
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
        chmod(fn, 0644)
        return fn
