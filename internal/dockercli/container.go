// SPDX-License-Identifier: AGPL-3.0-or-later

package dockercli

// Container is a handle to a docker container (port of DockerContainer).
type Container struct {
	d           *Docker
	id          string
	autoDestroy bool
}

func (c *Container) ID() string { return c.id }

func (c *Container) SetAutoDestroy(a bool) { c.autoDestroy = a }

// Start starts the container.
func (c *Container) Start(args ...string) int {
	return c.d.callDirect(append([]string{"start", c.id}, args...))
}

// Destroy force-removes the container.
func (c *Container) Destroy() (int, string, string) {
	return c.d.callCatch([]string{"rm", "-f", c.id})
}

// Execute runs a command in the container (interactive stdio).
func (c *Container) Execute(args []string) int {
	return c.d.callDirect(append([]string{"exec", c.id}, args...))
}

// ExecStdout runs a command capturing stdout.
func (c *Container) ExecStdout(args []string) (string, error) {
	return c.d.callStdout(append([]string{"exec", c.id}, args...))
}

// ExecCatch runs a command capturing stdout+stderr and the exit code.
func (c *Container) ExecCatch(args []string) (int, string, string) {
	return c.d.callCatch(append([]string{"exec", c.id}, args...))
}

func (c *Container) Mkdirs(dirs []string) int {
	return c.Execute(append([]string{"mkdir", "-p"}, dirs...))
}

// CpTo copies a host file into the container, optionally chown/chmod'ing it
// (pass "" to skip).
func (c *Container) CpTo(src, dest, owner, mode string) int {
	ret := c.d.callDirect([]string{"cp", src, c.id + ":" + dest})
	if owner != "" {
		c.Chown(owner, []string{dest})
	}
	if mode != "" {
		c.Chmod(mode, []string{dest})
	}
	return ret
}

func (c *Container) CpFrom(src, dest string) int {
	return c.d.callDirect([]string{"cp", c.id + ":" + src, dest})
}

func (c *Container) Chown(owner string, files []string) int {
	return c.d.callDirect(append([]string{"exec", c.id, "chown", owner}, files...))
}

func (c *Container) Chmod(mode string, files []string) int {
	return c.d.callDirect(append([]string{"exec", c.id, "chmod", mode}, files...))
}

func (c *Container) RmRecursive(dirs []string) int {
	return c.d.callDirect(append([]string{"exec", c.id, "rm", "-Rf"}, dirs...))
}

func (c *Container) Signal(sig string) (string, error) {
	return c.d.callStdout([]string{"kill", "-s", sig, c.id})
}

func (c *Container) JoinNetwork(netname string) {
	c.d.NetworkConnect(netname, c.id)
}

// --- atexit auto-destroy registry (mirrors DockerContainer.__atexit) ---

var cleanups []*Container

func registerCleanup(c *Container) { cleanups = append(cleanups, c) }

// RunCleanups destroys all auto-destroy containers. main() should defer it.
func RunCleanups() {
	for _, c := range cleanups {
		if c.autoDestroy {
			c.Destroy()
		}
	}
}
