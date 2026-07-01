// Package pkg abstracts the distro package manager used to populate an image
// sysroot inside a build jail (port of flyingtux.pkg).
package pkg

import (
	"github.com/metux/flyingtux/internal/buildjail"
	"github.com/metux/flyingtux/internal/util"
)

// Repos is a set of package repositories (urls) and their signing keys,
// mirroring the dict returned by the spec get_repos() helpers.
type Repos struct {
	URLs []string
	Keys []string
}

// Pkg is the package-manager interface driven by the builder.
type Pkg interface {
	Prepare() error
	AddRepos(repos *Repos) error
	AddPackages(pkgs []string) error
	Finish() error
}

// Get returns the package-manager driver for the given engine (port of pkg.get).
func Get(drv, arch string, jail buildjail.BuildJail) (Pkg, error) {
	switch drv {
	case "apk":
		return newAlpine(arch, jail)
	default:
		return nil, util.UnsupportedPkg("unsupported pkg driver: %s", drv)
	}
}

// base holds the shared jail + init-dirs handling (BasePkg).
type base struct {
	jail     buildjail.BuildJail
	initDirs []string
}

func (b *base) prepareBase() error {
	if err := b.jail.Prepare(); err != nil {
		return err
	}
	return b.jail.SysrootCreateDirs(b.initDirs)
}

func (b *base) Finish() error { return b.jail.Finish() }
