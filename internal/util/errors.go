// Package util holds the flyingtux error types and small helpers ported from
// the Python flyingtux.util and flyingtux.naming modules.
package util

import "fmt"

// ErrKind classifies an FTError, mirroring the Python FT_Error subclass
// hierarchy (FT_ConfigError, FT_UnsupportedJail, ...).
type ErrKind string

const (
	ErrGeneric         ErrKind = "error"
	ErrConfig          ErrKind = "config-error"
	ErrUnsupportedJail ErrKind = "unsupported-jail"
	ErrUnsupportedPkg  ErrKind = "unsupported-pkg"
	ErrUnsupportedTool ErrKind = "unsupported-tool"
)

// FTError is the base flyingtux error. The CLI catches it, logs the message
// and returns exit code 127 (matching run_cmd's FT_Error handler).
type FTError struct {
	Kind ErrKind
	Msg  string
}

func (e *FTError) Error() string { return e.Msg }

func newErr(kind ErrKind, format string, a ...any) *FTError {
	return &FTError{Kind: kind, Msg: fmt.Sprintf(format, a...)}
}

func Error(format string, a ...any) *FTError           { return newErr(ErrGeneric, format, a...) }
func ConfigError(format string, a ...any) *FTError     { return newErr(ErrConfig, format, a...) }
func UnsupportedJail(format string, a ...any) *FTError  { return newErr(ErrUnsupportedJail, format, a...) }
func UnsupportedPkg(format string, a ...any) *FTError   { return newErr(ErrUnsupportedPkg, format, a...) }
func UnsupportedTool(format string, a ...any) *FTError  { return newErr(ErrUnsupportedTool, format, a...) }
