package spec

import "testing"

// TestLoadTargetExample proves the magicdict-backed config core loads a real
// flyingtux descriptor, resolves "::" paths, and performs lazy ${..}
// substitution (web-proxy::ip references jail-network::reserved-ip::proxy).
func TestLoadTargetExample(t *testing.T) {
	s, err := Load("../../example/spec/target.yml")
	if err != nil {
		t.Fatalf("load target.yml: %v", err)
	}

	cases := []struct {
		key  Key
		want string
	}{
		{"platform", "toshiba-portege"},
		{"jail-engine", "docker"},
		{"jail-network::subnet", "172.66.0.0/16"},
		{"jail-network::reserved-ip::proxy", "172.66.0.2"},
		{"web-proxy::port", "3128"},
		// substitution: ${jail-network::reserved-ip::proxy}
		{"web-proxy::ip", "172.66.0.2"},
	}
	for _, c := range cases {
		if got := s.GetStr(c.key); got != c.want {
			t.Errorf("GetStr(%q) = %q, want %q", c.key, got, c.want)
		}
	}
}
