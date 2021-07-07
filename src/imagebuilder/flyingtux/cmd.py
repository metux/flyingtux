from sys import argv, exit
from flyingtux import target
from flyingtux.app import builder
from flyingtux.util import FT_Error
from metux.util import log

def run_cmd(conf, argv):
    my_target = target.get('cf/target.yml')

    def errhelp():
        print("%s [build|deploy|run]" % argv[0])
        exit(1)

    def cmd_run(args):
        if len(args) < 1:
            print("%s <run> <package>" % argv[0])
            return 1

        return my_target.get_runner(args[0]).run()

    def cmd_build(args):
        if len(args) < 1:
            print("%s <build> <package>" % argv[0])
            return 1

        return my_target.get_builder(args[0]).run()

    def cmd_deploy(args):
        if len(args) < 1:
            print("%s <deploy> <package>" % argv[0])
            return 1

        return my_target.get_deploy(args[0]).run()

    commands = {
        'build':  cmd_build,
        'run':    cmd_run,
        'deploy': cmd_deploy,
    }

    if len(argv) < 2 or argv[1] not in commands:
        return errhelp()

    try:
        return commands[argv[1]](argv[2:])
    except FT_Error as e:
        log.err(str(e))
        return 127
