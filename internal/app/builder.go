package app

import (
	"github.com/metux/flyingtux/internal/buildjail"
	"github.com/metux/flyingtux/internal/fs"
	"github.com/metux/flyingtux/internal/pkg"
	"github.com/metux/flyingtux/internal/spec"
)

// Builder assembles an image (port of app.builder.Builder).
type Builder struct {
	toolBase
	image    *spec.SpecObj
	platform *spec.SpecObj
	jail     buildjail.BuildJail
	pkg      pkg.Pkg
}

// Run performs the full image build (port of Builder.run).
func (b *Builder) Run() (int, error) {
	platform := b.Sub("PLATFORM")
	image := b.Sub("IMAGE")
	osbase := image.Sub("OSBASE")

	// object fixups: make ${PLATFORM::..} resolvable within image/osbase
	image.SetEntry("PLATFORM", platform.Entry)
	osbase.SetEntry("PLATFORM", platform.Entry)

	b.info("initializing build jail")
	buildTemp := b.GetStr("BUILD-TEMP")
	_ = fs.Rmtree(buildTemp)

	jailEngine := b.GetStr("TARGET::jail-engine")
	jail, err := buildjail.Get(buildjail.Params{
		RootfsImage: b.GetStr("ROOTFS-IMAGE"),
		Workdir:     buildTemp,
		Engine:      jailEngine,
		ConfImage:   osbase.GetStr(spec.Key("build-jail::" + jailEngine + "::image")),
		ConfInit:    osbase.GetStr(spec.Key("build-jail::" + jailEngine + "::init")),
	})
	if err != nil {
		return 0, err
	}
	b.jail = jail

	p, err := pkg.Get(osbase.GetStr("engine"), b.GetStr("ARCH"), jail)
	if err != nil {
		return 0, err
	}
	b.pkg = p

	b.info("preparing image")
	if err := p.Prepare(); err != nil {
		return 0, err
	}

	b.info("adding repos")
	r := imageRepos(image)
	if err := p.AddRepos(&pkg.Repos{URLs: r.URLs, Keys: r.Keys}); err != nil {
		return 0, err
	}

	b.info("copying base files")
	for _, e := range osbase.SubElems("rootfs::copy-files") {
		ent := spec.Wrap(e)
		if err := jail.SysrootCopyFile(ent.GetStr("source"), ent.GetStr("dest"), ent.GetStr("mode"), ent.GetStr("owner")); err != nil {
			return 0, err
		}
	}

	if err := jail.SysrootCreateDirs(append(
		osbase.GetStrList("rootfs::create-dirs"),
		image.GetStrList("rootfs::create-dirs")...)); err != nil {
		return 0, err
	}

	for _, e := range image.SubElems("rootfs::create-links") {
		ent := spec.Wrap(e)
		if err := jail.SysrootSymlink(ent.GetStr("name"), ent.GetStr("target")); err != nil {
			return 0, err
		}
	}

	b.info("adding os components")
	if err := b.doOSComponents(image.GetStrList("rootfs::os-components"), osbase); err != nil {
		return 0, err
	}

	b.info("installing application packages")
	if err := p.AddPackages(image.GetStrList("rootfs::packages")); err != nil {
		return 0, err
	}

	b.info("cleaning up")
	if err := jail.SysrootRemoveRecursive(purgedFiles(image)); err != nil {
		return 0, err
	}
	if err := jail.SysrootRemoveDirs(emptyDirs(image)); err != nil {
		return 0, err
	}

	b.info("finishing image")
	if err := p.Finish(); err != nil {
		return 0, err
	}

	b.info("cleaning working directory: " + buildTemp)
	_ = fs.Rmtree(buildTemp)

	b.info("image build done")
	return 0, nil
}

// doOSComponents processes a list of osbase components recursively (port of
// __do_os_components).
func (b *Builder) doOSComponents(names []string, osbase *spec.SpecObj) error {
	for _, name := range names {
		key := spec.Key("components::" + name)
		if !osbase.Has(key) {
			return b.abort("missing os component " + name + " needed by image")
		}
		b.info("processing component: " + name)
		if err := b.doSingleComponent(name, osbase.Sub(key), osbase); err != nil {
			return err
		}
	}
	return nil
}

// doSingleComponent installs a component's packages and selected choice (port
// of __do_single_os_component).
func (b *Builder) doSingleComponent(name string, comp, osbase *spec.SpecObj) error {
	if err := b.doOSComponents(comp.GetStrList("depends"), osbase); err != nil {
		return err
	}

	if pkgs := comp.GetStrList("packages"); len(pkgs) > 0 {
		b.info("osbase component " + name + ": installing packages")
		if err := b.pkg.AddPackages(pkgs); err != nil {
			return err
		}
	}

	selector := comp.GetStr("selector")
	if selector == "" {
		return nil
	}

	choiceKey := spec.Key("choice::" + selector)
	var choice *spec.SpecObj
	if comp.Has(choiceKey) {
		choice = comp.Sub(choiceKey)
	} else if comp.Has("default") {
		b.info("osbase component " + name + ": cant find choice " + selector + " - using default")
		choice = comp.Sub("default")
	} else {
		b.info("osbase component " + name + " has no default choice")
		return nil
	}

	if pkgs := choice.GetStrList("packages"); len(pkgs) > 0 {
		b.info("osbase component " + name + " choice: installing packages")
		if err := b.pkg.AddPackages(pkgs); err != nil {
			return err
		}
	}
	return nil
}

func (b *Builder) abort(text string) error {
	return &abortErr{b.toolname + ": " + text}
}

type abortErr struct{ msg string }

func (e *abortErr) Error() string { return e.msg }
