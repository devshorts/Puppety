#!/usr/bin/env python

import os
import shutil
import subprocess
import re
import time
import socket


class Config:
    def __init__(self,
                 puppet_master_ip,
                 manifests_dir,
                 docker_tag=None,
                 environment="production",
                 docker_host_name="docker_host",
                 master_puppet_conf='master/data/puppet.conf'):
        self.docker_tag = docker_tag
        self.master_puppet_conf = master_puppet_conf
        self.environment = environment
        self.manifests_dir = manifests_dir
        self.docker_host_name = docker_host_name
        self.environment = environment
        self.puppet_master_ip = puppet_master_ip


class Test:
    def __init__(self, test_name, file_location):
        self.test_name = test_name
        self.file_location = file_location

    def template(self, contents, config):
        return contents

    def pre_process(self):
        pass

    def post_process(self):
        pass


class NodeTest(Test):
    def __init__(self, test_name, file_location, node_name):
        Test.__init__(self, test_name, file_location)
        self.node_name = node_name

    def template(self, contents, config):
        return template(search_str="node.*" + self.node_name,
                        replace_str="node /" + config.docker_host_name + "\.*/",
                        contents=contents,
                        flags=TemplateFlags.Regex)


class RoleTest(Test):
    def __init__(self, test_name, file_location, role_name):
        Test.__init__(self, test_name, file_location)
        self.role_name = role_name

    def pre_process(self):
        role_path = "agent/data/etc/.role"

        os.makedirs("agent/data/etc/.role")

        with open(os.path.join(role_path, "role"), 'w+') as buffer:
            buffer.write(self.role_name)


class TemplateFlags:
    Normal, Regex = range(2)


def set_dns_alt(name, file):
    from ConfigParser import SafeConfigParser

    parser = SafeConfigParser()
    parser.read(file)

    parser.set("master", "dns_alt_names", name)

    parser.write(open(file, 'w'))


def get_test_name(line):
    test_match = re.compile(".*#\s+node-test:\s+(?P<test>.*)");

    match = test_match.match(line)

    if match is not None:
        return match.groups('test_match')[0]

    return None


def find_annotated_tests(curr_file):
    with open(curr_file, 'r') as buff:
        node_test_match_regex = re.compile(".*#\s+node-test:\s+(?P<test>.*)")
        node_match_regex = re.compile(".*node\s+(?P<node_name>.*)\{")

        role_test_match_regex = re.compile(".*#\s+role-test:\s+(?P<test>.*)")
        role_match_regex = re.compile(".*'(?P<role_name>.*)':.*\{")

        lines = buff.readlines()
        for i in range(len(lines)):
            current_line = lines[i]

            matched_node_test = node_test_match_regex.match(current_line)

            matched_role_test = role_test_match_regex.match(current_line)

            if matched_node_test is not None:
                test_name = matched_node_test.groups('test')[0]

                matched_node_name = node_match_regex.match(lines[i + 1])

                if matched_node_name is not None:
                    node_name = matched_node_name.groups('node_name')[0]

                    yield NodeTest(test_name=test_name.strip(),
                                   file_location=curr_file,
                                   node_name=node_name)

            if matched_role_test is not None:
                test_name = matched_role_test.groups('test')[0]

                matched_role_name = role_match_regex.match(lines[i + 1])

                if matched_role_name is not None:
                    role_name = matched_role_name.groups('role_name')[0]

                    yield RoleTest(test_name=test_name.strip(),
                                   role_name=role_name,
                                   file_location=curr_file)


def locate_tests(root_folder):
    aggregated_tests = []
    for folder, _, files in os.walk(root_folder):
        files = [f for f in files if ".bak" not in f]
        paths = [os.path.join(folder, filename) for filename in files]

        aggregated_tests.append((list(node) for node in map(find_annotated_tests, paths)))

    return [x for test_list in aggregated_tests
            for test in test_list
            if len(test) > 0
            for x in test]


def template_file(search_str, replace_str, file, flags=TemplateFlags.Normal):
    with open(file, 'r+w') as buffer:
        contents = buffer.read()

        contents = template(search_str, replace_str, contents, flags)

        buffer.seek(0)
        buffer.write(contents)
        buffer.truncate()


def get_puppet_master_ip():
    default = socket.gethostname()

    if subprocess.check_output("uname").strip() == "Darwin":
        return "192.168.59.103"

    return default


def template(search_str, replace_str, contents, flags=TemplateFlags.Normal):
    if flags == TemplateFlags.Normal:
        return contents.replace(search_str, replace_str)
    elif flags == TemplateFlags.Regex:
        return re.sub(search_str, replace_str, contents)

    return contents


def apply_template(test, config):
    template_file("--PUPPET_MASTER_IP--", config.puppet_master_ip, 'agent/puppet.conf.templated')
    template_file("--ENVIRONMENT--", config.environment, 'agent/entrypoint.templated')
    template_file("--RUNNER--", test.test_name, 'agent/entrypoint.templated')
    template_file("--RUNNER--", test.test_name, 'master/entrypoint.templated')

    with open(test.file_location, 'r+w') as buffer:
        contents = buffer.read()

        contents = test.template(contents, config)

        buffer.seek(0)
        buffer.write(contents)
        buffer.truncate()


def create_templates():
    shutil.copy('agent/Dockerfile', 'agent/Dockerfile.templated')
    shutil.copy('agent/entrypoint', 'agent/entrypoint.templated')
    shutil.copy('master/entrypoint', 'master/entrypoint.templated')
    shutil.copy('agent/puppet.conf', 'agent/puppet.conf.templated')


