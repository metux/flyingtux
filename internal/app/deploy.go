package app

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/metux/flyingtux/internal/fs"
	"github.com/metux/flyingtux/internal/services"
	"github.com/metux/flyingtux/internal/spec"
	"github.com/metux/flyingtux/internal/util"
)

// Deploy generates an app's deployment descriptor + launcher script (port of
// app.deploy.Deploy).
type Deploy struct {
	toolBase
	image *spec.SpecObj
}

// Run writes the deployment descriptor and the launcher script.
func (d *Deploy) Run() (int, error) {
	if err := d.createDeploy(); err != nil {
		return 0, err
	}
	if err := d.createScript(); err != nil {
		return 0, err
	}
	return 0, nil
}

func (d *Deploy) deployFile() string {
	return d.GetStr("TARGET::deploy-app-dir") + "/" + d.GetStr("IMAGE::NAME") + "/info.yml"
}

func (d *Deploy) createDeploy() error {
	image := d.image
	d.info("deploying " + image.GetStr("NAME"))
	deployFile := d.deployFile()
	if err := fs.Mkdir(filepath.Dir(deployFile)); err != nil {
		return err
	}

	dep := spec.NewRoot()
	if _, err := os.Stat(deployFile); err == nil {
		d.info("already deployed: " + deployFile)
		if existing, err := spec.Load(deployFile); err == nil {
			dep = existing
		}
	} else {
		d.info("creating new deployment: " + deployFile)
	}

	dep.SetStr("image", image.GetStr("NAME"))
	dep.SetStr("name", util.AppContainerName(image.GetStr("NAME"), image.GetStr("version")))
	dep.SetStr("version", image.GetStr("version"))
	dep.SetEntry("os-services", image.GetEntry("os-services"))
	dep.SetStr("arch", d.GetStr("ARCH"))
	dep.SetStr("platform", d.GetStr("PLATFORM::NAME"))
	dep.SetStr("engine", d.GetStr("TARGET::jail-engine"))
	dep.SetEntry("command", image.GetEntry("command"))
	dep.SetStr("rootfs-image", d.GetStr("ROOTFS-IMAGE"))

	// NOTE: the Python used 'IMAGE::OSBASE::tmpdirs' here, which resolves to
	// empty (image has no IMAGE key); replicated verbatim for parity.
	tmpdirs := append(image.GetStrList("rootfs::tmpdirs"),
		image.GetStrList("IMAGE::OSBASE::tmpdirs")...)
	for _, t := range tmpdirs {
		dep.AppendStr("tmpdirs", t)
	}

	dep.SetStr("user", image.GetStr("user"))
	dep.SetEntry("volumes", image.GetEntry("volumes"))

	for _, name := range image.SubKeys("os-services") {
		sspec := image.Sub(spec.Key("os-services::" + string(name)))
		svc, err := services.GetService(string(name), sspec, d)
		if err != nil {
			return err
		}
		conf, err := svc.GetConf()
		if err != nil {
			return err
		}
		dep.SetEntry(spec.Key("os-services::"+string(name)), conf.Entry)
	}

	return spec.Store(deployFile, dep, 0o644)
}

func (d *Deploy) createScript() error {
	scriptdir := d.GetStr("TARGET::workdir") + "/bin"
	name := d.GetStr("IMAGE::NAME")
	codebase := d.GetStr("TARGET::CODEBASE")
	scriptname := scriptdir + "/" + name
	if err := fs.Mkdir(scriptdir); err != nil {
		return err
	}
	script := fmt.Sprintf("#!/bin/sh\nexec %q run %q \"$@\"\n", codebase, name)
	if err := os.WriteFile(scriptname, []byte(script), 0o755); err != nil {
		return err
	}
	return os.Chmod(scriptname, 0o755)
}

// --- services.Runner (deploy only needs Get; the rest are unused in GetConf) ---

func (d *Deploy) Get(key string) string         { return d.GetStr(spec.Key(key)) }
func (d *Deploy) IPAddress() string             { return "" }
func (d *Deploy) StartWebProxy() (string, error) { return "", util.Error("web proxy not available at deploy time") }
