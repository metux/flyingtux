package services

import (
	"github.com/metux/flyingtux/internal/fs"
	"github.com/metux/flyingtux/internal/spec"
)

// simple is a service with only static temp_dirs and a no-op compute
// (TempHomedir, SysTempDir).
type simple struct{ base }

func newSimple(name string, tempdirs []string) func(*spec.SpecObj, Runner) Service {
	return func(sp *spec.SpecObj, r Runner) Service {
		s := &simple{base{name: name, spec: sp, runner: r, tempDirs: tempdirs}}
		s.self = s
		s.init()
		return s
	}
}

// serviceDir binds the app's service import/export dirs.
type serviceDir struct{ base }

func newServiceDir(sp *spec.SpecObj, r Runner) Service {
	s := &serviceDir{base{name: "ServiceDir", spec: sp, runner: r}}
	s.self = s
	s.init()
	return s
}

func (s *serviceDir) compute() error {
	dir := s.runner.Get("APP-SERVICE-DIR")
	s.bindDir(dir+"/import/", "/service/import")
	s.bindDir(dir+"/export/", "/service/export")
	return nil
}

// dataVolume mounts named data volumes from the service config.
type dataVolume struct{ base }

func newDataVolume(sp *spec.SpecObj, r Runner) Service {
	s := &dataVolume{base{name: "DataVolume", spec: sp, runner: r}}
	s.self = s
	s.init()
	return s
}

func (s *dataVolume) compute() error {
	datadir := s.runner.Get("APP-VOLUME-DIR")
	for _, e := range s.spec.SubElems("volumes") {
		v := spec.Wrap(e)
		name := v.GetStr("name")
		volumeDir := datadir + "/" + baseName(name)
		if err := fs.Mkdir(volumeDir); err != nil {
			return err
		}
		s.bindDir(volumeDir, v.GetStr("mountpoint"))
	}
	return nil
}

// dri passes through the DRI kernel device.
type dri struct{ base }

func newDri(sp *spec.SpecObj, r Runner) Service {
	s := &dri{base{name: "DriDevice", spec: sp, runner: r}}
	s.self = s
	s.init()
	return s
}

func (s *dri) compute() error {
	s.addDevice("/dev/dri/card0")
	return nil
}

// userDir maps a user home subdirectory into the container.
type userDir struct {
	base
	dirName string
	target  string
}

func newUserDir(name, dirName, target string) func(*spec.SpecObj, Runner) Service {
	return func(sp *spec.SpecObj, r Runner) Service {
		s := &userDir{
			base: base{
				name: name, spec: sp, runner: r,
				permDflt: map[string]bool{
					"__enabled__": true, "read": true, "write": true,
					"remove": true, "mkdir": true, "rmdir": true, "create": true,
				},
				setDflt: map[string]string{"name": dirName, "target": target},
			},
			dirName: dirName,
			target:  target,
		}
		s.self = s
		s.init()
		return s
	}
}

func (s *userDir) compute() error {
	s.bindUserDir(s.target, s.dirName)
	return nil
}

func baseName(p string) string {
	for i := len(p) - 1; i >= 0; i-- {
		if p[i] == '/' {
			return p[i+1:]
		}
	}
	return p
}
