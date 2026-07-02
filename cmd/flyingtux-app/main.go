// Command flyingtux-app is the Go port of the flyingtux imagebuilder CLI
// (build | run | deploy | exec | startup). Port of src/imagebuilder/flyingtux-app
// + flyingtux.cmd.
package main

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"

	"github.com/metux/flyingtux/internal/app"
	"github.com/metux/flyingtux/internal/dockercli"
	"github.com/metux/flyingtux/internal/log"
	"github.com/metux/flyingtux/internal/util"
)

func main() {
	os.Exit(run(os.Args))
}

func run(args []string) int {
	// Config path: $FLYINGTUX_TARGET, else <exedir>/cf/target.yml (as the
	// Python entry point derived it relative to the executable).
	conf := os.Getenv("FLYINGTUX_TARGET")
	exe, _ := os.Executable()
	if conf == "" {
		dir := filepath.Dir(exe)
		_ = os.Chdir(dir)
		conf = dir + "/cf/target.yml"
	}

	t, err := app.LoadTarget(conf)
	if err != nil {
		log.Err("failed loading target: " + err.Error())
		return 1
	}
	t.SetCodebase(exe)

	defer dockercli.RunCleanups()

	code, err := dispatch(t, args)
	if err != nil {
		var fe *util.FTError
		if errors.As(err, &fe) {
			log.Err(fe.Error())
			return 127
		}
		log.Err(err.Error())
		return 1
	}
	return code
}

func dispatch(t *app.Target, args []string) (int, error) {
	if len(args) < 2 {
		return usage(args), nil
	}
	rest := args[2:]

	switch args[1] {
	case "build":
		if len(rest) < 1 {
			fmt.Printf("%s build <package>\n", args[0])
			return 1, nil
		}
		b, err := t.GetBuilder(rest[0])
		if err != nil {
			return 0, err
		}
		return b.Run()

	case "run":
		if len(rest) < 1 {
			fmt.Printf("%s run <package>\n", args[0])
			return 1, nil
		}
		r, err := t.GetRunner(rest[0])
		if err != nil {
			return 0, err
		}
		return r.Run(rest[1:])

	case "deploy":
		if len(rest) < 1 {
			fmt.Printf("%s deploy <package>\n", args[0])
			return 1, nil
		}
		d, err := t.GetDeploy(rest[0])
		if err != nil {
			return 0, err
		}
		if _, err := d.Run(); err != nil {
			return 0, err
		}
		r, err := t.GetRunner(rest[0])
		if err != nil {
			return 0, err
		}
		return 0, r.Configure()

	case "exec":
		if len(rest) < 2 {
			fmt.Printf("%s exec <image> <args>\n", args[0])
			return 1, nil
		}
		r, err := t.GetRunner(rest[0])
		if err != nil {
			return 0, err
		}
		// NOTE: matches the Python arg slicing (execute(args[1:]) after
		// img=args[0], args=args[1:]) — i.e. rest[2:].
		return r.Execute(rest[2:])

	case "startup":
		t.StartNetwork()
		return 0, nil

	default:
		return usage(args), nil
	}
}

func usage(args []string) int {
	prog := "flyingtux-app"
	if len(args) > 0 {
		prog = args[0]
	}
	fmt.Printf("%s [build|deploy|run|exec|startup] <package> [args...]\n", prog)
	return 1
}
