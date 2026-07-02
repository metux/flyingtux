// SPDX-License-Identifier: AGPL-3.0-or-later

// Package log provides colored logging with microsecond inter-message timing,
// a faithful port of the Python metux.util.log module.
package log

import (
	"fmt"
	"os"
	"sync"
	"time"
)

const (
	colorNormal = "\033[0;32;39m"
	colorYellow = "\033[1;32;33m"
	colorGreen  = "\033[1;32;40m"
	colorCyan   = "\033[1;32;36m"
	colorRed    = "\033[1;32;91m"
)

var (
	mu       sync.Mutex
	lastTime = time.Now()
)

func wr(prefix, color, text string) {
	mu.Lock()
	defer mu.Unlock()
	now := time.Now()
	diff := now.Sub(lastTime).Microseconds()
	fmt.Fprintf(os.Stderr, "%s%5s%s [%8d] %s\n", color, prefix, colorNormal, diff, text)
	lastTime = now
}

func Info(text string)  { wr("INFO:", colorGreen, text) }
func Warn(text string)  { wr("WARN:", colorYellow, text) }
func Err(text string)   { wr("ERR:", colorRed, text) }
func Debug(text string) { wr("DBG:", colorCyan, text) }

func Infof(format string, a ...any)  { Info(fmt.Sprintf(format, a...)) }
func Warnf(format string, a ...any)  { Warn(fmt.Sprintf(format, a...)) }
func Errf(format string, a ...any)   { Err(fmt.Sprintf(format, a...)) }
func Debugf(format string, a ...any) { Debug(fmt.Sprintf(format, a...)) }
