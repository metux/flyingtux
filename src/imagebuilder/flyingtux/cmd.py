from sys import argv, exit
from os.path import dirname, abspath, basename
from os import chdir
from flyingtux import target
from flyingtux.app import builder
from flyingtux.util import FT_Error
from metux.util import log

def run_cmd(conf, args):
    my_target = target.get(conf)
    my_target['CODEBASE'] = dirname(dirname(abspath(__file__)))

    def errhelp():
        print("%s [build|deploy|run]" % args[0])
        exit(1)

    def cmd_run(args):
        if len(args) < 1:
            print("%s <run> <package>" % args[0])
            return 1

        return my_target.get_runner(args[0]).run(args[1:])

    def cmd_exec(args):
        if len(args) < 2:
            print("%s <run> <package>" % args[0])
            return 1

        img = args[0]
        args = args[1:]
        return my_target.get_runner(img).execute(args[1:])

    def cmd_build(args):
        if len(args) < 1:
            print("%s <build> <package>" % args[0])
            return 1

        return my_target.get_builder(args[0]).run()

    def cmd_deploy(args):
        if len(args) < 1:
            print("%s <deploy> <package>" % args[0])
            return 1

        my_target.get_deploy(args[0]).run()
        my_target.get_runner(args[0]).configure()

    def cmd_startup(args):
        return my_target.start_network()

    commands = {
        'build':   cmd_build,
        'run':     cmd_run,
        'deploy':  cmd_deploy,
        'exec':    cmd_exec,
        'startup': cmd_startup,
    }

    if len(args) < 2 or args[1] not in commands:
        return errhelp()

    try:
        return commands[args[1]](args[2:])
    except FT_Error as e:
        log.err(str(e))
        return 127

def run_app():
    dir = dirname(dirname(abspath(__file__)))
    chdir(dir)
    my_target = target.get(dir+'/cf/target.yml')
    exit(my_target.get_runner(basename(argv[0])).run(argv[1:]))
