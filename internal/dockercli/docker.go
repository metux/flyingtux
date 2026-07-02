// SPDX-License-Identifier: AGPL-3.0-or-later

// Package dockercli is a subprocess wrapper around the `docker` CLI, a faithful
// port of the Python metux.util.docker module (Docker + DockerContainer). It
// shells out to docker rather than using the daemon API, exactly like the
// original, so there is no daemon/library coupling.
package dockercli

import (
	"os"
	"os/exec"
	"sort"
	"strings"
)

// Docker is the docker CLI entry point. The binary can be overridden via $DOCKER.
type Docker struct {
	cmd string
}

func New() *Docker {
	cmd := os.Getenv("DOCKER")
	if cmd == "" {
		cmd = "docker"
	}
	return &Docker{cmd: cmd}
}

// callStdout runs docker and returns its trimmed stdout (error on non-zero).
func (d *Docker) callStdout(args []string) (string, error) {
	out, err := exec.Command(d.cmd, args...).Output()
	return strings.TrimSpace(string(out)), err
}

// callDirect runs docker with inherited stdio (interactive) and returns the
// exit code.
func (d *Docker) callDirect(args []string) int {
	cmd := exec.Command(d.cmd, args...)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			return ee.ExitCode()
		}
		return 127
	}
	return 0
}

// callCatch runs docker capturing both streams, returning (code, stdout, stderr).
func (d *Docker) callCatch(args []string) (int, string, string) {
	cmd := exec.Command(d.cmd, args...)
	var out, errb strings.Builder
	cmd.Stdout = &out
	cmd.Stderr = &errb
	code := 0
	if err := cmd.Run(); err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			code = ee.ExitCode()
		} else {
			code = 127
		}
	}
	return code, out.String(), errb.String()
}

func envParams(env map[string]string) []string {
	keys := make([]string, 0, len(env))
	for k := range env {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	p := make([]string, 0, len(env)*2)
	for _, k := range keys {
		p = append(p, "-e", k+"="+env[k])
	}
	return p
}

func withName(extra []string, name string) []string {
	out := append([]string{}, extra...)
	if name != "" {
		out = append(out, "--name", name)
	}
	return out
}

// ContainerCreate creates (without starting) a container and returns a handle.
func (d *Docker) ContainerCreate(image string, cmdline []string, name string, extraArgs []string, env map[string]string, autoDestroy bool) (*Container, error) {
	args := append([]string{"create"}, envParams(env)...)
	args = append(args, withName(extraArgs, name)...)
	args = append(args, image)
	args = append(args, cmdline...)
	id, err := d.callStdout(args)
	if err != nil {
		return nil, err
	}
	return d.ContainerGet(id, autoDestroy), nil
}

// ContainerGet returns a handle to an existing container by id or name.
func (d *Docker) ContainerGet(id string, autoDestroy bool) *Container {
	c := &Container{d: d, id: id, autoDestroy: autoDestroy}
	registerCleanup(c)
	return c
}

// ContainerQRun runs a container interactively (`run -ti --rm`), returning the
// exit code.
func (d *Docker) ContainerQRun(image string, cmdline []string, name string, extraArgs []string, env map[string]string) int {
	args := append([]string{"run", "-ti", "--rm"}, envParams(env)...)
	args = append(args, withName(extraArgs, name)...)
	args = append(args, image)
	args = append(args, cmdline...)
	return d.callDirect(args)
}

// ContainerRunDetached runs a container detached (`run -ti -d --rm`), returning
// its id.
func (d *Docker) ContainerRunDetached(image string, cmdline []string, name string, extraArgs []string, env map[string]string) (string, error) {
	args := append([]string{"run", "-ti", "-d", "--rm"}, envParams(env)...)
	args = append(args, withName(extraArgs, name)...)
	args = append(args, image)
	args = append(args, cmdline...)
	return d.callStdout(args)
}

// ContainerRunningID returns the id of a running container matching name.
func (d *Docker) ContainerRunningID(name string) (string, error) {
	return d.callStdout([]string{"container", "ls", "-q", "-f", "name=" + name})
}

// ImageImport imports a tarball as an image.
func (d *Docker) ImageImport(filename, name string) (string, error) {
	return d.callStdout([]string{"image", "import", filename, name})
}

// ImageCheck reports whether an image exists.
func (d *Docker) ImageCheck(name string) bool {
	code, _, _ := d.callCatch([]string{"inspect", "--type=image", name})
	return code == 0
}

// NetworkConnect connects a container to a network.
func (d *Docker) NetworkConnect(netname, containerID string) int {
	return d.callDirect([]string{"network", "connect", netname, containerID})
}

// NetworkCreate creates a docker network.
func (d *Docker) NetworkCreate(name, label, driver string, internal bool, subnet, ipRange string) (string, error) {
	args := []string{"network", "create"}
	if label != "" {
		args = append(args, "--label", label)
	}
	if driver != "" {
		args = append(args, "--driver", driver)
	}
	if internal {
		args = append(args, "--internal")
	}
	if ipRange != "" {
		args = append(args, "--ip-range="+ipRange)
	}
	if subnet != "" {
		args = append(args, "--subnet="+subnet)
	}
	args = append(args, name)
	return d.callStdout(args)
}
