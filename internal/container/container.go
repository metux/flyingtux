// Package container is the runtime container driver used to run an app from an
// already-built image (port of flyingtux.container). Only docker is supported,
// as in the original.
package container

import (
	"fmt"

	"github.com/metux/flyingtux/internal/dockercli"
	"github.com/metux/flyingtux/internal/log"
	"github.com/metux/flyingtux/internal/services"
	"github.com/metux/flyingtux/internal/util"
)

// Config constructs a container (the Python param dict subset actually used:
// engine, name, rootfs-image, command, tempdirs).
type Config struct {
	Engine      string
	Name        string
	RootfsImage string
	Command     []string
	Tempdirs    []string
}

// Container drives a docker runtime container (port of ContainerDriverDocker).
type Container struct {
	docker      *dockercli.Docker
	params      []string
	env         map[string]string
	name        string
	rootfsImage string
	command     []string
	jail        *dockercli.Container
}

// Get returns the runtime container driver for the engine (port of
// container.get).
func Get(cfg Config) (*Container, error) {
	if cfg.Engine != "docker" {
		return nil, util.UnsupportedJail("unknown container type %s", cfg.Engine)
	}
	c := &Container{
		docker:      dockercli.New(),
		env:         map[string]string{},
		name:        cfg.Name,
		rootfsImage: cfg.RootfsImage,
		command:     cfg.Command,
	}
	c.AddTempdirs(cfg.Tempdirs)
	return c, nil
}

// AddParams applies a service's contribution to the container config
// (port of add_params).
func (c *Container) AddParams(r *services.Result) {
	if r == nil {
		return
	}
	c.AddMounts(r.Mounts)
	c.AddEnv(r.Env)
	c.AddTempdirs(r.Tempdirs)
	c.AddOpts(r.Opts)
	c.AddDevices(r.Devices)
}

func (c *Container) AddBindMount(source, target string) {
	c.params = append(c.params, "-v", source+":"+target)
}

func (c *Container) AddMount(m services.Mount) {
	switch m.Type {
	case "bind":
		c.AddBindMount(m.Source, m.Target)
	default:
		log.Warnf("unsupported mount type: %s", m.Type)
	}
}

func (c *Container) AddMounts(mounts []services.Mount) {
	for _, m := range mounts {
		c.AddMount(m)
	}
}

func (c *Container) AddTempdir(t string) {
	c.params = append(c.params, "--mount", fmt.Sprintf("type=tmpfs,destination=%s", t))
}

func (c *Container) AddTempdirs(dirs []string) {
	for _, t := range dirs {
		c.AddTempdir(t)
	}
}

func (c *Container) AddEnv(env map[string]string) {
	for k, v := range env {
		c.env[k] = v
	}
}

// AddOpts applies container options (port of add_opts). Empty/false fields are
// skipped.
func (c *Container) AddOpts(o services.Opts) {
	if o.IPC != "" {
		c.params = append(c.params, "--ipc", o.IPC)
	}
	if o.User != "" {
		c.params = append(c.params, "--user", o.User)
	}
	if o.Name != "" {
		c.name = o.Name
	}
	if o.ReadOnly {
		c.params = append(c.params, "--read-only")
	}
}

func (c *Container) AddDevices(devs []string) {
	for _, d := range devs {
		c.params = append(c.params, "--device", d)
	}
}

func (c *Container) AddNetwork(net string) { c.params = append(c.params, "--network", net) }
func (c *Container) AddIP(ip string)       { c.params = append(c.params, "--ip="+ip) }

func (c *Container) checkMandatory() error {
	if c.rootfsImage == "" || len(c.command) == 0 {
		return util.ConfigError("container: missing mandatory field (rootfs-image/command)")
	}
	return nil
}

// RunForeground runs the container interactively (port of run_foreground).
func (c *Container) RunForeground() (int, error) {
	log.Info("docker jail running foreground")
	if err := c.checkMandatory(); err != nil {
		return 0, err
	}
	return c.docker.ContainerQRun(c.rootfsImage, c.command, c.name, c.params, c.env), nil
}

// RunDetached runs the container detached (port of run_detached).
func (c *Container) RunDetached() (string, error) {
	log.Info("docker jail running detached")
	if err := c.checkMandatory(); err != nil {
		return "", err
	}
	id, err := c.docker.ContainerRunDetached(c.rootfsImage, c.command, c.name, c.params, c.env)
	if err == nil {
		log.Info("new container ID: " + id)
	}
	return id, err
}

// Create creates (without starting) the container (port of create).
func (c *Container) Create() error {
	log.Infof("creating container: %s", c.name)
	jail, err := c.docker.ContainerCreate(c.rootfsImage, c.command, c.name, c.params, c.env, false)
	if err != nil {
		return err
	}
	c.jail = jail
	log.Info("new container ID: " + jail.ID())
	return nil
}

func (c *Container) Start() int {
	log.Infof("starting container: %s", c.name)
	if c.jail == nil {
		return 127
	}
	return c.jail.Start()
}

func (c *Container) JoinNetwork(netname string) {
	if c.jail != nil {
		c.jail.JoinNetwork(netname)
	}
}

func (c *Container) Destroy() {
	c.docker.ContainerGet(c.name, false).Destroy()
}

// Execute runs a command inside the running container (port of execute).
func (c *Container) Execute(args []string) int {
	return c.docker.ContainerGet(c.name, false).Execute(args)
}

func (c *Container) CheckRunning() bool {
	id, _ := c.docker.ContainerRunningID(c.name)
	return len(id) > 0
}

func (c *Container) CheckRootfs() bool {
	return c.docker.ImageCheck(c.rootfsImage)
}

func (c *Container) NetworkCreate(name, label, driver string, internal bool, subnet, ipRange string) (string, error) {
	return c.docker.NetworkCreate(name, label, driver, internal, subnet, ipRange)
}

func (c *Container) Signal(sig string) (string, error) {
	return c.docker.ContainerGet(c.name, false).Signal(sig)
}
