// SPDX-License-Identifier: AGPL-3.0-or-later

package pkg

import (
	"path/filepath"

	"github.com/metux/flyingtux/internal/buildjail"
	"github.com/metux/flyingtux/internal/util"
)

const apkCmd = "apk"

var alpineInitDirs = []string{
	"etc/apk/cache",
	"etc/apk/keys",
	"var/log",
	"lib/apk/db",
}

// alpine is the APK package manager (port of AlpinePkg).
type alpine struct {
	base
	arch      string
	reposText string
}

func newAlpine(arch string, jail buildjail.BuildJail) (Pkg, error) {
	if arch == "" {
		return nil, util.ConfigError("alpine pkg: missing mandatory field 'arch'")
	}
	return &alpine{
		base: base{jail: jail, initDirs: alpineInitDirs},
		arch: arch,
	}, nil
}

// call invokes apk against the sysroot root (private __call).
func (a *alpine) call(cmd string, args []string) int {
	full := append([]string{apkCmd, cmd, "--root=" + a.jail.SysrootFn("")}, args...)
	return a.jail.CallCmd(full)
}

func (a *alpine) Prepare() error {
	if err := a.prepareBase(); err != nil {
		return err
	}
	if err := a.jail.SysrootWriteFile("/etc/apk/arch", a.arch); err != nil {
		return err
	}
	return a.jail.SysrootWriteFile("/etc/apk/world", "")
}

func (a *alpine) AddRepos(repos *Repos) error {
	if repos == nil {
		return nil
	}
	for _, x := range repos.URLs {
		a.reposText += x + "\n"
	}
	if err := a.jail.SysrootWriteFile("/etc/apk/repositories", a.reposText); err != nil {
		return err
	}
	for _, x := range repos.Keys {
		if err := a.jail.SysrootCopyFile(x, "/etc/apk/keys/"+filepath.Base(x), "", ""); err != nil {
			return err
		}
	}
	return nil
}

func (a *alpine) AddPackages(pkgs []string) error {
	if len(pkgs) == 0 {
		return nil
	}
	if code := a.call("add", pkgs); code != 0 {
		return util.Error("apk add failed (exit %d)", code)
	}
	return nil
}
