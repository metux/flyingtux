from subprocess import call
from os import makedirs
from os.path import abspath
import errno

def mkdir(dirname):
    try:
        makedirs(dirname)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise
        # time.sleep might help here
        pass

def rmtree(dirname):
    call(['rm', '-Rf', abspath(dirname)])
