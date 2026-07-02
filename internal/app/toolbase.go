// Package app is the flyingtux orchestration layer: the Target (top-level
// config) and the Builder/Deploy/Runner pipeline tools (ports of
// flyingtux.target and flyingtux.app.*).
package app

import (
	"github.com/metux/flyingtux/internal/log"
	"github.com/metux/flyingtux/internal/spec"
)

// toolBase is the shared base for the pipeline tools (port of ToolBase).
type toolBase struct {
	*spec.SpecObj
	toolname string
	target   *Target
}

func (tb *toolBase) info(text string) { log.Info(tb.toolname + ": " + text) }
