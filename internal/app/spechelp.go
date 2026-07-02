package app

import (
	"path/filepath"

	"github.com/metux/flyingtux/internal/pkg"
	"github.com/metux/flyingtux/internal/spec"
	"github.com/metux/flyingtux/internal/util"
)

// baseName mirrors os.path.basename usage for volume names.
func baseName(p string) string { return filepath.Base(p) }

// archList returns a spec's supported architectures (BaseSpec.get_arch_list).
func archList(s *spec.SpecObj) []string { return s.GetStrList("arch") }

// osbaseRepos builds the repo set of an osbase spec (OSBaseSpec.get_repos).
func osbaseRepos(osb *spec.SpecObj) pkg.Repos {
	k := osb.GetStr("DATADIR") + "/keys/"
	var keys []string
	for _, x := range osb.GetStrList("repos::keys") {
		keys = append(keys, k+util.CleanPath(x))
	}
	return pkg.Repos{Keys: keys, URLs: osb.GetStrList("repos::urls")}
}

// imageRepos merges the osbase repos with the image's own (ImageSpec.get_repos).
func imageRepos(image *spec.SpecObj) pkg.Repos {
	r := osbaseRepos(image.Sub("OSBASE"))
	k := image.GetStr("DATADIR") + "/keys/"
	keys := append([]string{}, r.Keys...)
	for _, x := range image.GetStrList("rootfs::repos::keys") {
		keys = append(keys, k+util.CleanPath(x))
	}
	urls := append(append([]string{}, r.URLs...), image.GetStrList("rootfs::repos::urls")...)
	return pkg.Repos{Keys: keys, URLs: urls}
}

// mergeList concatenates the OSBASE:: and rootfs:: variants of a list key
// (ImageSpec.__mergelist).
func mergeList(image *spec.SpecObj, name string) []string {
	return append(image.GetStrList(spec.Key("OSBASE::"+name)),
		image.GetStrList(spec.Key("rootfs::"+name))...)
}

func purgedLocales(image *spec.SpecObj) []string {
	localeDirs := mergeList(image, "post-clean::locale-dirs")
	removeLocales := mergeList(image, "post-clean::remove-locales")
	var r []string
	for _, ld := range localeDirs {
		for _, rl := range removeLocales {
			r = append(r, ld+"/"+rl)
		}
	}
	return r
}

func purgedFiles(image *spec.SpecObj) []string {
	return append(purgedLocales(image), mergeList(image, "post-clean::remove")...)
}

func emptyDirs(image *spec.SpecObj) []string {
	return mergeList(image, "post-clean::empty-dirs")
}

func contains(list []string, v string) bool {
	for _, x := range list {
		if x == v {
			return true
		}
	}
	return false
}
