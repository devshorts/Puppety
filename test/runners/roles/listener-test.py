from util.puppet_utils import *

@agent
def test_file_exists():
    assert file_exists("/tmp/listener")
