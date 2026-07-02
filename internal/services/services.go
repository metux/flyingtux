// SPDX-License-Identifier: AGPL-3.0-or-later

// Package services implements the pluggable OS services (x11, devices, user
// dirs, web proxy, ...) that configure an app container's mounts, env, tmpfs,
// options and devices (port of flyingtux.services).
package services

import (
	"github.com/metux/flyingtux/internal/log"
	"github.com/metux/flyingtux/internal/spec"
	"github.com/metux/flyingtux/internal/util"
)

// Mount is a container bind mount.
type Mount struct {
	Type   string
	Source string
	Target string
}

// Opts are the container options a service can request. Empty string / false
// means "unset".
type Opts struct {
	IPC      string
	User     string
	Name     string
	ReadOnly bool
}

// Result is what a processed service contributes to the container config
// (the dict returned by Base.process).
type Result struct {
	Mounts   []Mount
	Env      map[string]string
	Tempdirs []string
	Opts     Opts
	Devices  []string
}

// Runner is the subset of the app runner that services rely on (breaks the
// app<->services import cycle). Get resolves a "::"-path string on the runner
// spec (image, APP-*, TARGET::...).
type Runner interface {
	Get(key string) string
	IPAddress() string
	StartWebProxy() (string, error)
}

// Service is a constructed OS service.
type Service interface {
	Process() (*Result, error)
	GetConf() (*spec.SpecObj, error)
}

// svc is the internal per-service compute hook (Go has no virtual dispatch, so
// Base dispatches through the concrete instance stored in base.self).
type svc interface {
	compute() error
}

// base carries the shared service state and helpers (port of os_service.Base).
type base struct {
	self     svc
	name     string // class-ish name, for logging
	spec     *spec.SpecObj
	runner   Runner
	permDflt map[string]bool
	setDflt  map[string]string
	tempDirs []string // static temp_dirs

	srvEnv      map[string]string
	srvMounts   []Mount
	srvTempdirs []string
	opts        Opts
	devices     []string
}

func (b *base) init() {
	if b.srvEnv == nil {
		b.srvEnv = map[string]string{}
	}
	b.applyDefaults()
}

// applyDefaults materializes permission/setting defaults into the spec if
// absent (mirrors get_conf's default loops; harmless at runtime, needed at
// deploy time for serialization).
func (b *base) applyDefaults() {
	if b.permDflt == nil {
		b.permDflt = map[string]bool{"__enabled__": true}
	}
	for k, v := range b.permDflt {
		key := spec.Key("permissions::" + k)
		if !b.spec.Has(key) {
			b.spec.SetBool(key, v)
		}
	}
	for k, v := range b.setDflt {
		key := spec.Key("settings::" + k)
		if !b.spec.Has(key) {
			b.spec.SetStr(key, v)
		}
	}
}

func (b *base) appName() string { return b.runner.Get("image") }

func (b *base) isPermitted(perm string) bool {
	dflt := true
	if d, ok := b.permDflt[perm]; ok {
		dflt = d
	}
	return b.spec.GetBool(spec.Key("permissions::"+perm), dflt)
}

func (b *base) getSetting(name string) string {
	return b.spec.GetStr(spec.Key("settings::" + name))
}

func (b *base) addEnv(name, val string)         { b.srvEnv[name] = val }
func (b *base) addTempdirs(dirs []string)       { b.srvTempdirs = append(b.srvTempdirs, dirs...) }
func (b *base) addDevice(name string)           { b.devices = append(b.devices, name) }
func (b *base) setContainerOpt(set func(*Opts)) { set(&b.opts) }

func (b *base) bindFileDirect(fn string) {
	b.srvMounts = append(b.srvMounts, Mount{Type: "bind", Source: fn, Target: fn})
}

func (b *base) bindDir(source, target string) {
	b.srvMounts = append(b.srvMounts, Mount{Type: "bind", Source: source, Target: target})
}

func (b *base) bindUserDir(src, dst string) {
	home := util.HomeDir()
	b.srvMounts = append(b.srvMounts, Mount{Type: "bind", Source: home + "/" + src, Target: "/home/app/" + dst})
}

func (b *base) info(msg string) { log.Infof("os-service %s: %s", b.name, msg) }

// compute is a no-op by default (services with only static temp_dirs).
func (b *base) compute() error { return nil }

// Process runs the service and returns its container contribution.
func (b *base) Process() (*Result, error) {
	b.addTempdirs(b.tempDirs)
	if b.isPermitted("__enabled__") {
		b.info("enabled")
		if err := b.self.compute(); err != nil {
			return nil, err
		}
	} else {
		b.info("disabled")
	}
	return &Result{
		Mounts:   b.srvMounts,
		Env:      b.srvEnv,
		Tempdirs: b.srvTempdirs,
		Opts:     b.opts,
		Devices:  b.devices,
	}, nil
}

// GetConf returns the service spec with defaults materialized (for deploy).
func (b *base) GetConf() (*spec.SpecObj, error) {
	b.applyDefaults()
	b.spec.SetBool("initialized", true)
	return b.spec, nil
}
