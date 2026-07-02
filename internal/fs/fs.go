// SPDX-License-Identifier: AGPL-3.0-or-later

// Package fs provides the small filesystem helpers ported from the Python
// metux.util.fs module.
package fs

import (
	"os"
	"os/exec"
	"path/filepath"
)

// Mkdir creates a directory (and parents), ignoring an already-existing target.
func Mkdir(dirname string) error {
	return os.MkdirAll(dirname, 0o755)
}

// Rmtree recursively removes a directory tree (via `rm -Rf`, as the original).
func Rmtree(dirname string) error {
	abs, err := filepath.Abs(dirname)
	if err != nil {
		return err
	}
	return exec.Command("rm", "-Rf", abs).Run()
}
