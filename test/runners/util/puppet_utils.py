import os
import subprocess
import pytest

agent = pytest.mark.agent
master = pytest.mark.master

def file_exists(file):
    return os.path.isfile(file) == True

def list_proc():
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)

    out, err = p.communicate()

    return map(lambda x: x.split(None, 3)[3], out.splitlines()[1:])

def proc_started(name):
    return len([x for x in list_proc() if name == x]) > 0


def contents_equals(input_file, contents):
    with open(input_file, 'r') as f:
        return f.read().strip() == contents.strip()

def contents_contains(input_file, contents):
    with open(input_file, 'r') as f:
        return contents in f.read()
