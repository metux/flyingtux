// SPDX-License-Identifier: AGPL-3.0-or-later

package app

import (
	"os"
	"strings"

	"github.com/metux/flyingtux/internal/spec"
	"github.com/metux/flyingtux/internal/util"
)

// Target is the top-level config object (port of flyingtux.target.Target).
type Target struct {
	*spec.SpecObj
	objcache map[string]*spec.SpecObj
	ipmap    *util.IpAddrMap
}

// LoadTarget loads the target config file and wires up ENV/USER defaults
// (port of target.get + Target.post_init).
func LoadTarget(conffile string) (*Target, error) {
	s, err := spec.Load(conffile)
	if err != nil {
		return nil, err
	}
	t := &Target{SpecObj: s, objcache: map[string]*spec.SpecObj{}}

	for _, kv := range os.Environ() {
		if i := strings.IndexByte(kv, '='); i >= 0 {
			t.SetDefaultStr(spec.Key("ENV::"+kv[:i]), kv[i+1:])
		}
	}
	t.SetDefaultStr("USER::uid", util.Uid())
	t.SetDefaultStr("USER::gid", util.Gid())
	t.SetDefaultStr("USER::home", util.HomeDir())
	t.SetDefaultStr("USER::cwd", util.Cwd())
	return t, nil
}

// SetCodebase records the path used by generated per-app launcher scripts.
func (t *Target) SetCodebase(path string) { t.SetStr("CODEBASE", path) }

// loadObject loads and caches a spec object of the given type/name, wiring in
// OSBASE for images (port of Target.load_object).
func (t *Target) loadObject(typ, name string) (*spec.SpecObj, error) {
	datadir := t.GetStr("configdir") + "/" + typ + "/" + name
	cf := datadir + "/info.yml"
	if o, ok := t.objcache[cf]; ok {
		return o, nil
	}
	o, err := spec.Load(cf)
	if err != nil {
		return nil, err
	}
	o.SetStr("DATADIR", datadir)
	o.SetStr("NAME", name)
	if typ == "image" {
		o.SetDefaultStr("user", "app") // ImageSpec.post_init
		osb, err := t.loadObject("osbase", o.GetStr("rootfs::osbase"))
		if err != nil {
			return nil, err
		}
		o.SetEntry("OSBASE", osb.Entry)
	}
	t.objcache[cf] = o
	return o, nil
}

// computeArch auto-selects or validates the architecture (port of
// Target.compute_arch), storing it as the ARCH default on the tool spec.
func (t *Target) computeArch(root, image, platform *spec.SpecObj) error {
	platformArch := archList(platform)
	osbaseArch := archList(image.Sub("OSBASE"))
	requested := root.GetStr("arch")

	if requested == "" {
		for _, pa := range platformArch {
			if contains(osbaseArch, pa) {
				root.SetDefaultStr("ARCH", pa)
				return nil
			}
		}
		return util.ConfigError("failed finding matching arch for platform and osbase")
	}
	if !contains(platformArch, requested) {
		return util.ConfigError("requested arch %s not supported by platform", requested)
	}
	if !contains(osbaseArch, requested) {
		return util.ConfigError("requested arch %s not supported by osbase", requested)
	}
	root.SetDefaultStr("ARCH", requested)
	return nil
}

// buildToolSpec assembles the shared tool spec tree (IMAGE/PLATFORM/TARGET/
// ROOTFS-IMAGE + computed ARCH), port of Target.get_tool.
func (t *Target) buildToolSpec(imgName string) (root, image, platform *spec.SpecObj, err error) {
	image, err = t.loadObject("image", imgName)
	if err != nil {
		return nil, nil, nil, err
	}
	platform, err = t.loadObject("platform", t.GetStr("platform"))
	if err != nil {
		return nil, nil, nil, err
	}
	root = spec.NewRoot()
	root.SetEntry("IMAGE", image.Entry)
	root.SetEntry("PLATFORM", platform.Entry)
	root.SetEntry("TARGET", t.Entry)
	root.SetStr("ROOTFS-IMAGE", "flyingtux-app-${IMAGE::NAME}-${ARCH}:${IMAGE::version}")
	if err = t.computeArch(root, image, platform); err != nil {
		return nil, nil, nil, err
	}
	return root, image, platform, nil
}

// GetBuilder returns a Builder for the image (port of Target.get_builder).
func (t *Target) GetBuilder(imgName string) (*Builder, error) {
	root, image, platform, err := t.buildToolSpec(imgName)
	if err != nil {
		return nil, err
	}
	root.SetStr("BUILD-TEMP", t.GetStr("build-temp")+"/${IMAGE::NAME}-${IMAGE::version}.${ARCH}")
	return &Builder{
		toolBase: toolBase{SpecObj: root, toolname: "Builder", target: t},
		image:    image,
		platform: platform,
	}, nil
}

// GetDeploy returns a Deploy tool for the image (port of Target.get_deploy).
func (t *Target) GetDeploy(imgName string) (*Deploy, error) {
	root, image, _, err := t.buildToolSpec(imgName)
	if err != nil {
		return nil, err
	}
	return &Deploy{
		toolBase: toolBase{SpecObj: root, toolname: "Deploy", target: t},
		image:    image,
	}, nil
}

// GetRunner loads a deployed app's runner (port of Target.get_runner).
func (t *Target) GetRunner(imgName string) (*Runner, error) {
	s, err := spec.Load(t.GetStr("deploy-app-dir") + "/" + imgName + "/info.yml")
	if err != nil {
		return nil, err
	}
	s.SetEntry("TARGET", t.Entry)
	s.SetStr("APP-BASE-DIR", t.GetStr("app-base-dir")+"/"+imgName)
	s.SetStr("APP-VOLUME-DIR", "${APP-BASE-DIR}/volumes")
	s.SetStr("APP-CACHE-DIR", "${APP-BASE-DIR}/cache")
	s.SetStr("APP-SERVICE-DIR", "${APP-BASE-DIR}/services")
	return &Runner{
		toolBase: toolBase{SpecObj: s, toolname: "Runner", target: t},
	}, nil
}

// StartNetwork creates the app network (port of Target.start_network). Errors
// are ignored, as in the original.
func (t *Target) StartNetwork() {
	c, err := containerForEngine(t.GetStr("jail-engine"))
	if err != nil {
		return
	}
	c.NetworkCreate(
		t.GetStr("jail-network::name"),
		t.GetStr("jail-network::name"),
		"",
		true,
		t.GetStr("jail-network::subnet"),
		t.GetStr("jail-network::ip-range"),
	)
}

// GetAppIPAddr returns the container IP for an app (port of get_app_ipaddr).
func (t *Target) GetAppIPAddr(name string) (string, error) {
	return t.getContainerIP("app@" + name)
}

func (t *Target) getContainerIP(name string) (string, error) {
	if t.ipmap == nil {
		reserved := map[string]string{}
		for k, v := range t.GetStrMap("jail-network::reserved-ip") {
			reserved[string(k)] = v
		}
		t.ipmap = util.NewIpAddrMap(
			t.GetStr("dynconf-dir")+"/ip-map.yml",
			t.GetStr("jail-network::ip-range"),
			reserved,
		)
	}
	return t.ipmap.GetIP(name)
}