def print_tests(root_folder):
    for test in locate_tests(root_folder):
        print test.test_name


def docker_args(cmd):
    return list(x for x in (["docker"] + cmd.split(' ')) if len(x) > 0)


def build_docker_images():
    master_name = get_image_name(config, "puppet-master")
    agent_name = get_image_name(config, "puppet-agent")

    if 0 != subprocess.call(docker_args("build -t " + agent_name + " -f agent/Dockerfile.templated agent")):
        exit(1)

    if 0 != subprocess.call(docker_args("build -t " + master_name + " master")):
        exit(1)


def get_image_name(config, name):
    base_name = "puppet-tests/" + name

    if config.docker_tag is not None:
        return base_name + ":" + config.docker_tag

    return base_name


def wait_for_master_to_run(config):
    max_time = 20

    while not os.path.isfile("results/" + config.environment + "/sync") and max_time > 0:
        time.sleep(1)
        max_time -= 1

    if max_time == 0:
        print "Max time for master to setup reached, exiting"

        stop_pending_docker_masters()

        exit(1)


def run_docker_images(config):
    master_name = get_image_name(config, "puppet-master")
    agent_name = get_image_name(config, "puppet-agent")

    pwd = os.getcwd()

    print "Executing master"

    master_sha = subprocess.check_output(
        docker_args("run -d -p 8140:8140 -v %(pwd)s/results/%(environment)s:/opt/local --privileged %(master_name)s" % \
                    {'pwd': pwd,
                     'environment': config.environment,
                     'master_name': master_name})).strip()

    wait_for_master_to_run(config)

    time.sleep(2)

    print "Executing agent"

    agent_cmd = "run -v %(pwd)s/results/%(environment)s:/opt/local -h %(docker_host)s --privileged  %(agent_name)s" % \
                {'pwd': pwd,
                 'environment': config.environment,
                 'docker_host': config.docker_host_name,
                 'agent_name': agent_name}

    try:
        print subprocess.check_output(docker_args(agent_cmd))
    except subprocess.CalledProcessError as e:
        print e.output

        exit(1)
    finally:
        if 0 != subprocess.call(docker_args("kill %s" % master_sha)):
            exit(1)


def template_puppet_master(config):
    set_dns_alt(get_puppet_master_ip(), config.master_puppet_conf)


def stop_pending_docker_masters():
    items = subprocess.check_output(docker_args("ps -f 'image=puppet-tests/puppet-master' -q")).splitlines()

    if len(items) > 0:
        print "Closing pending puppet test masters"
        subprocess.call(["docker", "kill"] + items)


def fixture_setup():
    shutil.rmtree('agent/runners', ignore_errors=True)
    shutil.copytree('runners', 'agent/runners')

    shutil.rmtree('master/runners', ignore_errors=True)
    shutil.copytree('runners', 'master/runners')

    shutil.rmtree('results', ignore_errors=True)

    shutil.rmtree('master/data', ignore_errors=True)
    shutil.rmtree('agent/data', ignore_errors=True)

    os.mkdir('agent/data')

    shutil.copytree('../data/', 'master/data/')
    for folder, _, file in os.walk("."):
        files = (f for f in file if f.endswith(".templated") or f.endswith(".pyc"))

        for d in files:
            os.remove(os.path.join(folder, d))


def get_args_parser():
    import argparse

    parser = argparse.ArgumentParser(description='Executes puppet tests in docker containers',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-e', dest='environment',
                        help='Environment',
                        default="production")

    parser.add_argument('--manifests-dir', dest='manifests_dir',
                        help='The manifests directory to scan relative to the /data folder.'
                             ' default: environments/{environment}')

    parser.add_argument('-t', dest='test_name',
                        help='The test to run')

    parser.add_argument('--all', dest="all_tests", action="store_true",
                        help="Run all tests")

    parser.add_argument("--master-conf", dest="master_puppet_conf",
                        default="puppet.conf",
                        help="Master puppet conf relative to the /data folder")

    parser.add_argument("--list", dest="list_only", action="store_true",
                        help="Only list tests that have been detected")

    parser.add_argument("--docker-tag", dest="docker_tag",
                        help="Tag created docker images with specific tag. Useful if you want to run tests in parallel for different "
                             "environments")

    return parser


def run_tests(config, tests):
    stop_pending_docker_masters()

    for test in tests:
        print "Processing test: " + test.test_name

        fixture_setup()

        create_templates()

        test.pre_process()

        apply_template(test, config)

        template_puppet_master(config)

        build_docker_images()

        run_docker_images(config)

        test.post_process()


if __name__ == '__main__':
    args = get_args_parser().parse_args()

    manifests_dir = "master/data/" + args.manifests_dir \
        if args.manifests_dir is not None \
        else "master/data/environments/" + args.environment + "/manifests"

    config = Config(
        puppet_master_ip=get_puppet_master_ip(),
        manifests_dir=manifests_dir,
        environment=args.environment,
        docker_tag=args.docker_tag,
        master_puppet_conf="master/data/" + args.master_puppet_conf
    )

    fixture_setup()

    if args.list_only:
        for test in locate_tests(config.manifests_dir):
            print test.test_name

        exit(0)

    tests = list((test for test in locate_tests(config.manifests_dir)
                  if args.test_name is not None and args.test_name == test.test_name
                  or args.all_tests))

    if len(tests) > 0:
        run_tests(config, tests)
    else:
        print "No tests found"
