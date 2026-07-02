// SPDX-License-Identifier: AGPL-3.0-or-later

package buildjail

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/metux/flyingtux/internal/dockercli"
	"github.com/metux/flyingtux/internal/fs"
	"github.com/metux/flyingtux/internal/util"
)

const (
	rootfsTarball = "/sysroot.tar.bz2"
	buildSysroot  = "/sysroot"
)

// dockerJail is the docker-backed BuildJail (port of BuildJailDriverDocker).
type dockerJail struct {
	workdir     string
	rootfsImage string
	confImage   string
	confInit    string
	docker      *dockercli.Docker
	container   *dockercli.Container
}

func newDocker(p Params) (BuildJail, error) {
	if p.Workdir == "" || p.RootfsImage == "" || p.ConfImage == "" {
		return nil, util.ConfigError("build jail: missing mandatory field (workdir/rootfs-image/conf)")
	}
	return &dockerJail{
		workdir:     p.Workdir,
		rootfsImage: p.RootfsImage,
		confImage:   p.ConfImage,
		confInit:    p.ConfInit,
		docker:      dockercli.New(),
	}, nil
}

func (j *dockerJail) tempFn(fn string) string {
	return fmt.Sprintf("%s/sysroot/%s", j.workdir, fn)
}

func (j *dockerJail) SysrootFn(fn string) string {
	return fmt.Sprintf("%s/%s", buildSysroot, fn)
}

func (j *dockerJail) SysrootCreateDirs(dirs []string) error {
	remote := make([]string, 0, len(dirs))
	for _, x := range dirs {
		remote = append(remote, j.SysrootFn(x))
	}
	j.container.Mkdirs(remote)
	for _, x := range dirs {
		if err := fs.Mkdir(j.tempFn(x)); err != nil {
			return err
		}
	}
	return nil
}

func (j *dockerJail) SysrootWriteFile(fn, text string) error {
	local := j.tempFn(fn)
	remote := j.SysrootFn(fn)
	if err := os.MkdirAll(filepath.Dir(local), 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(local, []byte(text), 0o644); err != nil {
		return err
	}
	j.container.CpTo(local, remote, "", "")
	j.container.Chown("root:root", []string{remote})
	return nil
}

func (j *dockerJail) SysrootCopyFile(src, dst, mode, owner string) error {
	j.container.CpTo(src, j.SysrootFn(dst), owner, mode)
	return nil
}

func (j *dockerJail) SysrootRemoveRecursive(dirs []string) error {
	remote := make([]string, 0, len(dirs))
	for _, x := range dirs {
		remote = append(remote, j.SysrootFn(x))
	}
	j.container.RmRecursive(remote)
	return nil
}

func (j *dockerJail) SysrootRemoveDirs(dirs []string) error {
	args := []string{"find"}
	for _, x := range dirs {
		args = append(args, j.SysrootFn(x))
	}
	args = append(args, "-type", "d", "-empty", "-exec", "rmdir", "-p", "{}", ";")
	j.container.ExecCatch(args)
	return nil
}

func (j *dockerJail) SysrootSymlink(name, target string) error {
	if err := j.SysrootCreateDirs([]string{filepath.Dir(name), filepath.Dir(target)}); err != nil {
		return err
	}
	j.container.Execute([]string{"ln", "-s", target, j.SysrootFn(name)})
	return nil
}

func (j *dockerJail) CallCmd(args []string) int {
	return j.container.Execute(args)
}

func (j *dockerJail) Prepare() error {
	c, err := j.docker.ContainerCreate(j.confImage, []string{j.confInit}, "", nil, nil, false)
	if err != nil {
		return err
	}
	j.container = c
	j.container.Start()
	return nil
}

func (j *dockerJail) Finish() error {
	targetTarball := j.workdir + "/rootfs-temp.tar.bz2"
	targetDir := filepath.Dir(targetTarball)

	j.container.Execute([]string{"tar", "-cf", rootfsTarball, "-C", buildSysroot, "."})
	if err := fs.Mkdir(targetDir); err != nil {
		return err
	}
	j.container.CpFrom(rootfsTarball, targetTarball)
	j.container.Destroy()
	if _, err := j.docker.ImageImport(targetTarball, j.rootfsImage); err != nil {
		return err
	}
	return nil
}
