from util.puppet_utils import *

@agent
def test_file_exists():
    assert file_exists("/tmp/example-ip")

@agent
def test_ip_contents_set():
    assert contents_contains('/tmp/example-ip', 'Here is my Public IP Address')

@master
def test_setup():
    print "foo"
