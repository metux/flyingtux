package app

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestDeployChromium drives the full docker-free path: load target, chain
// image->osbase + platform, compute arch, resolve cross-object ${..}, run
// service get_conf, and serialize the deployment descriptor.
func TestDeployChromium(t *testing.T) {
	specDir, err := filepath.Abs("../../example/spec")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(specDir + "/image/chromium/info.yml"); err != nil {
		t.Skipf("example specs not present: %v", err)
	}

	work := t.TempDir()
	targetFile := filepath.Join(work, "target.yml")
	targetYaml := fmt.Sprintf(`platform: toshiba-portege
configdir: %s
workdir: %s/work
build-temp: %s/work/temp
deploy-app-dir: %s/work/deploy/app
deploy-dir: %s/work/deploy
dynconf-dir: %s/work/deploy/conf
app-base-dir: %s/work/apps
jail-engine: docker
jail-network:
    name: flyingtux-app
    bridge: bridge
    ip-range: 172.66.0.0/16
    subnet: 172.66.0.0/16
    reserved-ip:
        net: 172.66.0.0
        gw: 172.66.0.1
        proxy: 172.66.0.2
web-proxy:
    ip: ${jail-network::reserved-ip::proxy}
    port: 3128
    image: flyingtux-sys-squid
    name: flyingtux-sys-squid
    conf-source: %s/work/deploy/squid
    conf-target: /etc/squid/app.d
`, specDir, work, work, work, work, work, work, work)

	if err := os.WriteFile(targetFile, []byte(targetYaml), 0o644); err != nil {
		t.Fatal(err)
	}

	tgt, err := LoadTarget(targetFile)
	if err != nil {
		t.Fatalf("LoadTarget: %v", err)
	}
	tgt.SetCodebase("/opt/flyingtux/flyingtux-app")

	d, err := tgt.GetDeploy("chromium")
	if err != nil {
		t.Fatalf("GetDeploy: %v", err)
	}
	if _, err := d.Run(); err != nil {
		t.Fatalf("Deploy.Run: %v", err)
	}

	// deployment descriptor
	info, err := os.ReadFile(filepath.Join(work, "work/deploy/app/chromium/info.yml"))
	if err != nil {
		t.Fatalf("read info.yml: %v", err)
	}
	got := string(info)
	for _, want := range []string{
		"flyingtux-app-chromium_92.0.4515.107-r0",           // container name
		"x86_64",                                             // auto-selected arch
		"flyingtux-app-chromium-x86_64:92.0.4515.107-r0",    // resolved ROOTFS-IMAGE
		"x11",                                                // os-services materialized
		"user: app",                                         // ImageSpec.post_init default
	} {
		if !strings.Contains(got, want) {
			t.Errorf("info.yml missing %q\n---\n%s", want, got)
		}
	}

	// round-trip: the descriptor must reload as a bare dict (no "entry:" wrap),
	// so top-level keys resolve.
	r, err := tgt.GetRunner("chromium")
	if err != nil {
		t.Fatalf("GetRunner: %v", err)
	}
	if got := r.GetStr("engine"); got != "docker" {
		t.Errorf("reloaded engine = %q, want docker (round-trip/serialization broken)", got)
	}
	if got := r.GetStr("name"); got != "flyingtux-app-chromium_92.0.4515.107-r0" {
		t.Errorf("reloaded name = %q", got)
	}

	// launcher script
	script, err := os.ReadFile(filepath.Join(work, "work/bin/chromium"))
	if err != nil {
		t.Fatalf("read launcher: %v", err)
	}
	if !strings.Contains(string(script), "run") || !strings.Contains(string(script), "chromium") {
		t.Errorf("launcher script unexpected:\n%s", script)
	}
}
