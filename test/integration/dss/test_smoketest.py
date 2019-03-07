import tempfile
import os
import sys
import subprocess
import json

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.util.compat import USING_PYTHON2
if USING_PYTHON2:
    import backports.tempfile
    import unittest2 as unittest
    TemporaryDirectory = backports.tempfile.TemporaryDirectory
else:
    import unittest
    TemporaryDirectory = tempfile.TemporaryDirectory


def GREEN(message=None):
    if message is None:
        return "\033[32m" if sys.stdout.isatty() else ""
    else:
        return GREEN() + str(message) + ENDC()


def RED(message=None):
    if message is None:
        return "\033[31m" if sys.stdout.isatty() else ""
    else:
        return RED() + str(message) + ENDC()


def ENDC():
    return "\033[0m" if sys.stdout.isatty() else ""


def run(command, **kwargs):
    print(GREEN(command))
    try:
        return subprocess.run(command, check=True, shell=isinstance(command, str), **kwargs)
    except subprocess.CalledProcessError as e:
        parser.exit(RED(f'{parser.prog}: Exit status {e.returncode} while running "{command}". Stopping.'))

def run_for_json(command, **kwargs):
    return json.loads(run(command, stdout=subprocess.PIPE, **kwargs).stdout.decode(sys.stdout.encoding))


class Smoketest(unittest.testCase):
    staging_bucket = 'org-humancellatlas-dss-cli-test'

    @classmethod
    def setupclass(cls):
        """ uses smoketesting from the data-store to ensure cli usage is working as expected."""
        os.chdir('..')
        cls.workingDir = os.getcwd()
        if os.path.exists("../data-store"):
            run("git pull --recurse-submodules", cwd=".")
        else:
            run("git clone --depth 1 --recurse-submodules https://github.com/HumanCellAtlas/dcp-cli")

