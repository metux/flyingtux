// SPDX-License-Identifier: AGPL-3.0-or-later

package util

import (
	"fmt"
	"path/filepath"
	"strings"
)

// AppContainerName builds the runtime container name for an app image,
// ported from flyingtux.naming.app_container_name.
func AppContainerName(appname, version string) string {
	return fmt.Sprintf("flyingtux-app-%s_%s", appname, version)
}

// CleanPath normalizes a path and strips any "../" components
// (flyingtux.util.clean_path).
func CleanPath(path string) string {
	return strings.ReplaceAll(filepath.Clean(path), "../", "")
}
