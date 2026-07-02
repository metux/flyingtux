package app

import (
	"os"
	"strings"

	"github.com/metux/flyingtux/internal/container"
	"github.com/metux/flyingtux/internal/fs"
	"github.com/metux/flyingtux/internal/services"
	"github.com/metux/flyingtux/internal/spec"
	"github.com/metux/flyingtux/internal/util"
)

func containerForEngine(engine string) (*container.Container, error) {
	return container.Get(container.Config{Engine: engine})
}

// Runner runs a deployed app (port of app.runner.Runner). It implements
// services.Runner.
type Runner struct {
	toolBase
	jail         *container.Container
	appVolumeDir string
	appCacheDir  string
	ipAddress    string
}

// --- services.Runner interface ---

func (r *Runner) Get(key string) string { return r.GetStr(spec.Key(key)) }
func (r *Runner) IPAddress() string      { return r.ipAddress }

func (r *Runner) StartWebProxy() (string, error) {
	t := r.target
	p := webProxyParam{
		engine:     t.GetStr("jail-engine"),
		name:       t.GetStr("web-proxy::name"),
		image:      t.GetStr("web-proxy::image"),
		bridge:     t.GetStr("jail-network::bridge"),
		network:    t.GetStr("jail-network::name"),
		ip:         t.GetStr("web-proxy::ip"),
		port:       t.GetStr("web-proxy::port"),
		confSource: t.GetStr("web-proxy::conf-source"),
		confTarget: t.GetStr("web-proxy::conf-target"),
	}
	wp, err := newWebProxyContainer(p)
	if err != nil {
		return "", err
	}
	wp.reload()
	return wp.getURL(), nil
}

func (r *Runner) dataVolDir(volname string) string  { return r.appVolumeDir + "/" + baseName(volname) }
func (r *Runner) cacheVolDir(volname string) string { return r.appCacheDir + "/" + baseName(volname) }

func (r *Runner) mountVolume(vol *spec.SpecObj) error {
	switch {
	case vol.Has("tempdir"):
		r.jail.AddTempdir(vol.GetStr("tempdir"))
	case vol.Has("datadir"):
		if !vol.Has("name") {
			return util.Error("data volume needs a name: %s", vol.GetStr("datadir"))
		}
		d := r.dataVolDir(vol.GetStr("name"))
		if err := fs.Mkdir(d); err != nil {
			return err
		}
		r.jail.AddBindMount(d, vol.GetStr("datadir"))
	case vol.Has("cachedir"):
		if !vol.Has("name") {
			return util.Error("data volume needs a name: %s", vol.GetStr("cachedir"))
		}
		d := r.cacheVolDir(vol.GetStr("name"))
		if err := fs.Mkdir(d); err != nil {
			return err
		}
		r.jail.AddBindMount(d, vol.GetStr("cachedir"))
	case vol.Has("nullfile"):
		r.jail.AddBindMount("/dev/null", vol.GetStr("nullfile"))
	default:
		return util.Error("unknown volume type")
	}
	return nil
}

func (r *Runner) initJail() error {
	for _, kv := range os.Environ() {
		if i := strings.IndexByte(kv, '='); i >= 0 {
			r.SetStr(spec.Key("ENV::"+kv[:i]), kv[i+1:])
		}
	}

	jail, err := container.Get(container.Config{
		Engine:      r.GetStr("engine"),
		Name:        r.GetStr("name"),
		RootfsImage: r.GetStr("rootfs-image"),
		Command:     r.GetStrList("command"),
		Tempdirs:    r.GetStrList("tmpdirs"),
	})
	if err != nil {
		return err
	}
	r.jail = jail
	r.appVolumeDir = r.GetStr("APP-VOLUME-DIR")
	r.appCacheDir = r.GetStr("APP-CACHE-DIR")

	ip, err := r.target.GetAppIPAddr(r.GetStr("image"))
	if err != nil {
		return err
	}
	r.ipAddress = ip

	for _, e := range r.SubElems("volumes") {
		if err := r.mountVolume(spec.Wrap(e)); err != nil {
			return err
		}
	}

	for _, name := range r.SubKeys("os-services") {
		sspec := r.Sub(spec.Key("os-services::" + string(name)))
		res, err := services.ProcessService(string(name), sspec, r)
		if err != nil {
			return err
		}
		r.jail.AddParams(res)
	}

	r.jail.AddOpts(services.Opts{
		User:     r.GetStr("user"),
		Name:     r.GetStr("name"),
		ReadOnly: true,
	})
	r.jail.AddNetwork(r.target.GetStr("jail-network::name"))
	r.jail.AddIP(r.ipAddress)
	return nil
}

// Configure sets up the container without running it (port of configure).
func (r *Runner) Configure() error { return r.initJail() }

// Run runs the app, building the image first if missing (port of run).
func (r *Runner) Run(args []string) (int, error) {
	if err := r.initJail(); err != nil {
		return 0, err
	}
	r.target.StartNetwork()
	if r.jail.CheckRunning() {
		r.info("container already running")
		return 0, nil
	}
	r.info("container not running yet")
	if !r.jail.CheckRootfs() {
		r.info("missing image: " + r.GetStr("image"))
		b, err := r.target.GetBuilder(r.GetStr("image"))
		if err != nil {
			return 0, err
		}
		if _, err := b.Run(); err != nil {
			return 0, err
		}
	}
	return r.jail.RunForeground()
}

// Execute runs a command in the app container (port of execute).
func (r *Runner) Execute(args []string) (int, error) {
	if err := r.initJail(); err != nil {
		return 0, err
	}
	if !r.jail.CheckRunning() {
		if _, err := r.Run(nil); err != nil {
			return 0, err
		}
	}
	return r.jail.Execute(args), nil
}

// --- service containers (port of ServiceContainer / WebProxyContainer) ---

type serviceContainer struct {
	jail    *container.Container
	bridge  string
	network string
	ip      string
}

func newServiceContainer(engine, name, image, network, bridge, ip string) (*serviceContainer, error) {
	jail, err := container.Get(container.Config{Engine: engine, Name: name, RootfsImage: image})
	if err != nil {
		return nil, err
	}
	return &serviceContainer{jail: jail, bridge: bridge, network: network, ip: ip}, nil
}

func (s *serviceContainer) reload() {
	if s.jail.CheckRunning() {
		s.jail.Signal("HUP")
	} else {
		s.startup()
	}
}

func (s *serviceContainer) startup() int {
	if s.ip != "" {
		s.jail.AddIP(s.ip)
	}
	if s.network != "" {
		s.jail.AddNetwork(s.network)
	}
	s.jail.Destroy()
	s.jail.Create()
	if s.bridge != "" {
		s.jail.JoinNetwork(s.bridge)
	}
	return s.jail.Start()
}

type webProxyParam struct {
	engine, name, image, bridge, network, ip, port, confSource, confTarget string
}

type webProxyContainer struct {
	*serviceContainer
	ip   string
	port string
}

func newWebProxyContainer(p webProxyParam) (*webProxyContainer, error) {
	sc, err := newServiceContainer(p.engine, p.name, p.image, p.network, p.bridge, p.ip)
	if err != nil {
		return nil, err
	}
	sc.jail.AddBindMount(p.confSource, p.confTarget)
	return &webProxyContainer{serviceContainer: sc, ip: p.ip, port: p.port}, nil
}

func (w *webProxyContainer) getURL() string { return w.ip + ":" + w.port }
