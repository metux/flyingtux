// Package spec is the flyingtux configuration core. It wraps go-magicdict
// (the same recursive YAML dict with "::"-path access, lazy ${..} substitution
// and defaults that mpbt uses) and provides the typed accessors that the Python
// SpecObject base class offered.
package spec

import (
	"os"

	"github.com/metux/go-magicdict/api"
	"github.com/metux/go-magicdict/core"
	"github.com/metux/go-magicdict/magic"
)

// Key and Entry are re-exported so callers need not import the magicdict api.
type Key = api.Key
type Entry = api.Entry

// SpecObj wraps a magicdict entry. It can hold the root document (from Load)
// or any nested entry (from Wrap/Sub). Methods deliberately avoid the names in
// the api.Entry interface (Get, Keys, Elems, ...) so *SpecObj keeps satisfying
// api.Entry and can be handed straight to the api.* helpers.
type SpecObj struct {
	api.Entry
}

// Load reads a YAML file into a fresh SpecObj (mirrors SpecObject.load_spec).
func Load(fn string) (*SpecObj, error) {
	d, err := magic.YamlLoad(fn, "")
	if err != nil {
		return nil, err
	}
	return &SpecObj{d}, nil
}

// Wrap adapts an existing magicdict entry as a SpecObj.
func Wrap(e api.Entry) *SpecObj { return &SpecObj{e} }

// Store serializes a SpecObj to a YAML file (raw/unsubstituted, matching the
// Python yaml.dump of a spec).
func Store(fn string, s *SpecObj, mode os.FileMode) error {
	// Serialize the underlying entry (which implements MarshalYAML) rather than
	// the *SpecObj wrapper, otherwise yaml wraps it under an "entry:" key.
	return core.YamlStore(fn, s.Entry, mode)
}

// NewRoot creates an empty root SpecObj to assemble a spec tree in memory
// (nesting sub-specs via SetEntry) — used to build the Builder/Deploy tool
// specs the way Target.get_tool does.
func NewRoot() *SpecObj {
	return &SpecObj{magic.NewMagicFromDict(core.EmptyDict(), core.EmptyDict())}
}

// --- read accessors (SpecObject.get_cf* family) ---

func (c *SpecObj) GetStr(k Key) string             { return api.GetStr(c, k) }
func (c *SpecObj) GetStrList(k Key) []string       { return api.GetStrList(c, k) }
func (c *SpecObj) GetStrMap(k Key) map[Key]string  { return api.GetStrMap(c, k) }
func (c *SpecObj) GetBool(k Key, dflt bool) bool    { return api.GetBool(c, k, dflt) }
func (c *SpecObj) GetInt(k Key, dflt int) int       { return api.GetInt(c, k, dflt) }
func (c *SpecObj) GetEntry(k Key) Entry             { return api.GetEntry(c, k) }
func (c *SpecObj) SubKeys(k Key) api.KeyList        { return api.GetKeys(c, k) }
func (c *SpecObj) SubElems(k Key) api.EntryList     { return api.GetElems(c, k) }

// Sub returns a nested entry wrapped as a SpecObj (nil-safe: a missing key
// yields a SpecObj wrapping a nil entry, whose accessors return zero values).
func (c *SpecObj) Sub(k Key) *SpecObj { return Wrap(api.GetEntry(c, k)) }

// Has reports whether key k resolves to a present entry.
func (c *SpecObj) Has(k Key) bool { return api.GetEntry(c, k) != nil }

// --- write accessors ---

func (c *SpecObj) SetStr(k Key, v string) error        { return api.SetStr(c, k, v) }
func (c *SpecObj) SetBool(k Key, v bool) error         { return api.SetBool(c, k, v) }
func (c *SpecObj) SetInt(k Key, v int) error           { return api.SetInt(c, k, v) }
func (c *SpecObj) SetEntry(k Key, v Entry) error       { return api.SetEntry(c, k, v) }
func (c *SpecObj) AppendStr(k Key, v string) error     { return api.AppendStr(c, k, v) }
func (c *SpecObj) Delete(k Key) error                  { return api.Delete(c, k) }

func (c *SpecObj) SetDefaultStr(k Key, v string) error { return api.SetDefaultStr(c, k, v) }
func (c *SpecObj) SetDefaultInt(k Key, v int) error    { return api.SetDefaultInt(c, k, v) }
func (c *SpecObj) SetDefaultBool(k Key, v bool) error  { return api.SetDefaultBool(c, k, v) }
