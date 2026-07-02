// SPDX-License-Identifier: AGPL-3.0-or-later

package util

import (
	"net"
	"os"

	"gopkg.in/yaml.v3"
)

// Bimap is a bidirectional string map (name<->ip), ported from the Python
// flyingtux.util.bimap. Setting a key removes any prior mapping of either the
// key or the value, keeping both directions consistent.
type Bimap struct {
	forward map[string]string
	inverse map[string]string
}

func NewBimap() *Bimap {
	return &Bimap{forward: map[string]string{}, inverse: map[string]string{}}
}

func (b *Bimap) Get(k string) (string, bool) { v, ok := b.forward[k]; return v, ok }

func (b *Bimap) HasVal(v string) bool { _, ok := b.inverse[v]; return ok }

func (b *Bimap) Set(k, v string) {
	if old, ok := b.forward[k]; ok {
		delete(b.inverse, old)
	}
	if oldk, ok := b.inverse[v]; ok {
		delete(b.forward, oldk)
	}
	b.forward[k] = v
	b.inverse[v] = k
}

func loadBimapYaml(fn string) *Bimap {
	b := NewBimap()
	data, err := os.ReadFile(fn)
	if err != nil {
		return b
	}
	m := map[string]string{}
	if yaml.Unmarshal(data, &m) != nil {
		return b
	}
	for k, v := range m {
		b.Set(k, v)
	}
	return b
}

func storeBimapYaml(b *Bimap, fn string) error {
	data, err := yaml.Marshal(b.forward)
	if err != nil {
		return err
	}
	return os.WriteFile(fn, data, 0o644)
}

// IpAddrMap allocates and persists container IP addresses within a subnet,
// ported from flyingtux.util.IpAddrMap.
type IpAddrMap struct {
	fn     string
	subnet string
	ipmap  *Bimap
}

func NewIpAddrMap(fn, subnet string, reserved map[string]string) *IpAddrMap {
	m := &IpAddrMap{fn: fn, subnet: subnet, ipmap: loadBimapYaml(fn)}
	for k, v := range reserved {
		m.ipmap.Set(k, v)
	}
	return m
}

// GetIP returns the address already allocated for name, or allocates and
// persists a fresh one from the subnet (skipping multicast/link-local/reserved).
func (m *IpAddrMap) GetIP(name string) (string, error) {
	if v, ok := m.ipmap.Get(name); ok {
		return v, nil
	}

	_, ipnet, err := net.ParseCIDR(m.subnet)
	if err != nil {
		return "", Error("invalid subnet %q: %v", m.subnet, err)
	}

	ip := make(net.IP, len(ipnet.IP))
	copy(ip, ipnet.IP.Mask(ipnet.Mask))
	for ; ipnet.Contains(ip); incIP(ip) {
		ips := ip.String()
		if ip.IsMulticast() || ip.IsLinkLocalUnicast() || ip.IsLinkLocalMulticast() ||
			ip.IsUnspecified() || ip.IsLoopback() {
			continue
		}
		if m.ipmap.HasVal(ips) {
			continue
		}
		m.ipmap.Set(name, ips)
		if err := storeBimapYaml(m.ipmap, m.fn); err != nil {
			return "", err
		}
		return ips, nil
	}

	return "", Error("failed to allocate a new ip address for: %s", name)
}

func incIP(ip net.IP) {
	for i := len(ip) - 1; i >= 0; i-- {
		ip[i]++
		if ip[i] != 0 {
			break
		}
	}
}
