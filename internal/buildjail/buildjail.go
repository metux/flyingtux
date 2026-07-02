// SPDX-License-Identifier: AGPL-3.0-or-later

// Package buildjail abstracts the throwaway container used to assemble an image
// sysroot at build time (port of flyingtux.buildjail).
package buildjail

import "github.com/metux/flyingtux/internal/util"

// Params configures a build jail (the Python param dict: workdir, rootfs-image,
// engine, conf::image, conf::init).
type Params struct {
	Engine      string
	Workdir     string
	RootfsImage string
	ConfImage   string
	ConfInit    string
}

// BuildJail is the sysroot-manipulation interface the package manager and
// builder drive.
type BuildJail interface {
	Prepare() error
	Finish() error
	SysrootFn(fn string) string
	SysrootCreateDirs(dirs []string) error
	SysrootWriteFile(fn, text string) error
	SysrootCopyFile(src, dst, mode, owner string) error
	SysrootRemoveRecursive(dirs []string) error
	SysrootRemoveDirs(dirs []string) error
	SysrootSymlink(name, target string) error
	CallCmd(args []string) int
}

// Get returns the build-jail driver for the given engine (port of
// buildjail.get).
func Get(p Params) (BuildJail, error) {
	switch p.Engine {
	case "docker":
		return newDocker(p)
	default:
		return nil, util.UnsupportedJail("unknown build jail type %s", p.Engine)
	}
}
