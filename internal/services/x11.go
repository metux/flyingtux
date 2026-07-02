// SPDX-License-Identifier: AGPL-3.0-or-later

package services

import (
	"crypto/rand"
	"encoding/hex"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/metux/flyingtux/internal/fs"
	"github.com/metux/flyingtux/internal/spec"
	"github.com/metux/flyingtux/internal/util"
)

var displayRe = regexp.MustCompile(`^:([0-9]+)(\.[0-9]+|)$`)

// x11 grants access to the X11 display, optionally confining the app to its own
// X-NAMESPACE when the server supports it (best-effort, falls back to full
// access). Port of services/x11.py.
type x11 struct{ base }

func newX11(sp *spec.SpecObj, r Runner) Service {
	s := &x11{base{
		name: "X11", spec: sp, runner: r,
		permDflt: map[string]bool{"__enabled__": true, "shm": true, "namespace": true},
		setDflt: map[string]string{
			"x11-display":        "${ENV::DISPLAY}",
			"x11-socketdir":      "/tmp/.X11-unix",
			"x11-namespace-bin":  "xnamespace",
			"x11-namespace-caps": "mouse,keyboard,shape,input",
		},
	}}
	s.self = s
	s.init()
	return s
}

func (s *x11) compute() error {
	display := s.getSetting("x11-display")
	m := displayRe.FindStringSubmatch(display)
	if m == nil {
		return util.ConfigError("x11: cannot parse display %q", display)
	}
	disp := m[1]
	sockname := s.getSetting("x11-socketdir") + "/X" + disp

	s.info("display: " + display)
	s.addEnv("DISPLAY", display)
	s.bindFileDirect(sockname)

	if s.isPermitted("shm") {
		s.info("host shm: enabled")
		s.setContainerOpt(func(o *Opts) { o.IPC = "host" })
	} else {
		s.info("host shm: disabled")
	}

	if s.isPermitted("namespace") {
		s.setupNamespace(display)
	} else {
		s.info("X-NAMESPACE isolation: disabled by config")
	}
	return nil
}

func (s *x11) runXnamespace(display string, args []string) (int, string, string) {
	xnbin := s.getSetting("x11-namespace-bin")
	cmd := exec.Command(xnbin, append([]string{"-s"}, args...)...)
	cmd.Env = append(os.Environ(), "DISPLAY="+display)
	var out, errb strings.Builder
	cmd.Stdout = &out
	cmd.Stderr = &errb
	if err := cmd.Run(); err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			return ee.ExitCode(), strings.TrimSpace(out.String()), strings.TrimSpace(errb.String())
		}
		return 127, "", err.Error()
	}
	return 0, strings.TrimSpace(out.String()), strings.TrimSpace(errb.String())
}

func (s *x11) probeNamespace(display string) bool {
	rc, out, errs := s.runXnamespace(display, []string{"version"})
	if rc != 0 {
		if errs == "" {
			errs = "unknown error"
		}
		s.info("X-NAMESPACE unavailable on " + display + ": " + errs)
		return false
	}
	s.info("X-NAMESPACE present, version " + out)
	return true
}

func (s *x11) setupNamespace(display string) {
	if !s.probeNamespace(display) {
		return
	}

	name := "app-" + s.appName()
	var caps []string
	for _, c := range strings.Split(s.getSetting("x11-namespace-caps"), ",") {
		if c != "" {
			caps = append(caps, c)
		}
	}

	if rc, _, errs := s.runXnamespace(display, append(append([]string{"create", name}, caps...), "transient")); rc != 0 {
		if errs == "" {
			errs = "unknown error"
		}
		s.info("X-NAMESPACE create " + name + " failed (may already exist): " + errs)
	}

	tokenBuf := make([]byte, 16)
	if _, err := rand.Read(tokenBuf); err != nil {
		s.info("X-NAMESPACE: failed generating token: " + err.Error())
		return
	}
	token := hex.EncodeToString(tokenBuf)

	if rc, _, errs := s.runXnamespace(display, []string{"addtoken", name, "MIT-MAGIC-COOKIE-1", token}); rc != 0 {
		if errs == "" {
			errs = "unknown error"
		}
		s.info("X-NAMESPACE addtoken for " + name + " failed, falling back to full access: " + errs)
		return
	}

	xauthFile, err := s.writeXauth(display, token)
	if err != nil {
		s.info("X-NAMESPACE: writing xauth failed: " + err.Error())
		return
	}
	s.addEnv("XAUTHORITY", "/etc/x11-app.xauth")
	s.bindDir(xauthFile, "/etc/x11-app.xauth")
	s.info("X-NAMESPACE: confined to namespace '" + name + "' (caps: " + strings.Join(caps, ",") + ")")
}

func (s *x11) writeXauth(display, token string) (string, error) {
	fn := s.runner.Get("TARGET::dynconf-dir") + "/xauth/" + s.appName() + ".xauth"
	if err := fs.Mkdir(filepath.Dir(fn)); err != nil {
		return "", err
	}
	exec.Command("xauth", "-f", fn, "add", display, "MIT-MAGIC-COOKIE-1", token).Run()
	os.Chmod(fn, 0o644)
	return fn, nil
}
