Puppet-scripts
=====

This is a way to test puppet scripts. Currently supported is both role based testing and node based testing.

Roles are assigned to remote machines by setting a file in `/etc/.role/role` whose contents contains the role name.

# Requirements

- Docker v1.6+
- python
- pip

# Testing your puppet scripts

```
$ python test-runner.py  -h
usage: test-runner.py [-h] [-e ENVIRONMENT] [--manifests-dir MANIFESTS_DIR]
                      [-t TEST_NAME] [--all]
                      [--master-conf MASTER_PUPPET_CONF] [--list]

Executes puppet tests in docker containers

optional arguments:
  -h, --help            show this help message and exit
  -e ENVIRONMENT        Environment (default: production)
  --manifests-dir MANIFESTS_DIR
                        The manifests directory to scan relative to the /data
                        folder. default: environments/{environment} (default:
                        None)
  -t TEST_NAME          The test to run (default: None)
  --all                 Run all tests (default: False)
  --master-conf MASTER_PUPPET_CONF
                        Master puppet conf relative to the /data folder
                        (default: puppet.conf)
  --list                Only list tests that have been detected (default:
                        False)
```

Scripts can be tested in jenkins via paired docker images.  Annotate a
puppet node with either `# node-test: <test-name>` or `# role-test: <test-name>` depending on the type of test

The `<test name>` should correlate to a path in `test/runners` which uses `pytest`
as the test framework.  

The runner will execute your test as if it was the target node in the docker image
and output a junit style xml for jenkins consumption

## Node tests

To test a node, annotate a node with 
```
# node-test: <testname
```

For example, if there is a test in

```
test/runners/jenkins/test-jenkins.py
```

And we have a node in

```
data/environments/develop/manifests/jenkins.pp
```

With the content of

```
# node-test: jenkins/test-server
node "test.foo.com" {
  file {'/tmp/example-ip':                                            # resource type file and filename
    ensure  => present,                                               # make sure it exists
    mode    => 0644,                                                  # file permissions
    content =>  "Here is my Public IP Address: ${ipaddress_eth0}.\n",  # note the ipaddress_eth0 fact
  }
}
```

When you do `./run.sh -r jenkins/test-server -e develop` your node definition will get assigned to the docker image
and then your test can run against the node and validate any assertions you want

## Role tests

We also support role based testing.  For our system, we include a custom facter that gathers the role from the agent.

This factor looks in the agents `/etc/.role/role` file to determine its role.  You can now create a puppet file like this:

```
node default {
  case $node_role{
    # role-test: roles/slave-test
    'slave': {
      file {'/tmp/node-role': # resource type file and file
        ensure  => present,   # make sure it exists
        mode    => 0644,      # file permissions
        content =>    "Here is my Role ${$node_Role}.\n",  # note the node role
       }
    }
    # role-test: roles/listener-test
    'listener': {
      file { '/tmp/listener': # resource type file and file
        ensure  => present,   # make sure it exists
        mode    => 0644,      # file permissions
        content =>    "I am a listener",  # note the node role
      }
    }
   }
}
```

Tests annotated with 
```
# role-test: <test name>
```

Will generate the appropriate file in the agent corresponding to the annotated role.

# Environments

You can also run your test against multiple environments

```
$ python test-runner.py  --list -e develop
random-test
jenkins/test-server

python test-runner.py -e develop -t jenkins/test-server
```

The default environment is "production"

Run all the tests in an environment

```
python test-runner.py -e develop --all
```

# Test on master and test on agent

To write a test on the agent, annotate your test with `@agent`. To support a master test (which is used for master setup before running puppet) create a test with `@master`.

For example:

```
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
```
