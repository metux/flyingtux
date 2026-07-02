// SPDX-License-Identifier: AGPL-3.0-or-later

package util

import (
	"os"
	"strconv"
)

// HomeDir returns the user's home directory ($HOME), matching the Python
// os.environ['HOME'] / expanduser('~') usage.
func HomeDir() string {
	if h := os.Getenv("HOME"); h != "" {
		return h
	}
	h, _ := os.UserHomeDir()
	return h
}

func Cwd() string {
	d, _ := os.Getwd()
	return d
}

func Uid() string { return strconv.Itoa(os.Getuid()) }
func Gid() string { return strconv.Itoa(os.Getgid()) }
