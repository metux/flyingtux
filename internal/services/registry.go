// SPDX-License-Identifier: AGPL-3.0-or-later

package services

import (
	"github.com/metux/flyingtux/internal/spec"
	"github.com/metux/flyingtux/internal/util"
)

// registry maps os-service names to their constructors (port of the
// os_services dict).
var registry = map[string]func(*spec.SpecObj, Runner) Service{
	"x11":            newX11,
	"temp-homedir":   newSimple("TempHomedir", []string{"/root", "/home/app", "/tmp"}),
	"sys-tempdir":    newSimple("SysTempDir", []string{"/tmp", "/var/tmp"}),
	"user-documents": newUserDir("UserDocuments", "Documents", "Documents"),
	"user-pictures":  newUserDir("UserPictures", "Pictures", "Pictures"),
	"user-movies":    newUserDir("UserMovies", "Movies", "Movies"),
	"user-downloads": newUserDir("UserDownloads", "Downloads", "Downloads"),
	"dri":            newDri,
	"service-dir":    newServiceDir,
	"data-volume":    newDataVolume,
	"web":            newWebProxy,
}

// GetService instantiates an OS service by name (port of get_os_service).
func GetService(name string, sp *spec.SpecObj, r Runner) (Service, error) {
	ctor, ok := registry[name]
	if !ok {
		return nil, util.ConfigError("Unknown OS service: %s", name)
	}
	// A null service entry (e.g. `user-downloads:` with no sub-config) parses to
	// a nil entry; treat it as an empty spec, like SpecObject(None) in Python.
	if sp == nil || sp.Entry == nil {
		sp = spec.NewRoot()
	}
	return ctor(sp, r), nil
}

// ProcessService instantiates and processes a service (port of
// process_os_service).
func ProcessService(name string, sp *spec.SpecObj, r Runner) (*Result, error) {
	s, err := GetService(name, sp, r)
	if err != nil {
		return nil, err
	}
	return s.Process()
}
