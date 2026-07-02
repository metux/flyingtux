// SPDX-License-Identifier: AGPL-3.0-or-later

package services

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/metux/flyingtux/internal/fs"
	"github.com/metux/flyingtux/internal/spec"
)

// webProxy configures a per-app squid web proxy and its ACL. Port of
// services/webproxy.py.
type webProxy struct {
	base
	appname string
}

func newWebProxy(sp *spec.SpecObj, r Runner) Service {
	s := &webProxy{base: base{name: "WebProxy", spec: sp, runner: r}}
	s.self = s
	s.init()
	return s
}

func (s *webProxy) compute() error {
	s.appname = s.appName()
	proxy, err := s.runner.StartWebProxy()
	if err != nil {
		return err
	}
	s.info("web proxy is: " + proxy)
	s.addEnv("http_proxy", proxy)
	s.addEnv("https_proxy", proxy)
	s.addEnv("ftp_proxy", proxy)
	return s.writeACL(s.runner.Get("TARGET::web-proxy::conf-source") + "/" + s.appname + ".conf")
}

func (s *webProxy) writeACL(fn string) error {
	aclIP := s.appname + "_ip"
	if err := fs.Mkdir(filepath.Dir(fn)); err != nil {
		return err
	}
	f, err := os.Create(fn)
	if err != nil {
		return err
	}
	defer f.Close()

	fmt.Fprintf(f, "acl %s src %s\n", aclIP, s.runner.IPAddress())
	for cnt, wl := range s.spec.GetStrList("whitelist") {
		aclURL := fmt.Sprintf("%s_wl%d", s.appname, cnt)
		fmt.Fprintf(f, "acl %s url_regex %s\n", aclURL, wl)
		fmt.Fprintf(f, "http_access allow %s %s\n", aclIP, aclURL)
	}
	return nil
}
